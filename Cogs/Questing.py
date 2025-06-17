import json
import random
import time
from .start import get_user_id, CHANNELS

def get_classes(name_class=None):
    with open("classes.json", "r") as f:
        data = json.load(f)
        class_names = [item['Class'] for item in data if 'Class' in item]
        if name_class is not None:
            return any(c.lower() == name_class.lower() for c in class_names)
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

def get_player_info(target_user, lookingFor=None):
    """Get all player information including level, money, class, etc."""
    UserID = get_user_id(target_user)
    try:
        with open('players.json', 'r') as f:
            players = json.load(f)
            if str(UserID) in players:
                player_data = players[str(UserID)]
                if lookingFor:
                    return player_data.get(lookingFor)
                return {
                    'class': player_data.get('class', 'No Class'),
                    'level': player_data.get('level', 0),
                    'money': player_data.get('money', 0),
                    'weapon': player_data.get('weapon', 'fists'),
                    'start_time': player_data.get('start', None)
                }
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return None

def make_quests(level):
    Heathpoints = random.randint(10, 100)
    Weapon = random.choice(['gun', 'crossbow', 'long sword', 'great axe', 'ninja star'])
    
    if random.randint(0, 3) == 0:
        Damage = {
            "BaseDamage": random.randint(4, 12),
            "AddonDamage": random.randint(1, 3)
        }
    else:
        Damage = {
            "BaseDamage": random.randint(4, 12),
            "AddonDamage": 0
        }

    return {
        "Damage": Damage,
        "Weapon": Weapon,
        "BaseHeath": Heathpoints
    }

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
    try:
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
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def handle_quest(user, channel, sock):
    if get_player_info(user) is None:
        available_classes = get_classes()
        resp = f"PRIVMSG {channel} :@{user} Please choose one of the following classes: {available_classes}. Then use the command '!class <choice>'. After that you can rerun this command to do the quest!\r\n"
        sock.send(resp.encode())
    else:
        currentLevel = get_player_info(target_user=user, lookingFor='level')
        boss_stats = make_quests(level=currentLevel)
        resp = f"PRIVMSG {channel} :@{user} You encounter a boss with {boss_stats['BaseHeath']} HP wielding a {boss_stats['Weapon']}! Use !attack to fight!\r\n"
        sock.send(resp.encode())

def handle_start(user, channel, sock):
    available_classes = get_classes()
    resp = f"PRIVMSG {channel} :@{user} Please choose one of the following classes: {available_classes}. Then use the command '!class <choice>'\r\n"
    sock.send(resp.encode())

def handle_class(user, channel, sock, selected_class):
    if not selected_class:
        resp = f"PRIVMSG {channel} :@{user} Please specify a class to choose. Available classes: {get_classes()}\r\n"
        sock.send(resp.encode())
        return
        
    isClass = get_classes(selected_class)
    if isClass:
        give_class(class_name=selected_class, target_user=user)
        resp = f"PRIVMSG {channel} :@{user} You have been given a class!\r\n"
        sock.send(resp.encode())

def handle_level(user, channel, sock):
    level = get_player_info(target_user=user, lookingFor='level')
    if level:
        resp = f"PRIVMSG {channel} :@{user} You are level {level}!\r\n"
    else:
        resp = f"PRIVMSG {channel} :@{user} You haven't started your adventure yet! Use !start to begin.\r\n"
    sock.send(resp.encode())

def handle_info(user, channel, sock):
    player_info = get_player_info(user)
    if player_info:
        playtime = time.time() - player_info['start_time'] if player_info['start_time'] else 0
        playtime_hours = round(playtime / 3600, 1)
        resp = f"PRIVMSG {channel} :@{user} Class: {player_info['class']} | Level: {player_info['level']} | Money: {player_info['money']} gold | Playtime: {playtime_hours}h\r\n"
    else:
        resp = f"PRIVMSG {channel} :@{user} You haven't started your adventure yet! Use !start to begin.\r\n"
    sock.send(resp.encode())