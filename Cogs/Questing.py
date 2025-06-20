import json
import random
import time
import re
from .start import get_user_id, CHANNELS

def get_classes(name_class=None):
    with open("Storage/classes.json", "r") as f:
        data = json.load(f)
        class_names = [item['Class'] for item in data if 'Class' in item]
        if name_class is not None:
            return any(c.lower() == name_class.lower() for c in class_names)
        return ", ".join(class_names).capitalize()

def give_class(class_name, target_user):
    UserID = get_user_id(target_user)
    # Get starting weapon for the class
    starting_weapon = None
    with open("Storage/classes.json", "r") as f:
        data = json.load(f)
        for class_data in data:
            if class_data.get('Class', '').lower() == class_name.lower():
                starting_weapon = class_data.get('Weapons', 'fists')
                break

    try:
        with open('Storage/players.json', 'r') as fr:
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

    with open('Storage/players.json', 'w') as fw:
        json.dump(players, fw, indent=2)
    
    return True

def get_player_info(target_user, lookingFor=None):
    """Get all player information including level, money, class, etc."""
    UserID = get_user_id(target_user)
    try:
        with open('Storage/players.json', 'r') as f:
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
    with open('Storage/players.json', 'w') as f:
        json.dump({str(get_user_id(user)): player_info}, f, indent=2)

    return f"PRIVMSG {CHANNELS[0]} :@{user} You have purchased {item_name} for {cost} gold!\r\n"

def get_items():
    """Get all items available for purchase in the shop with their prices."""
    try:
        with open('Storage/itemCosts.json', 'r') as f:
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

def parse_damage_string(damage_str):
    """Parse a damage string like "2d6" or "3d4 + 1" into number of dice, sides, and bonus"""
    pattern = r"(\d+)?d(\d+)(?:\s*\+\s*(\d+))?"
    match = re.match(pattern, damage_str)
    if match:
        num_dice = int(match.group(1)) if match.group(1) else 1
        sides = int(match.group(2))
        bonus = int(match.group(3)) if match.group(3) else 0
        return num_dice, sides, bonus
    return None

def roll_damage(damage_str):
    """Roll damage based on weapon damage string (e.g. "2d6" or "3d4 + 1")"""
    parsed = parse_damage_string(damage_str)
    if parsed:
        num_dice, sides, bonus = parsed
        rolls = [random.randint(1, sides) for _ in range(num_dice)]
        return sum(rolls) + bonus
    return 0

def get_active_quest(user_id):
    """Get active quest for a user"""
    try:
        with open('Storage/active_quests.json', 'r') as f:
            quests = json.load(f)
            return quests.get(str(user_id))
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def save_active_quest(user_id, quest_data):
    """Save or update active quest for a user"""
    try:
        with open('Storage/active_quests.json', 'r') as f:
            quests = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        quests = {}
    
    quests[str(user_id)] = quest_data
    
    with open('Storage/active_quests.json', 'w') as f:
        json.dump(quests, f, indent=2)

def remove_active_quest(user_id):
    """Remove a completed/failed quest"""
    try:
        with open('Storage/active_quests.json', 'r') as f:
            quests = json.load(f)
        if str(user_id) in quests:
            del quests[str(user_id)]
            with open('Storage/active_quests.json', 'w') as f:
                json.dump(quests, f, indent=2)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

def handle_attack(user, channel, sock):
    player_info = get_player_info(user)
    if not player_info:
        resp = f"PRIVMSG {channel} :@{user} You need to start your adventure first! Use !start\r\n"
        sock.send(resp.encode())
        return

    user_id = get_user_id(user)
    quest = get_active_quest(user_id)
    
    if not quest:
        resp = f"PRIVMSG {channel} :@{user} You're not in combat! Use !quest to find a monster to fight\r\n"
        sock.send(resp.encode())
        return

    # Get player's weapon damage from their class
    with open("Storage/classes.json", "r") as f:
        classes = json.load(f)
        weapon_damage = None
        for c in classes:
            if c['Class'].lower() == player_info['class'].lower():
                weapon_damage = c['WeaponDamage']
                break
    
    if not weapon_damage:
        resp = f"PRIVMSG {channel} :@{user} Error: Could not find your class weapon damage\r\n"
        sock.send(resp.encode())
        return

    # Calculate player's damage
    damage = roll_damage(weapon_damage)
    quest['BaseHeath'] -= damage

    # Update quest state
    save_active_quest(user_id, quest)

    # Send combat message
    resp = f"PRIVMSG {channel} :@{user} attacks for {damage} damage! "
    
    if quest['BaseHeath'] <= 0:
        # Quest completed!
        gold_reward = random.randint(50, 150)  # Random gold reward
        exp_reward = random.randint(10, 30)   # Random exp reward
        
        # Update player stats
        try:
            with open('Storage/players.json', 'r') as f:
                players = json.load(f)
            
            player_data = players[str(user_id)]
            player_data['money'] = player_data.get('money', 0) + gold_reward
            
            # Simple leveling system
            current_level = player_data.get('level', 1)
            current_exp = player_data.get('exp', 0) + exp_reward
            exp_needed = current_level * 100  # Simple formula: level * 100 exp needed
            
            if current_exp >= exp_needed:
                player_data['level'] = current_level + 1
                resp += f"LEVEL UP! You are now level {current_level + 1}! "
            
            player_data['exp'] = current_exp
            players[str(user_id)] = player_data
            
            with open('Storage/players.json', 'w') as f:
                json.dump(players, f, indent=2)
                
            resp += f"Victory! The monster is defeated! You gain {gold_reward} gold and {exp_reward} experience!\r\n"
            remove_active_quest(user_id)
            
        except Exception as e:
            resp += f"Victory! But there was an error saving rewards: {str(e)}\r\n"
            
    else:
        # Monster still alive - it attacks back
        monster_damage = random.randint(quest['Damage']['BaseDamage'], 
                                      quest['Damage']['BaseDamage'] + quest['Damage']['AddonDamage'])
        resp += f"Monster has {quest['BaseHeath']} HP left and strikes back for {monster_damage} damage!\r\n"

    sock.send(resp.encode())

def handle_quest(user, channel, sock):
    if get_player_info(user) is None:
        available_classes = get_classes()
        resp = f"PRIVMSG {channel} :@{user} Please choose one of the following classes: {available_classes}. Then use the command '!class <choice>'. After that you can rerun this command to do the quest!\r\n"
        sock.send(resp.encode())
        return

    user_id = get_user_id(user)
    current_quest = get_active_quest(user_id)
    if current_quest:
        resp = f"PRIVMSG {channel} :@{user} You're already in combat! The monster has {current_quest['BaseHeath']} HP left! Use !attack to fight!\r\n"
        sock.send(resp.encode())
        return

    currentLevel = get_player_info(target_user=user, lookingFor='level')
    boss_stats = make_quests(level=currentLevel)
    save_active_quest(user_id, boss_stats)
    
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