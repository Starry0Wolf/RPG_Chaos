import json
from .start import get_user_id

def update_task_completion(user):
    userID = str(get_user_id(user))
    try:
        with open('Storage/players.json', 'r') as f:
            players = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        players = {}
    if userID not in players:
        players[userID] = {}
    players[userID]['tasks_completed'] = players[userID].get('tasks_completed', 0) + 1
    with open('Storage/players.json', 'w') as f:
        json.dump(players, f, indent=2)

def handle_done(user, channel, sock, tasksHuman=None, task_number=None):
    userID = str(get_user_id(user))
    try:
        with open('Storage/players.json', 'r') as f:
            players = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        players = {}
    user_tasks = players.get(userID, {}).get('tasks', [])
    if not user_tasks:
        resp = f"PRIVMSG {channel} :@{user} You have no tasks to complete! Use !task to create one! Like '!task Take a nap'\r\n"
        sock.send(resp.encode())
        return
    # If only one task, or valid number provided, complete it
    if len(user_tasks) == 1 or (task_number and task_number.isdigit() and 1 <= int(task_number) <= len(user_tasks)):
        idx = 0 if len(user_tasks) == 1 else int(task_number) - 1
        finished_task = user_tasks.pop(idx)
        players[userID]['tasks'] = user_tasks
        players[userID]['tasks_completed'] = players[userID].get('tasks_completed', 0) + 1
        with open('Storage/players.json', 'w') as f:
            json.dump(players, f, indent=2)
        resp = f"PRIVMSG {channel} :@{user} Good job finishing {finished_task}! Here is a reward 🍪.\r\n"
        sock.send(resp.encode())
    else:
        # Show numbered list and prompt (single line for Twitch)
        tasks_list = ' | '.join([f"{i+1}. {task}" for i, task in enumerate(user_tasks)])
        resp = f"PRIVMSG {channel} :@{user} You have multiple tasks. Please specify which one to complete using !done <number>: {tasks_list}\r\n"
        sock.send(resp.encode())

def handle_task(user, channel, sock, task, tasksHuman=None):
    userID = str(get_user_id(user))
    if not task:
        resp = f"PRIVMSG {channel} :@{user} Please specify a task to do!\r\n"
        sock.send(resp.encode())
        return
    try:
        with open('Storage/players.json', 'r') as f:
            players = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        players = {}
    if userID not in players:
        players[userID] = {}
    if 'tasks' not in players[userID]:
        players[userID]['tasks'] = []
    players[userID]['tasks'].append(task)
    with open('Storage/players.json', 'w') as f:
        json.dump(players, f, indent=2)
    resp = f"PRIVMSG {channel} :@{user} has started the task: {task}\r\n"
    sock.send(resp.encode())

def handle_list_tasks(user, channel, sock, tasksHuman=None):
    userID = str(get_user_id(user))
    try:
        with open('Storage/players.json', 'r') as f:
            players = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        players = {}
    user_tasks = players.get(userID, {}).get('tasks', [])
    if not user_tasks:
        resp = f"PRIVMSG {channel} :@{user} You have no current tasks. Use !task to add one!\r\n"
    else:
        tasks_list = ' | '.join([f"{i+1}. {task}" for i, task in enumerate(user_tasks)])
        resp = f"PRIVMSG {channel} :@{user} Your current tasks: {tasks_list}\r\n"
    sock.send(resp.encode())

def handle_chaos(user, channel, sock):
    resp = f"PRIVMSG {channel} :@{user} You have lost the game! Never gonna give you up, never gonna let you down, never gonna spin you 'round.\r\n"
    sock.send(resp.encode())

def handle_intro(user, channel, sock):
    resp = f"PRIVMSG {channel} :@{user} Hello! I'm a simple RPG bot made by @Starry0Wolf! Inspired by the @ada_rpg bot, I aim to provide a bit more than Ada. Ada's code organization is a mess, and is coded in the insane language of JavaScript! The reason I was created was that @ribbons_ would not add a cat class, but she said I could make my own bot, so I did, you can check out the coding streams on @Starry0Wolf's channel.\r\n"
    sock.send(resp.encode())

def handle_WIP(user, channel, sock):
    resp = f"PRIVMSG {channel} :@{user} Hey, so sorry, but this command is not yet completed, if you can code, come check out my github repo, and make these updates come faster!"
    sock.send(resp.encode)