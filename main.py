import socket
import requests
from twitch_oauth_flow import get_valid_token, get_user_id
from dotenv import load_dotenv
import os
import threading
import time
import json
import random
import ssl
# TODO: FIX ALIASES
load_dotenv()
CLIENT_ID = os.getenv('CLIENT_ID')
HOST = 'irc.chat.twitch.tv'
PORT = 6667
NICK = 'rpg_chaos'          # Your bot account’s username
CHANNELS = ['#starry0wolf']  # Renamed for clarity

def connect():
    """Connect to Twitch IRC with an auto-refreshed token."""
    token = get_valid_token()
    context = ssl.create_default_context()
    sock = socket.socket()
    ssl_sock = context.wrap_socket(sock, server_hostname=HOST)
    ssl_sock.connect((HOST, PORT))
    sock.send(f"PASS oauth:{token}\r\n".encode())
    sock.send(f"NICK {NICK}\r\n".encode())
    # Join each channel individually
    for channel in CHANNELS:
        sock.send(f"JOIN {channel}\r\n".encode())
    return sock

def who_am_i(token):
    headers = {
        'Authorization': f'Bearer {token}'
    }
    url = 'https://id.twitch.tv/oauth2/validate'
    resp = requests.get(url, headers=headers)
    # print(f"[DEBUG] Token Identity: {resp.status_code} {resp.text}")
    return resp.json()

# Add this function somewhere accessible (e.g., near your imports or before main())
def shoutout(target_user):
    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    from_broadcaster_id = get_channel_id('starry0wolf')
    to_broadcaster_id = get_user_id(target_user)
    moderator_id = get_user_id(NICK)  # assuming bot is the streamer or a mod

    # print(f"[DEBUG] From: {from_broadcaster_id}, To: {to_broadcaster_id}, Mod: {moderator_id}")

    if not from_broadcaster_id or not to_broadcaster_id:
        print("[ERROR] Missing broadcaster ID(s)")
        return {"status": 404}

    url = "https://api.twitch.tv/helix/shoutouts"
    payload = {
        "from_broadcaster_id": from_broadcaster_id,
        "to_broadcaster_id": to_broadcaster_id,
        "moderator_id": moderator_id
    }

    resp = requests.post(url, headers=headers, json=payload)
    # print(f"[DEBUG] shoutout() status: {resp.status_code}, response: {resp.text}")
    return resp

def get_user_id(username):
    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    url = f"https://api.twitch.tv/helix/users?login={username}"
    resp = requests.get(url, headers=headers)
    # print(f"[DEBUG] get_user_id({username}) returned: {resp.status_code} {resp.text}")
    data = resp.json()
    if data.get('data'):
        return data['data'][0]['id']
    return None

def get_channel_id(username):
    # Same as get_user_id but for your channel
    return get_user_id(username)

def channel_wide_announcement(message, sock):
    for channel in CHANNELS:
        resp = f"PRIVMSG {channel} :{message}\r\n"
        sock.send(resp.encode())

def send_reminder(user, minutes, sock):
    time.sleep(minutes * 60)
    resp = f"PRIVMSG {CHANNELS} :@{user} you were supposed to be doing something! It has been {minutes} minutes!\r\n"
    sock.send(resp.encode())

def get_follower_count(channel_name):
    token = get_valid_token()
    headers = {
        'Client-ID': CLIENT_ID,
        'Authorization': f'Bearer {token}'
    }
    # Get the user ID for the channel
    user_id = get_user_id(channel_name.lstrip('#'))
    if not user_id:
        return None
    url = f"https://api.twitch.tv/helix/users/follows?to_id={user_id}"
    resp = requests.get(url, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        return data.get('total')
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
        if data.get('data') and data['data'][0].get('broadcaster_type') == 'affiliate':
            return True
    return False

def get_classes(name_class=None):
    with open("classes.json", "r") as f:
        data = json.load(f)
        class_names = [item['Class'] for item in data if 'Class' in item]
        if name_class != None:
            if [c for c in class_names if c.lower() == name_class.lower()]:
                return True
            return False
        return ", ".join(class_names).capitalize()

def give_class(class_name, target_user):
    UserID = get_user_id(target_user)
    # Get starting weapon for the class
    starting_weapon = None
    with open("classes.json", "r") as f:
        data = json.load(f)
        for class_data in data:
            if class_data.get('Class', '').lower() == class_name.lower():
                starting_weapon = class_data.get('Weapons', 'fists')
                break

    try:
        with open('players.json', 'r') as fr:
            players = json.load(fr)
    except (FileNotFoundError, json.JSONDecodeError):
        players = {}

    # Preserve existing player data if any
    player_data = players.get(str(UserID), {})
    # Update only the class-specific fields
    class_data = {
        "class": class_name,
        "level": 1,
        "money": 250,
        "weapon": starting_weapon,
        "start": time.time()
    }
    # Merge the data, keeping existing fields intact
    player_data.update(class_data)
    players[str(UserID)] = player_data

    with open('players.json', 'w') as fw:
        json.dump(players, fw, indent=2)
    
    return True

def get_player_info(target_user, lookingFor = None):
    """Get all player information including level, money, class, etc."""
    UserID = get_user_id(target_user)
    try:
        with open('players.json', 'r') as f:
            players = json.load(f)
        user_data = players.get(str(UserID))
        if user_data:
            userInfo = {
                'class': user_data.get('class', 'No Class'),
                'level': user_data.get('level', 0),
                'money': user_data.get('money', 0),
                'weapons': user_data.get('weapon', 0 ),
                'start_time': user_data.get('Start', None)
            }
            if lookingFor == None:
                return userInfo
            else:
                print(userInfo[lookingFor])
                return userInfo[lookingFor]
        return None
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def make_quests(level):
    Heathpoints = random.randint(10,100)
    #TODO: ADD MORE WEAPONS
    Weapon = random.choice(['gun', 'crossbow', 'long sword', 'great axe', 'ninja star'])
    #TODO: MAKE BASE DAMAGE BASED OFF THE WEAPON
    if random.randint(0,3) == 0:
        Damage = {
            "BaseDamage": random.randint(4,12),
            "AddonDamage": random.randint(1,3)
        }
    else:
        Damage = {
            "BaseDamage": random.randint(4,12),
            "AddonDamage": 0
        }

    Stats = {
        "Damage": Damage,
        "Weapon": Weapon,
        "BaseHeath": Heathpoints
    }
    return Stats

def purchase_item(user, item_name, cost):
    """Purchase an item for the user if they have enough money."""
    player_info = get_player_info(user)
    if not player_info:
        return f"PRIVMSG {CHANNELS[0]} :@{user} You need to start your adventure first! Use !start.\r\n"

    if player_info['money'] < cost:
        return f"PRIVMSG {CHANNELS[0]} :@{user} You don't have enough money to buy {item_name}!\r\n"

    # Deduct cost and update player info
    player_info['money'] -= cost
    with open('players.json', 'w') as f:
        json.dump({str(get_user_id(user)): player_info}, f, indent=2)

    return f"PRIVMSG {CHANNELS[0]} :@{user} You have purchased {item_name} for {cost} gold!\r\n"

def get_items():
    """Get all items available for purchase in the shop with their prices."""
    # Read available items
    # with open('shop_items.json', 'r') as f:
    #     items = json.load(f)

    # Read item costs
    with open('itemCosts.json', 'r') as f:
        costs = json.load(f)
        items = [item for item in costs.keys()]

    # Combine items with their costs
    items_with_costs = {}
    for item_name in items:
        if item_name in costs:
            items_with_costs[item_name] = {
                "details": items[item_name],
                "cost": costs[item_name]["Cost"]
            }

    return items_with_costs

def start_shop():
    # This creates the stuff you can buy in the shop.
    available_items = get_items()
    for i in range(4):
        items,cost = get_items()

# def get_item_info(item_name):

tasksHuman = []

def main():
    sock = connect()
    while True:
        data = sock.recv(2048).decode()
        if data.startswith('PING'):
            sock.send("PONG :tmi.twitch.tv\r\n".encode())
            continue

        if 'PRIVMSG' not in data:
            continue

        # Extract channel from message
        channel = data.split('PRIVMSG')[1].split(':', 1)[0].strip().split(' ')[0]
        user = data.split('!', 1)[0][1:]
        msg  = data.split('PRIVMSG', 1)[1].split(':', 1)[1].strip()
        print(f"{user}@{channel}: {msg}")

        lower = msg.lower()

        # 1 Exact chat commands
        if lower == '!chaos':
            resp = f"PRIVMSG {channel} :@{user} You have lost the game! . . . . . . . . . . . . . . .\r Never gonna give you up, never gonna let you down, never gonna spin you 'round. \r\n"
            sock.send(resp.encode())
        
        elif lower == '!done':
            userID = get_user_id(user)
            task = None
            for t in tasksHuman[:]:  # Use slice to iterate over copy while modifying original
                if t.startswith(f"{userID}:"):
                    task = t.split(":", 1)[1].strip(" '")  # Extract task text
                    tasksHuman.remove(t)
                    break
            if not task:
                resp = f"PRIVMSG {channel} :@{user} You have no tasks to complete! Use !task to create one! Like '!task Take a nap'\r\n"
                sock.send(resp.encode())
                continue
            resp = f"PRIVMSG {channel} :@{user} Good job finishing {task}! Here is a reward 🍪.\r\n"
            # First send the message
            sock.send(resp.encode())
            
            # Update tasks completed count in players.json
            try:
                with open('players.json', 'r') as f:
                    players = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                players = {}

            userID = str(get_user_id(user))
            if userID in players:
                # Add or increment tasks_completed
                players[userID]['tasks_completed'] = players[userID].get('tasks_completed', 0) + 1
            else:
                # Create minimal entry just for tasks if user hasn't started game
                players[userID] = {'tasks_completed': 1}

            with open('players.json', 'w') as f:
                json.dump(players, f, indent=2)


        elif lower == '!lurk':
            resp = f"PRIVMSG {channel} :@{user} is lurking! Thanks for the lurk! \r\n"
            sock.send(resp.encode())

        elif lower == '!raid':
            resp = f"PRIVMSG {channel} :STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 STARRY0WOLF RAID! 🐈‍⬛ 🐈 🐅 \r\n"
            resp2 = f"PRIMSG {channel} :^^ LET'S RAID! GO SPAM THE CHAT WITH CATS! 🐈‍⬛ 🐈 🐅! ^^ \r\n"
            sock.send(resp.encode())
            sock.send(resp2.encode())

        elif lower == '!intro':
            resp = f"PRIVMSG {channel} :@{user} Hello! I'm a simple RPG bot made by @Starry0Wolf! Inspired by the @ada_rpg bot, I aim to provide a bit more than Ada. Ada's code organization is a mess, and is coded in the insane language of JavaScript! The reason I was created was that @ribbons_ would not add a cat class, but she said I could make my own bot, so I did, you can check out the coding streams on @Starry0Wolf's channel.\r\n"
            sock.send(resp.encode())

        # Questing
        elif lower == '!start':
            available_classes = get_classes()
            resp = f"PRIVMSG {channel} :@{user} Please choose one of the following classes: {available_classes}. Then use the command '!class <choice>'\r\n"
            sock.send(resp.encode())

        elif lower == '!quest':
            if get_player_info(user) == None:
                available_classes = get_classes()
                resp = f"PRIVMSG {channel} :@{user} Please choose one of the following classes: {available_classes}. Then use the command '!class <choice>. After that you can rerun this command to do the quest!'\r\n"
                sock.send(resp.encode())
            else:
                currentLevel = get_player_info(target_user=user, lookingFor='class')
                StartingBossStats = make_quests(level=currentLevel)
                print(StartingBossStats)
                print()
                resp = f"PRIVMSG {channel} :@{user} Your quest: Slay the dragon!\r\n"
                sock.send(resp.encode())

        # 2) Pattern match: startswith 'bex' AND contains 'reeere'
        # elif lower.startswith('!chaos') and 'remind' in lower:
        #     parts = msg.split()
        #     if len(parts) > 1:
        #         minutes = parts[3]
        #     # resp = f"PRIVMSG {CHANNEL} :@{user} you were supposed to be doing something! It has been {minutes}!\r\n"
        #     print(resp)
        #     sock.send(resp.encode())

        # class

        elif lower.startswith('!task'):
            parts = msg.split()
            if len(parts) > 1:
                userID = get_user_id(user)
                task = " ".join(parts[1:])  # Get everything after !task
                existing_tasks = [t.split(':', 1)[1].strip(" '") for t in tasksHuman if t.startswith(f"{userID}:")]
                print(existing_tasks)
                
                if existing_tasks:
                    resp = f"PRIVMSG {channel} :@{user} You should finish {existing_tasks[0]} first!\r\n"
                else:
                    task_entry = f"{userID}: '{task}'"
                    tasksHuman.append(task_entry)
                    resp = f"PRIVMSG {channel} :@{user} Task added: {task}\r\n"
                sock.send(resp.encode())


        elif lower.startswith('!attack'):
            parts = msg.split()
            defaultWeapon = get_player_info(target_user=user, lookingFor='weapon'[0])
            if len(parts) > 1:
                selectedWeapon = parts[1]
            else:
                selectedWeapon = defaultWeapon


        elif lower.startswith('!class'):
            parts = msg.split()
            if len(parts) > 1:
                selected_class = parts[1]
                isClass = get_classes(selected_class)
                hasClass = get_player_info(target_user=user, lookingFor='class')  # <-- FIXED: pass user, not selected_class
                print(hasClass)
                # if hasClass is not None:
                #     resp = f"PRIVMSG {channel} :@{user} Sorry! You already have a class, currently I have not added class switching! DM me to remind me to add it!\r\n"
                #     sock.send(resp.encode())
                if isClass == True:
                    give_class(class_name=selected_class, target_user=user)
                    resp = f"PRIVMSG {channel} :@{user} You have been given a class!\r\n"
                    sock.send(resp.encode())


        elif lower.startswith('!cwa'):
            parts = msg.split()
            if len(parts) > 1:
                message = parts[1]
                # resp = f"PRIVMSG {channel} :Channel wide announcement sent!\r\n"
                # sock.send(resp.encode())
                for channel in CHANNELS:
                    resp2 = f"PRIVMSG {channel} :{message}\r\n"
                    sock.send(resp2.encode())
            else:
                resp = f"PRIVMSG {channel} :Usage: !cwa <message>\r\n"

        elif lower.startswith('!remind'):
            parts = msg.split()
            if len(parts) > 2:
                # Expecting: !chaos remind 3m [optional message...]
                time_str = parts[2].lower()
                reminder_msg = " ".join(parts[3:]).strip() if len(parts) > 3 else None

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
                    def threaded_reminder(user, seconds, sock, reminder_msg):
                        time.sleep(seconds)
                        if reminder_msg:
                            resp = f"PRIVMSG {channel} :@{user} Reminder: {reminder_msg} (after {time_str})\r\n"
                        else:
                            resp = f"PRIVMSG {channel} :@{user} You were supposed to be doing something! It has been {time_str}!\r\n"
                        sock.send(resp.encode())
                    threading.Thread(target=threaded_reminder, args=(user, total_seconds, sock, reminder_msg), daemon=True).start()
                    resp = f"PRIVMSG {channel} :@{user} Reminder set for {time_str}{' (' + reminder_msg + ')' if reminder_msg else ' (Did you know by adding a message after the time, you can say what to be reminded about?)'}!\r\n"
                    sock.send(resp.encode())
                else:
                    resp = f"PRIVMSG {channel} :@{user} Invalid time format. Use like '!chaos remind 3m' or '!chaos remind 2h'\r\n"
                    sock.send(resp.encode())
            else:
                resp = f"PRIVMSG {channel} :@{user} Usage: !chaos remind 3m [what to remind you about]\r\n"
                sock.send(resp.encode())
        
        elif lower.startswith('!so'):
            parts = msg.split()
            if len(parts) > 1:
                target = parts[1].lstrip('@').capitalize()
                if not is_affiliate(channel):
                    resp = f"PRIVMSG {channel} :We can't do this until we are affiliate. But still EVERYONE GO FOLLOW {target}!\r\n"
                    sock.send(resp.encode())
                    sock.send(resp.encode())
                    sock.send(resp.encode())
                else:
                    resp = shoutout(target)
                    if isinstance(resp, dict) and resp.get('status') == 404:
                        reply = f"PRIVMSG {channel} :@{user} Couldn't find user @{target} on Twitch.\r\n"
                    elif hasattr(resp, 'status_code') and resp.status_code == 204:
                        reply = f"PRIVMSG {channel} :@{user} Shoutout to @{target}!\r\n"
                    else:
                        reply = f"PRIVMSG {channel} :@{user} Failed to shout out @{target}. Status {resp.status_code}\r\n"
                    sock.send(reply.encode())
            else:
                resp = f"PRIVMSG {channel} :@{user} Usage: !so <username>\r\n"
                sock.send(resp.encode())


        # 4) Other “!” commands or fallback
        elif lower == '!followers':
            count = get_follower_count(channel)
            if count != None:
                resp = f"PRIVMSG {channel} :This channel has {count} followers!\r\n"
            else:
                resp = f"PRIVMSG {channel} :Sorry, couldn't fetch follower count.\r\n"
            sock.send(resp.encode())

        elif lower == '!info':
            player_info = get_player_info(user)
            if player_info:
                playtime = time.time() - player_info['start_time'] if player_info['start_time'] else 0
                playtime_hours = round(playtime / 3600, 1)
                resp = f"PRIVMSG {channel} :@{user} Class: {player_info['class']} | Level: {player_info['level']} | Money: {player_info['money']} gold | Playtime: {playtime_hours}h\r\n"
            else:
                resp = f"PRIVMSG {channel} :@{user} You haven't started your adventure yet! Use !start to begin.\r\n"
            sock.send(resp.encode())

        elif lower == '!level':
            level = get_player_info(target_user=user, lookingFor='level')
            if level:
                resp = f"PRIVMSG {channel} :@{user} You are level {level}!\r\n"
            else:
                resp = f"PRIVMSG {channel} :@{user} You haven't started your adventure yet! Use !start to begin.\r\n"
            sock.send(resp.encode())

        elif lower.startswith('!'):
            resp = f"PRIVMSG {channel} :@{user} Unknown command: {msg}\r\n"
            sock.send(resp.encode())


if __name__ == "__main__":
    print("Starting bot. Press Ctrl+C to stop.")
    main()
