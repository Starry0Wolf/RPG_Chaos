# filepath: /Users/starry/Desktop/Code/RPG_Chaos/Cogs/Commands.py
from .Streaming import (
    handle_lurk, handle_raid, shoutout,
    get_follower_count, is_affiliate, send_reminder,
    handle_followers
)
from .Questing import (
    get_classes, handle_quest, handle_level,
    handle_info, handle_class, handle_start
)
from .misc import handle_intro, handle_done, handle_task, handle_chaos, handle_WIP

# Command registry with aliases
COMMANDS = {
    # Basic commands
    # '!chaos': handle_chaos,
    '!intro': handle_intro,
    '!done': handle_done,
    
    # Streaming commands
    '!lurk': handle_lurk,
    '!raid': handle_raid,
    # '!so': shoutout,
    # '!shoutout': shoutout,  # alias
    '!followers': handle_followers,
    
    # RPG commands
    '!start': handle_start,
    '!quest': handle_quest,
    '!class': handle_class,
    '!level': handle_level,
    '!lvl': handle_level,  # alias
    '!info': handle_info,
    '!stats': handle_info,  # alias
    
    # Task commands
    '!task': handle_task,
    '!todo': handle_task,  # alias
    
    # Reminder commands
    '!remind': send_reminder,
    '!reminder': send_reminder,  # alias
    '!remindme': send_reminder,
}

def handle_command(user, channel, msg, sock, tasksHuman):
    """Main command handler that routes commands to their specific handlers"""
    parts = msg.lower().split()
    if not parts:
        return
        
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    # Special handling for commands that start with a prefix
    if cmd.startswith('!task'):
        COMMANDS['!task'](user, channel, sock, ' '.join(args))
    elif cmd.startswith('!class'):
        COMMANDS['!class'](user, channel, sock, args[0] if args else None)
    elif cmd.startswith('!so'):
        COMMANDS['!so'](user, channel, sock, args[0] if args else None)
    elif cmd.startswith('!remind'):
        if len(args) >= 1:
            COMMANDS['!remind'](user, channel, sock, args[0], ' '.join(args[1:]) if len(args) > 1 else None)
    # Handle exact matches
    elif cmd in COMMANDS:
        COMMANDS[cmd](user, channel, sock)
    # Unknown command
    elif cmd.startswith('!'):
        resp = f"PRIVMSG {channel} :@{user} Unknown command: {msg}\r\n"
        sock.send(resp.encode())