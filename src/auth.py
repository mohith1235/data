import json
import re
import socket
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen


class SupabaseAuthError(Exception):
    """Raised when Supabase authentication cannot complete."""


class SupabaseConfigurationError(Exception):
    """Raised when the Supabase project configuration is invalid."""


USERNAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{2,31}$")
INTERNAL_AUTH_DOMAIN = "users.dataintelligence.invalid"


def normalize_username(username):
    normalized = username.strip().lower()
    if not USERNAME_PATTERN.fullmatch(normalized):
        raise SupabaseAuthError(
            "User ID must be 3 to 32 characters, start with a letter or number, "
            "and contain only letters, numbers, underscores, or hyphens."
        )
    return normalized


def _username_auth_email(username):
    return f"{normalize_username(username)}@{INTERNAL_AUTH_DOMAIN}"


def validate_supabase_config(config):
    if not config:
        return None

    project_url = str(config.get("url", "")).strip().rstrip("/")
    anon_key = str(config.get("anon_key", "")).strip()

    if not project_url or not anon_key:
        raise SupabaseConfigurationError(
            "Set both `url` and `anon_key` in the Supabase secrets section."
        )

    parsed_url = urlsplit(project_url)
    if (
        parsed_url.scheme != "https"
        or not parsed_url.hostname
        or parsed_url.username
        or parsed_url.password
        or parsed_url.query
        or parsed_url.fragment
    ):
        raise SupabaseConfigurationError(
            "The Supabase project URL must be a valid HTTPS URL."
        )

    return {"url": project_url, "anon_key": anon_key}


def _request(config, endpoint, payload, access_token=None, method="POST"):
    headers = {
        "apikey": config["anon_key"],
        "Content-Type": "application/json",
    }
    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    request = Request(
        f"{config['url'].rstrip('/')}/auth/v1/{endpoint}",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method=method,
    )

    try:
        with urlopen(request, timeout=15) as response:
            body = response.read()
    except HTTPError as exc:
        response_body = exc.read()
        try:
            error_data = json.loads(response_body) if response_body else {}
        except json.JSONDecodeError:
            error_data = {}
        message = (
            error_data.get("msg")
            or error_data.get("message")
            or error_data.get("error_description")
            or error_data.get("error")
            or f"Supabase returned HTTP {exc.code}."
        )
        raise SupabaseAuthError(str(message)) from exc
    except URLError as exc:
        if isinstance(exc.reason, socket.gaierror):
            hostname = urlsplit(config["url"]).hostname
            raise SupabaseAuthError(
                f"Could not resolve Supabase host `{hostname}`. Verify that "
                "Streamlit Cloud's `[supabase].url` exactly matches your "
                "Supabase Project URL, then save the secrets and reboot the app."
            ) from exc
        raise SupabaseAuthError(
            f"Could not reach Supabase: {exc.reason}"
        ) from exc
    except TimeoutError as exc:
        raise SupabaseAuthError("The Supabase request timed out.") from exc

    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise SupabaseAuthError(
            "Supabase returned an invalid response."
        ) from exc


def sign_up(config, username, password):
    normalized_username = normalize_username(username)
    return _request(
        config,
        "signup",
        {
            "email": _username_auth_email(normalized_username),
            "password": password,
            "data": {"username": normalized_username},
        },
    )


def sign_in(config, username, password):
    return _request(
        config,
        "token?grant_type=password",
        {
            "email": _username_auth_email(username),
            "password": password,
        },
    )


def sign_out(config, access_token):
    return _request(config, "logout", {}, access_token=access_token)
