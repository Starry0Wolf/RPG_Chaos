import time
import threading
import requests
import json
from twitch_oauth_flow import get_valid_token
from .start import CLIENT_ID, CHANNELS, NICK, get_user_id, get_channel_id

def shoutout(user, channel, sock):
    if not user:
        resp = f"PRIVMSG {channel} :Please specify a user to shoutout!\r\n"
        sock.send(resp.encode())
        return

    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    from_broadcaster_id = get_channel_id('starry0wolf')
    to_broadcaster_id = get_user_id(user)
    moderator_id = get_user_id(NICK)

    if not from_broadcaster_id or not to_broadcaster_id:
        resp = f"PRIVMSG {channel} :Could not find the specified user.\r\n"
        sock.send(resp.encode())
        return

    url = "https://api.twitch.tv/helix/shoutouts"
    payload = {
        "from_broadcaster_id": from_broadcaster_id,
        "to_broadcaster_id": to_broadcaster_id,
        "moderator_id": moderator_id
    }

    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code == 200:
        resp_msg = f"PRIVMSG {channel} :Shoutout to @{user}! Go check them out!\r\n"
    else:
        resp_msg = f"PRIVMSG {channel} :Failed to shoutout @{user}. Error: {resp.status_code}\r\n"
    sock.send(resp_msg.encode())

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

def load_reminders():
    try:
        with open('Storage/reminders.json', 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_reminders(reminders):
    with open('Storage/reminders.json', 'w') as f:
        json.dump(reminders, f, indent=2)

def show_reminders(user, channel, sock):
    reminders = load_reminders()
    user_reminders = reminders.get(user, [])
    
    if not user_reminders:
        resp = f"PRIVMSG {channel} :@{user} You have no active reminders.\r\n"
    else:
        # Filter out expired reminders
        current_time = time.time()
        active_reminders = [r for r in user_reminders if r['end_time'] > current_time]
        
        if not active_reminders:
            resp = f"PRIVMSG {channel} :@{user} You have no active reminders.\r\n"
        else:
            reminder_texts = []
            for r in active_reminders:
                time_left = int(r['end_time'] - current_time)
                minutes_left = time_left // 60
                hours_left = minutes_left // 60
                if hours_left > 0:
                    time_text = f"{hours_left}h"
                else:
                    time_text = f"{minutes_left}m"
                reminder_texts.append(f"{r.get('message', 'No message')} ({time_text} left)")
            
            resp = f"PRIVMSG {channel} :@{user} Your active reminders: {' | '.join(reminder_texts)}\r\n"
    
    sock.send(resp.encode())

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

    if not multiplier or not amount:
        resp = f"PRIVMSG {channel} :@{user} Invalid time format. Use numbers followed by 'm' for minutes or 'h' for hours (e.g., 5m or 2h)\r\n"
        sock.send(resp.encode())
        return

    total_seconds = amount * multiplier
    end_time = time.time() + total_seconds

    # Store the reminder
    reminders = load_reminders()
    if user not in reminders:
        reminders[user] = []
    
    reminders[user].append({
        'message': reminder_msg,
        'end_time': end_time,
        'duration': time_str
    })
    save_reminders(reminders)
        
    def threaded_reminder():
        time.sleep(total_seconds)
        if reminder_msg:
            resp = f"PRIVMSG {channel} :@{user} Reminder: {reminder_msg} (after {time_str})\r\n"
        else:
            resp = f"PRIVMSG {channel} :@{user} You were supposed to be doing something! It has been {time_str}!\r\n"
        sock.send(resp.encode())
        
        # Remove the reminder once it's done
        reminders = load_reminders()
        if user in reminders:
            reminders[user] = [r for r in reminders[user] if r['end_time'] != end_time]
            if not reminders[user]:
                del reminders[user]
            save_reminders(reminders)
            
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
    
def handle_raid(user, channel, sock):
    resp = f"PRIVMSG {channel} :STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 \r\n"
    resp2 = f"PRIVMSG {channel} :^^ LET'S RAID! GO SPAM THE CHAT WITH CATS! 🐈‍⬛ 🐈 🐅! ^^ \r\n"
    sock.send(resp.encode())
    sock.send(resp2.encode())

def handle_lurk(user, channel, sock):
    resp = f"PRIVMSG {channel} :@{user} is lurking! Thanks for the lurk! \r\n"
    sock.send(resp.encode())