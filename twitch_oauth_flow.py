import json
import time
import webbrowser
from flask import Flask, request
import requests
from dotenv import load_dotenv
import os


# ── Twitch OAuth Flow for Chat Bot ─────────────────────────────────────────────
# Ensure in your Twitch Developer Console, under your app's "OAuth Redirect URLs",
# you have registered exactly:
#   http://localhost:3000
#   http://127.0.0.1:3000
# This must match REDIRECT_URI below exactly, including the port.

# Configuration
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI  = "http://localhost:3000"
SCOPES        = "chat:read chat:edit moderator:read:chatters"  # Only chat scopes for IRC
TOKEN_FILE    = "tokens.json"
#  moderator:manage:shoutouts moderator:manage:announcements channel:manage:raids
app = Flask(__name__)

@app.route('/')
def receive_code():
    """
    Twitch redirects here after the user authorizes your app.
    Extract the 'code' parameter and exchange it for tokens.
    """
    code = request.args.get('code')
    if not code:
        return "No code provided", 400

    # Exchange authorization code for access and refresh tokens
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            'client_id':     CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'code':          code,
            'grant_type':    'authorization_code',
            'redirect_uri':  REDIRECT_URI
        }
    )
    data = resp.json()
    if 'access_token' not in data:
        return f"Error fetching token: {data}", 400

    # Save tokens and metadata for refreshing
    token_data = {
        'access_token':  data['access_token'],
        'refresh_token': data['refresh_token'],
        'expires_in':    data['expires_in'],
        'obtained_at':   time.time()
    }
    with open(TOKEN_FILE, 'w') as f:
        json.dump(token_data, f, indent=2)

    return "Authorization successful! You can close this tab."


def start_auth():
    """
    Open the user's browser to start the OAuth flow.
    """
    auth_url = (
        f"https://id.twitch.tv/oauth2/authorize"
        f"?client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&response_type=code"
        f"&scope={SCOPES.replace(' ', '+')}"
    )
    webbrowser.open(auth_url)
    print(auth_url)


def load_tokens():
    """
    Read token data from TOKEN_FILE.
    """
    return json.load(open(TOKEN_FILE, 'r'))


def save_tokens(tokens):
    """
    Write token data to TOKEN_FILE.
    """
    with open(TOKEN_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)


def is_expired(tokens):
    """
    Determine if the access token is expired (with 60s buffer).
    """
    return time.time() > tokens['obtained_at'] + tokens['expires_in'] - 60


def refresh_token():
    """
    Use the saved refresh_token to obtain a new access_token.
    """
    tokens = load_tokens()
    resp = requests.post(
        "https://id.twitch.tv/oauth2/token",
        data={
            'grant_type':    'refresh_token',
            'refresh_token': tokens['refresh_token'],
            'client_id':     CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
    )
    data = resp.json()
    if 'access_token' not in data:
        raise Exception(f"Failed to refresh token: {data}")

    new_tokens = {
        'access_token':  data['access_token'],
        'refresh_token': data['refresh_token'],
        'expires_in':    data['expires_in'],
        'obtained_at':   time.time()
    }
    save_tokens(new_tokens)
    return new_tokens


def get_valid_token():
    """
    Ensure a valid access_token: refresh if needed.
    Returns the current valid access_token.
    """
    tokens = load_tokens()
    if is_expired(tokens):
        print("Access token expired. Refreshing...")
        tokens = refresh_token()
    return tokens['access_token']


if __name__ == '__main__':
    # Step 1: Run this script to perform OAuth and get initial tokens
    print("Starting OAuth flow. A browser window will open for authorization...")
    start_auth()
    app.run(host="127.0.0.1", port=3000)

def get_user_id(username: str, token: str, client_id: str) -> str:
    headers = {
        'Authorization': f'Bearer {token}',
        'Client-Id': client_id
    }
    resp = requests.get(f'https://api.twitch.tv/helix/users?login={username}', headers=headers)
    data = resp.json()
    if 'data' in data and data['data']:
        return data['data'][0]['id']
    return None