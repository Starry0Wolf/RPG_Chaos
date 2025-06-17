import json
from .start import get_user_id

def update_task_completion(user):
    try:
        with open('Storage/players.json', 'r') as f:
            players = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        players = {}

    userID = str(get_user_id(user))
    if userID in players:
        players[userID]['tasks_completed'] = players[userID].get('tasks_completed', 0) + 1
    else:
        players[userID] = {'tasks_completed': 1}

    with open('Storage/players.json', 'w') as f:
        json.dump(players, f, indent=2)

def handle_done(user, channel, sock, tasksHuman):
    userID = str(get_user_id(user))
    task = None
    for t in tasksHuman[:]:  # Use slice to iterate over copy while modifying original
        if t.startswith(f"{userID}:"):
            task = t.split(":", 1)[1].strip(" '")  # Extract task text
            tasksHuman.remove(t)
            break
    
    if not task:
        resp = f"PRIVMSG {channel} :@{user} You have no tasks to complete! Use !task to create one! Like '!task Take a nap'\r\n"
        sock.send(resp.encode())
        return
        
    resp = f"PRIVMSG {channel} :@{user} Good job finishing {task}! Here is a reward 🍪.\r\n"
    sock.send(resp.encode())
    update_task_completion(user)

def handle_task(user, channel, sock, task):
    if not task:
        resp = f"PRIVMSG {channel} :@{user} Please specify a task to do!\r\n"
    else:
        resp = f"PRIVMSG {channel} :@{user} has started the task: {task}\r\n"
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