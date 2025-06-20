import json
import os

def load_config():
    """Load configuration from config.json"""
    config_path = os.path.join('Storage', 'config.json')
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return default config if file doesn't exist or is invalid
        return {
            "features": {
                "tasks": True,
                "quests": True,
                "reminders": True,
                "streaming": True,
                "raids": True,
                "shop": True
            },
            "commands": {
                "!task": True,
                "!todo": True,
                "!done": True,
                "!quest": True,
                "!attack": True,
                "!class": True,
                "!level": True,
                "!info": True,
                "!stats": True,
                "!remind": True,
                "!reminder": True,
                "!remindme": True,
                "!reminders": True,
                "!listreminders": True,
                "!lurk": True,
                "!raid": True,
                "!followers": True,
                "!intro": True,
                "!chaos": False
            },
            "settings": {
                "max_reminder_duration_hours": 24,
                "max_tasks_per_user": 5,
                "max_level": 100,
                "exp_per_level": 100,
                "gold_reward_min": 50,
                "gold_reward_max": 150,
                "exp_reward_min": 10,
                "exp_reward_max": 30
            }
        }

def save_config(config):
    """Save configuration to config.json"""
    config_path = os.path.join('Storage', 'config.json')
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)

def is_command_enabled(command):
    """Check if a command is enabled in config"""
    config = load_config()
    return config["commands"].get(command, True)

def is_feature_enabled(feature):
    """Check if a feature is enabled in config"""
    config = load_config()
    return config["features"].get(feature, True)

def get_setting(setting, default=None):
    """Get a setting value from config"""
    config = load_config()
    return config["settings"].get(setting, default)
