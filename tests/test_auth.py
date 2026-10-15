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
    INTERNAL_AUTH_DOMAIN,
    normalize_username,
    sign_in,
    sign_out,
    sign_up,
    validate_supabase_config,
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
        response = sign_in(self.config, "Test_User", "password")

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
            {
                "email": f"test_user@{INTERNAL_AUTH_DOMAIN}",
                "password": "password",
            },
        )

    @patch("src.auth.urlopen", return_value=io.BytesIO(b"{}"))
    def test_sign_up_maps_username_to_internal_email(self, urlopen_mock):
        sign_up(self.config, "Test_User", "password")

        request = urlopen_mock.call_args.args[0]
        self.assertTrue(request.full_url.endswith("/auth/v1/signup"))
        self.assertEqual(
            json.loads(request.data),
            {
                "email": f"test_user@{INTERNAL_AUTH_DOMAIN}",
                "password": "password",
                "data": {"username": "test_user"},
            },
        )

    def test_username_is_case_insensitive(self):
        self.assertEqual(normalize_username("  Test_User "), "test_user")

    def test_username_rejects_invalid_characters_and_lengths(self):
        for username in ("ab", "starts with space", "has.dot", "x" * 33):
            with self.subTest(username=username):
                with self.assertRaises(SupabaseAuthError):
                    normalize_username(username)

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
            sign_in(self.config, "test_user", "wrong-password")

    @patch(
        "src.auth.urlopen",
        side_effect=URLError(socket.gaierror(-2, "Name or service not known")),
    )
    def test_dns_errors_show_the_supabase_host_to_verify(self, _urlopen_mock):
        with self.assertRaisesRegex(
            SupabaseAuthError,
            r"Could not resolve Supabase host `example\.supabase\.co`",
        ):
            sign_in(self.config, "test_user", "password")


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
            ["Sign in", "Create account"],
        )
        self.assertEqual(
            [field.label for field in app.text_input],
            [
                "User ID",
                "Password",
                "Choose a user ID",
                "Create a password",
                "Confirm password",
            ],
        )
        self.assertFalse(
            any("email" in field.label.lower() for field in app.text_input)
        )

    def test_missing_credentials_shows_setup_instructions(self):
        app = AppTest.from_file(self.app_path).run(timeout=60)

        self.assertFalse(app.exception)
        self.assertTrue(
            any("Secure your workspace" in str(title.value) for title in app.title)
        )


if __name__ == "__main__":
    unittest.main()
