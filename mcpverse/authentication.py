import os
import json
import click
import webbrowser
import http.server
import socketserver
import threading
import random
import string
import urllib.parse
import requests
from datetime import datetime, timezone
from typing import Callable

AUTH_FILE = os.path.expanduser("~/.mcpverse/auth.json")

MCPVERSE_API_URL = "https://api.mcpverse.dev"
MCPVERSE_APP_URL = "https://mcpverse.dev"

class AuthData:
    def __init__(self, access_token: str, expires_at: datetime, refresh_token: str, id: str, email: str, first_name: str, last_name: str, display_name: str, locale: str):
        self.access_token = access_token
        self.expires_at = expires_at
        self.refresh_token = refresh_token
        self.id = id
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.display_name = display_name
        self.locale = locale
    
    def to_dict(self) -> dict:
        return {
            "access_token": self.access_token,
            "expires_at": self.expires_at.isoformat(),
            "refresh_token": self.refresh_token,
            "id": self.id,
            "email": self.email,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "display_name": self.display_name,
            "locale": self.locale
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'AuthData':
        return AuthData(
            data['access_token'],
            datetime.fromisoformat(data['expires_at']),
            data['refresh_token'],
            data['id'],
            data['email'],
            data['first_name'],
            data['last_name'],
            data['display_name'],
            data['locale']
        )
    
    @staticmethod
    def from_token_data(token_data: dict) -> 'AuthData':
        return AuthData(
            token_data['access_token'],
            datetime.fromisoformat(token_data['expires_at']),
            token_data['refresh_token'],
            token_data['user']['id'],
            token_data['user']['email'],
            token_data['user']['firstName'],
            token_data['user']['lastName'],
            token_data['user']['displayName'],
            token_data['user']['locale']
        )

def get_auth_file_path() -> str:
    """Return the path to the auth file, ensuring directory exists."""
    auth_dir = os.path.dirname(AUTH_FILE)
    os.makedirs(auth_dir, exist_ok=True)
    return AUTH_FILE


def save_auth_info(auth_data: AuthData):
    """Save authentication token and email to the auth file."""
    with open(get_auth_file_path(), "w") as f:
        json.dump(auth_data.to_dict(), f)


def get_auth_info() -> AuthData | None:
    """Get the authentication information from the auth file."""
    try:
        with open(get_auth_file_path(), "r") as f:
            data = json.load(f)
            return AuthData.from_dict(data)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


def refresh_tokens(refresh_token: str) -> AuthData | None:
    """Refresh the access token using the refresh token."""
    try:
        response = requests.post(
            f"{MCPVERSE_API_URL}/api/oauth/token",
            json={
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
        )
        response.raise_for_status()
        token_data = response.json()
        auth_data = AuthData.from_token_data(token_data)
        save_auth_info(auth_data)
        return auth_data
    except Exception:
        return None


def get_valid_auth_info() -> AuthData | None:
    """Get valid authentication info, refreshing if expired."""
    auth_data = get_auth_info()
    if not auth_data:
        return None
    
    # Check if token is expired
    now = datetime.now(tz=timezone.utc)
    if now >= auth_data.expires_at:
        # Token is expired, try to refresh
        refreshed_auth = refresh_tokens(auth_data.refresh_token)
        if not refreshed_auth:
            remove_auth_info()  # Clear invalid auth data
            return None
        return refreshed_auth
    
    return auth_data


def is_authenticated() -> bool:
    """Check if user is authenticated with a valid token."""
    return get_valid_auth_info() is not None


def get_current_user_email() -> str:
    """Get the email of the currently authenticated user."""
    auth_data = get_valid_auth_info()
    if not auth_data:
        raise Exception("Not authenticated")
    return auth_data.email


def get_access_token() -> str:
    """Get a valid access token of the currently authenticated user."""
    auth_data = get_valid_auth_info()
    if not auth_data:
        raise Exception("Not authenticated")
    return auth_data.access_token


def remove_auth_info() -> bool:
    """Remove the authentication information."""
    try:
        os.remove(get_auth_file_path())
        return True
    except FileNotFoundError:
        return False


def browser_login() -> tuple[bool, str]:
    """Launch a browser-based authentication flow.
    
    Returns:
        tuple: (success, message) where success is a boolean indicating if login was successful
               and message is either the email on success or error message on failure
    """
    # Generate a random state value to verify callback
    state = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    
    # Set up a local server to receive the callback
    callback_received = threading.Event()
    auth_data: AuthData | None = None
    
    class OAuthCallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            nonlocal auth_data
            query = urllib.parse.urlparse(self.path).query
            params = urllib.parse.parse_qs(query)
            
            # Check state to prevent CSRF
            if 'state' not in params or params['state'][0] != state:
                self.send_response(302)
                self.send_header('Location', f"{MCPVERSE_APP_URL}/auth/cli?error=true")
                self.end_headers()
                return False, "Invalid state parameter."
            
            # Exchange the code for tokens
            if 'code' in params:
                code = params['code'][0]
                redirect_uri = f"http://localhost:{port}"
                
                try:
                    # Exchange the code for tokens
                    response = requests.post(
                        f"{MCPVERSE_API_URL}/api/oauth/token",
                        json={
                            'code': code,
                            'redirect_uri': redirect_uri,
                            'grant_type': 'authorization_code'
                        }
                    )
                    response.raise_for_status()
                    token_data = response.json()

                    # Assuming the response includes tokens and user info
                    auth_data = AuthData.from_token_data(token_data)
                    
                    self.send_response(302)
                    self.send_header('Location', f"{MCPVERSE_APP_URL}/auth/cli?success=true")
                    self.end_headers()
                    callback_received.set()
                except Exception as e:
                    self.send_response(302)
                    self.send_header('Location', f"{MCPVERSE_APP_URL}/auth/cli?error=true")
                    self.end_headers()
            else:
                self.send_response(302)
                self.send_header('Location', f"{MCPVERSE_APP_URL}/auth/cli?error=true")
                self.end_headers()
        
        def log_message(self, format, *args):
            # Suppress logs
            return
    
    # Start server on a random available port
    with socketserver.TCPServer(("localhost", 0), OAuthCallbackHandler) as httpd:
        port = httpd.server_address[1]
        
        # Start the server in a new thread
        server_thread = threading.Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        
        try:
            # Construct the auth URL with the state parameter and redirect URL
            redirect_uri = f"http://localhost:{port}"
            auth_url = f"{MCPVERSE_APP_URL}/auth/cli?state={state}&redirect_uri={urllib.parse.quote(redirect_uri)}"
            
            # Open the browser to the auth URL
            webbrowser.open(auth_url)
            click.echo(f"Opened browser for authentication. Waiting for login...")
            
            # Wait for the callback (with timeout)
            callback_received.wait(timeout=300)  # 5 minutes timeout
            
            if callback_received.is_set():
                # Save the token data
                save_auth_info(auth_data)
                return True, auth_data.email
            else:
                return False, "Authentication timed out"
                
        finally:
            # Shutdown the server
            httpd.shutdown()
            server_thread.join()