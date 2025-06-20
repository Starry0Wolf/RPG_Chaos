# filepath: /Users/starry/Desktop/Code/RPG_Chaos/Cogs/Commands.py
from .Streaming import (
    handle_lurk, handle_raid, shoutout,
    get_follower_count, is_affiliate, send_reminder,
    handle_followers, show_reminders
)
from .Questing import (
    get_classes, handle_quest, handle_level,
    handle_info, handle_class, handle_start,
    handle_attack
)
from .misc import handle_intro, handle_done, handle_task, handle_chaos, handle_WIP
from .config import is_command_enabled, is_feature_enabled

# Command registry with aliases and argument requirements
COMMANDS = {
    # Basic commands
    '!chaos': {'handler': handle_chaos, 'needs_tasks': False},
    '!intro': {'handler': handle_intro, 'needs_tasks': False},
    '!done': {'handler': handle_done, 'needs_tasks': True},
    
    # Streaming commands
    '!lurk': {'handler': handle_lurk, 'needs_tasks': False},
    '!raid': {'handler': handle_raid, 'needs_tasks': False},
    '!so': {'handler': shoutout, 'needs_tasks': False},
    '!shoutout': {'handler': shoutout, 'needs_tasks': False},  # alias
    '!followers': {'handler': handle_followers, 'needs_tasks': False},
    
    # RPG commands
    '!start': {'handler': handle_start, 'needs_tasks': False},
    '!quest': {'handler': handle_quest, 'needs_tasks': False},
    '!attack': {'handler': handle_attack, 'needs_tasks': False},
    '!class': {'handler': handle_class, 'needs_tasks': False},
    '!level': {'handler': handle_level, 'needs_tasks': False},
    '!lvl': {'handler': handle_level, 'needs_tasks': False},  # alias
    '!info': {'handler': handle_info, 'needs_tasks': False},
    '!stats': {'handler': handle_info, 'needs_tasks': False},  # alias
    
    # Task commands
    '!task': {'handler': handle_task, 'needs_tasks': False},
    '!todo': {'handler': handle_task, 'needs_tasks': False},  # alias
    
    # Reminder commands
    '!remind': {'handler': send_reminder, 'needs_tasks': False},
    '!reminder': {'handler': send_reminder, 'needs_tasks': False},  # alias
    '!remindme': {'handler': send_reminder, 'needs_tasks': False},  # alias
    '!reminders': {'handler': show_reminders, 'needs_tasks': False},  # Command to list active reminders
    '!listreminders': {'handler': show_reminders, 'needs_tasks': False}  # alias
}

def handle_command(user, channel, msg, sock, tasksHuman):
    """Main command handler that routes commands to their specific handlers"""
    parts = msg.lower().split()
    if not parts:
        return
        
    cmd = parts[0]
    args = parts[1:] if len(parts) > 1 else []
    
    # Check if command exists and is enabled
    if not cmd in COMMANDS or not is_command_enabled(cmd):
        if cmd.startswith('!'):
            resp = f"PRIVMSG {channel} :@{user} This command is not available.\r\n"
            sock.send(resp.encode())
        return
        
    # Get command handler and whether it needs tasksHuman
    command = COMMANDS[cmd]
    handler = command['handler']
    needs_tasks = command['needs_tasks']
    
    # Special handling for commands that start with a prefix
    if cmd in ['!task', '!todo']:
        if not is_feature_enabled('tasks'):
            resp = f"PRIVMSG {channel} :@{user} Tasks are currently disabled.\r\n"
            sock.send(resp.encode())
            return
        handler(user, channel, sock, ' '.join(args) if args else None)
    elif cmd.startswith('!class'):
        handler(user, channel, sock, args[0] if args else None)
    elif cmd in ['!so', '!shoutout']:
        if not args:
            resp = f"PRIVMSG {channel} :@{user} Please specify a user to shoutout!\r\n"
            sock.send(resp.encode())
            return
        handler(args[0] if args else None)
    elif cmd in ['!remind', '!reminder', '!remindme']:
        if not is_feature_enabled('reminders'):
            resp = f"PRIVMSG {channel} :@{user} Reminders are currently disabled.\r\n"
            sock.send(resp.encode())
            return
        if len(args) >= 1:
            time_str = args[0]
            reminder_msg = ' '.join(args[1:]) if len(args) > 1 else None
            handler(user, channel, sock, time_str, reminder_msg)
        else:
            resp = f"PRIVMSG {channel} :@{user} Please specify a time for the reminder (e.g., 5m or 2h)\r\n"
            sock.send(resp.encode())
    elif cmd in ['!reminders', '!listreminders']:
        if not is_feature_enabled('reminders'):
            resp = f"PRIVMSG {channel} :@{user} Reminders are currently disabled.\r\n"
            sock.send(resp.encode())
            return
        handler(user, channel, sock)
    # Handle commands that need tasksHuman
    elif needs_tasks:
        handler(user, channel, sock, tasksHuman)
    # Handle other commands
    else:
        handler(user, channel, sock)