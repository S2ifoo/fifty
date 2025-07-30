import json
import os
import logging

logger = logging.getLogger(__name__)
CONFIG_PATH = os.path.join(os.path.dirname(__file__), 'config.json')

def load_config():
    """تحميل ملف التكوين"""
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error("Config file not found. Creating default config.")
        return create_default_config()
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing config file: {e}")
        return None

def save_config(config):
    """حفظ ملف التكوين"""
    try:
        with open(CONFIG_PATH, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving config: {e}")
        return False

def create_default_config():
    """إنشاء تكوين افتراضي"""
    default_config = {
        "tokens": [],
        "settings": {
            "scan_interval": 15,
            "reaction_delay": [1.5, 3.0],
            "auto_start": True
        }
    }
    save_config(default_config)
    return default_config

def add_token(token, guild_ids):
    """إضافة توكن جديد إلى التكوين"""
    config = load_config()
    if not config:
        return False
    
    # تجنب تكرار التوكنات
    if any(t['token'] == token for t in config['tokens']):
        return False
    
    config['tokens'].append({
        "token": token,
        "guild_ids": guild_ids
    })
    return save_config(config)

def remove_token(token):
    """إزالة توكن من التكوين"""
    config = load_config()
    if not config:
        return False
    
    config['tokens'] = [t for t in config['tokens'] if t['token'] != token]
    return save_config(config)

def update_settings(new_settings):
    """تحديث الإعدادات"""
    config = load_config()
    if not config:
        return False
    
    config['settings'].update(new_settings)
    return save_config(config)
