import io
import json
import socket
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from src.auth import (
    SupabaseAuthError,
    SupabaseConfigurationError,
    request_password_reset,
    sign_in,
    sign_out,
    sign_up,
    update_password,
    validate_supabase_config,
    verify_recovery_code,
)


class SupabaseAuthTests(unittest.TestCase):
    def setUp(self):
        self.config = {
            "url": "https://example.supabase.co/",
            "anon_key": "test-anon-key",
        }

    def test_missing_config_is_not_configured(self):
        self.assertIsNone(validate_supabase_config(None))

    def test_config_requires_https_url(self):
        with self.assertRaises(SupabaseConfigurationError):
            validate_supabase_config(
                {"url": "http://example.supabase.co", "anon_key": "test"}
            )

    def test_config_requires_both_values(self):
        with self.assertRaises(SupabaseConfigurationError):
            validate_supabase_config({"url": "https://example.supabase.co"})

    @patch("src.auth.urlopen", return_value=io.BytesIO(b'{"access_token":"token"}'))
    def test_sign_in_sends_password_grant_request(self, urlopen_mock):
        response = sign_in(self.config, "user@example.com", "password")

        self.assertEqual(response, {"access_token": "token"})
        request = urlopen_mock.call_args.args[0]
        self.assertEqual(
            request.full_url,
            "https://example.supabase.co/auth/v1/token?grant_type=password",
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Apikey"), "test-anon-key")
        self.assertEqual(
            json.loads(request.data),
            {"email": "user@example.com", "password": "password"},
        )

    @patch("src.auth.urlopen", return_value=io.BytesIO(b"{}"))
    def test_sign_up_uses_email_and_password(self, urlopen_mock):
        sign_up(self.config, "user@example.com", "password")

        request = urlopen_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/auth/v1/signup"))

    @patch("src.auth.urlopen", return_value=io.BytesIO(b"{}"))
    def test_password_recovery_requests_email_code(self, urlopen_mock):
        request_password_reset(self.config, "user@example.com")

        request = urlopen_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/auth/v1/recover"))

    @patch("src.auth.urlopen", return_value=io.BytesIO(b'{"access_token":"recovery"}'))
    def test_recovery_code_is_verified(self, urlopen_mock):
        verify_recovery_code(self.config, "user@example.com", "123456")

        request = urlopen_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/auth/v1/verify"))
        self.assertEqual(
            json.loads(request.data),
            {
                "type": "recovery",
                "email": "user@example.com",
                "token": "123456",
            },
        )

    @patch("src.auth.urlopen", return_value=io.BytesIO(b"{}"))
    def test_password_update_uses_authenticated_put(self, urlopen_mock):
        update_password(self.config, "recovery-token", "new-password")

        request = urlopen_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/auth/v1/user"))
        self.assertEqual(request.get_method(), "PUT")
        self.assertEqual(request.get_header("Authorization"), "Bearer recovery-token")

    @patch("src.auth.urlopen", return_value=io.BytesIO(b""))
    def test_sign_out_uses_authenticated_session(self, urlopen_mock):
        sign_out(self.config, "access-token")

        request = urlopen_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/auth/v1/logout"))
        self.assertEqual(request.get_header("Authorization"), "Bearer access-token")

    @patch(
        "src.auth.urlopen",
        side_effect=HTTPError(
            "https://example.supabase.co/auth/v1/token",
            400,
            "Bad Request",
            {},
            io.BytesIO(b'{"msg":"Invalid login credentials"}'),
        ),
    )
    def test_auth_api_errors_are_reported(self, _urlopen_mock):
        with self.assertRaisesRegex(
            SupabaseAuthError,
            "Invalid login credentials",
        ):
            sign_in(self.config, "user@example.com", "wrong-password")

    @patch(
        "src.auth.urlopen",
        side_effect=URLError(socket.gaierror(-2, "Name or service not known")),
    )
    def test_dns_errors_show_the_supabase_host_to_verify(self, _urlopen_mock):
        with self.assertRaisesRegex(
            SupabaseAuthError,
            r"Could not resolve Supabase host `example\.supabase\.co`",
        ):
            sign_in(self.config, "user@example.com", "password")


class AuthenticationScreenTests(unittest.TestCase):
    app_path = str(Path(__file__).resolve().parents[1] / "app.py")

    def test_auth_screen_renders_when_supabase_is_configured(self):
        app = AppTest.from_file(self.app_path)
        app.secrets = {
            "supabase": {
                "url": "https://example.supabase.co",
                "anon_key": "test-anon-key",
            }
        }

        app.run(timeout=60)

        self.assertFalse(app.exception)
        self.assertEqual(
            [tab.label for tab in app.tabs],
            ["Sign in", "Create account", "Reset password"],
        )

    def test_missing_credentials_shows_setup_instructions(self):
        app = AppTest.from_file(self.app_path).run(timeout=60)

        self.assertFalse(app.exception)
        self.assertTrue(
            any("Secure your workspace" in str(title.value) for title in app.title)
        )


if __name__ == "__main__":
    unittest.main()
