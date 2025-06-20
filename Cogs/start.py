import os
import ssl
import socket
import requests
from twitch_oauth_flow import get_valid_token, get_user_id
from dotenv import load_dotenv

load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
HOST = 'irc.chat.twitch.tv'
PORT = 6697
NICK = 'rpg_chaos'
CHANNELS = ['#starry0wolf']

def connect():
    """Connect to Twitch IRC with SSL and auto-refreshed token."""
    token = get_valid_token()
    
    # Create plain socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    
    # Wrap with SSL
    context = ssl.create_default_context()
    ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
    
    # Connect and authenticate
    ssl_sock.connect((HOST, PORT))
    ssl_sock.send(f"PASS oauth:{token}\r\n".encode())
    ssl_sock.send(f"NICK {NICK}\r\n".encode())
    
    # Join channels
    for channel in CHANNELS:
        ssl_sock.send(f"JOIN {channel}\r\n".encode())
    
    return ssl_sock

def who_am_i(token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    url = 'https://id.twitch.tv/oauth2/validate'
    resp = requests.get(url, headers=headers)
    return resp.json()

def get_user_id(username):
    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    url = f"https://api.twitch.tv/helix/users?login={username}"
    resp = requests.get(url, headers=headers)
    data = resp.json()
    if data.get('data'):
        return data['data'][0]['id']
    return None

def get_channel_id(username):
    return get_user_id(username)
