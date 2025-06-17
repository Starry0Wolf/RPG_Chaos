import time
import threading
import requests
from twitch_oauth_flow import get_valid_token
from .start import CLIENT_ID, CHANNELS, NICK, get_user_id, get_channel_id

def shoutout(target_user):
    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    from_broadcaster_id = get_channel_id('starry0wolf')
    to_broadcaster_id = get_user_id(target_user)
    moderator_id = get_user_id(NICK)

    if not from_broadcaster_id or not to_broadcaster_id:
        return {"status": 404}

    url = "https://api.twitch.tv/helix/shoutouts"
    payload = {
        "from_broadcaster_id": from_broadcaster_id,
        "to_broadcaster_id": to_broadcaster_id,
        "moderator_id": moderator_id
    }

    resp = requests.post(url, headers=headers, json=payload)
    return resp

def get_follower_count(channel_name):
    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    user_id = get_user_id(channel_name.lstrip('#'))
    if not user_id:
        return None
        
    url = f"https://api.twitch.tv/helix/users/follows?to_id={user_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        return data.get('total', 0)
    return None

def is_affiliate(channel_name):
    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    user_id = get_user_id(channel_name.lstrip('#'))
    if not user_id:
        return False
        
    url = f"https://api.twitch.tv/helix/users?id={user_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        if data.get('data'):
            broadcaster_type = data['data'][0].get('broadcaster_type')
            return broadcaster_type in ['affiliate', 'partner']
    return False

def send_reminder(user, channel, sock, time_str, reminder_msg=None):
    multiplier = None
    amount = None
    
    if time_str.endswith('m'):
        multiplier = 60
        try:
            amount = int(time_str[:-1])
        except ValueError:
            amount = None
    elif time_str.endswith('h'):
        multiplier = 3600
        try:
            amount = int(time_str[:-1])
        except ValueError:
            amount = None

    if multiplier and amount:
        total_seconds = amount * multiplier
        
        def threaded_reminder():
            time.sleep(total_seconds)
            if reminder_msg:
                resp = f"PRIVMSG {channel} :@{user} Reminder: {reminder_msg} (after {time_str})\r\n"
            else:
                resp = f"PRIVMSG {channel} :@{user} You were supposed to be doing something! It has been {time_str}!\r\n"
            sock.send(resp.encode())
            
        threading.Thread(target=threaded_reminder, daemon=True).start()
        resp = f"PRIVMSG {channel} :@{user} Reminder set for {time_str}{' (' + reminder_msg + ')' if reminder_msg else ' (Did you know by adding a message after the time, you can say what to be reminded about?)'}!\r\n"
        sock.send(resp.encode())

def handle_followers(user, channel, sock):
    count = get_follower_count(channel)
    if count is not None:
        resp = f"PRIVMSG {channel} :This channel has {count} followers!\r\n"
    else:
        resp = f"PRIVMSG {channel} :Sorry, couldn't fetch follower count.\r\n"
    sock.send(resp.encode())
    
def handle_raid(channel, sock):
    resp = f"PRIVMSG {channel} :STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 \r\n"
    resp2 = f"PRIVMSG {channel} :^^ LET'S RAID! GO SPAM THE CHAT WITH CATS! 🐈‍⬛ 🐈 🐅! ^^ \r\n"
    sock.send(resp.encode())
    sock.send(resp2.encode())

def handle_lurk(user, channel, sock):
    resp = f"PRIVMSG {channel} :@{user} is lurking! Thanks for the lurk! \r\n"
    sock.send(resp.encode())