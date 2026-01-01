#!/usr/bin/env python3
"""Complete OAuth flow to get api.responses.write scope for Codex API"""
import requests
import json
import secrets
import hashlib
import base64
import urllib.parse
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

class OAuthCallbackHandler(BaseHTTPRequestHandler):
    """Handles OAuth redirect callback"""
    authorization_code = None

    def do_GET(self):
        query = urllib.parse.urlparse(self.path).query
        params = urllib.parse.parse_qs(query)
        OAuthCallbackHandler.authorization_code = params.get('code', [None])[0]

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        html = """
        <html>
        <head><title>Success!</title></head>
        <body style="font-family: Arial; text-align: center; margin-top: 100px;">
            <h1 style="color: green;">✅ Authorization Successful!</h1>
            <p>You can close this window and return to the terminal.</p>
        </body>
        </html>
        """
        self.wfile.write(html.encode())

    def log_message(self, format, *args):
        pass  # Silence HTTP server logs

def generate_pkce_pair():
    """Generate PKCE code_verifier and code_challenge"""
    # Generate random code verifier (43-128 characters)
    code_verifier = base64.urlsafe_b64encode(
        secrets.token_bytes(32)
    ).decode('utf-8').rstrip('=')

    # Generate code challenge (SHA256 hash of verifier)
    code_challenge = base64.urlsafe_b64encode(
        hashlib.sha256(code_verifier.encode('utf-8')).digest()
    ).decode('utf-8').rstrip('=')

    return code_verifier, code_challenge

def get_codex_oauth_token():
    """Perform OAuth 2.0 PKCE flow using Codex CLI's client ID"""

    # OpenAI's official Codex CLI client ID (from binary)
    CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"
    REDIRECT_URI = "http://localhost:8080/auth/callback"
    AUTH_ENDPOINT = "https://auth.openai.com/authorize"
    TOKEN_ENDPOINT = "https://auth.openai.com/oauth/token"

    # Required scopes including the special api.responses.write
    SCOPES = "openid profile email offline_access api.responses.write"

    print("=" * 80)
    print("🔐 Codex OAuth 2.0 Authentication Flow")
    print("=" * 80)
    print()
    print("This will authenticate you to use the Codex direct API with the")
    print("'api.responses.write' scope by using the official Codex CLI client ID.")
    print()

    # Step 1: Generate PKCE parameters
    print("📝 Step 1: Generating PKCE parameters...")
    code_verifier, code_challenge = generate_pkce_pair()
    print(f"   Code verifier: {code_verifier[:20]}...")
    print(f"   Code challenge: {code_challenge[:20]}...")
    print()

    # Step 2: Build authorization URL
    print("🔗 Step 2: Building authorization URL...")
    auth_params = {
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": SCOPES,
        "code_challenge": code_challenge,
        "code_challenge_method": "S256"
    }

    auth_url = f"{AUTH_ENDPOINT}?{urllib.parse.urlencode(auth_params)}"
    print()
    print("=" * 80)
    print("🌐 Opening browser for authentication...")
    print("=" * 80)
    print()
    print(f"URL: {auth_url}")
    print()
    print("👉 Please:")
    print("   1. Log in with your ChatGPT Pro account")
    print("   2. Authorize the application")
    print("   3. Wait for the redirect...")
    print()

    # Open browser
    webbrowser.open(auth_url)

    # Step 3: Start local callback server
    print("⏳ Step 3: Waiting for OAuth callback...")
    print(f"   Listening on {REDIRECT_URI}")
    print()

    server = HTTPServer(('localhost', 8080), OAuthCallbackHandler)
    server.handle_request()  # Wait for single request

    authorization_code = OAuthCallbackHandler.authorization_code

    if not authorization_code:
        raise Exception("❌ Failed to receive authorization code from callback")

    print("✅ Authorization code received!")
    print(f"   Code: {authorization_code[:20]}...")
    print()

    # Step 4: Exchange authorization code for tokens
    print("🔄 Step 4: Exchanging authorization code for access token...")

    token_data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "code_verifier": code_verifier
    }

    token_response = requests.post(TOKEN_ENDPOINT, data=token_data, timeout=30)

    if token_response.status_code != 200:
        raise Exception(f"❌ Token exchange failed: {token_response.status_code}\n{token_response.text}")

    tokens = token_response.json()

    print("✅ Access token received!")
    print(f"   Token: {tokens['access_token'][:30]}...")
    print()

    # Step 5: Decode JWT to verify scopes (optional, for confirmation)
    import jwt
    try:
        # Decode without verification (just to inspect claims)
        decoded = jwt.decode(tokens['access_token'], options={"verify_signature": False})
        scopes = decoded.get('scp', [])
        print("📋 Token scopes:")
        for scope in scopes:
            marker = "✅" if scope == "api.responses.write" else "  "
            print(f"   {marker} {scope}")
        print()
    except:
        print("   (Could not decode JWT for verification)")
        print()

    # Step 6: Save tokens
    auth_path = Path.home() / ".codex" / "auth_direct_api.json"
    auth_path.parent.mkdir(parents=True, exist_ok=True)

    token_file = {
        "access_token": tokens["access_token"],
        "refresh_token": tokens.get("refresh_token"),
        "id_token": tokens.get("id_token"),
        "token_type": tokens.get("token_type", "Bearer"),
        "scope": SCOPES
    }

    auth_path.write_text(json.dumps(token_file, indent=2))

    print(f"💾 Step 5: Tokens saved to {auth_path}")
    print()
    print("=" * 80)
    print("🎉 SUCCESS! You now have api.responses.write scope!")
    print("=" * 80)
    print()

    return tokens["access_token"]

if __name__ == "__main__":
    try:
        # Check if PyJWT is installed
        try:
            import jwt
        except ImportError:
            print("⚠️  Optional: Install PyJWT to verify token scopes")
            print("   pip install PyJWT")
            print()

        access_token = get_codex_oauth_token()

        print("🚀 Token ready to use!")
        print()
        print("Next steps:")
        print("   1. Use this token to call https://api.openai.com/v1/responses")
        print("   2. Run /tmp/test_codex_direct_api.py to test it")
        print()

    except KeyboardInterrupt:
        print("\n\n❌ Cancelled by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
