import sys
import os
import json
import requests
import threading
import time
from datetime import datetime
import uuid
import base64
import random
import urllib.parse
import logging
import argparse

CONFIG_FILE = 'config.json'
LOG_FILE = 'reactions_log.txt'

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("autoreaction.log"),
        logging.StreamHandler()
    ]
)
############### هنا لازم تعدل ###############

SERVER_ID = "1391031458474496151"  # ايدي السيرفر 
CHANNEL_IDS = ["1391031459099316236"]  # ايدي الشات 

############################################
class DiscordAuth:
    """Handles Discord authentication with proper headers"""
    def __init__(self, token):
        self.token = token
        self.fingerprint = self.generate_fingerprint()
        self.super_properties = self.get_super_properties()

    def generate_fingerprint(self):
        """Generate unique browser fingerprint"""
        return str(uuid.uuid4())

    def get_super_properties(self):
        """Create advanced properties to mimic a real browser"""
        properties = {
            "os": "Windows",
            "browser": "Chrome",
            "device": "",
            "browser_user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "browser_version": "121.0.0.0",
            "os_version": "10",
            "referrer": "",
            "referring_domain": "",
            "referrer_current": "",
            "referring_domain_current": "",
            "release_channel": "stable",
            "client_build_number": 223000,
            "client_event_source": None
        }
        json_str = json.dumps(properties, separators=(',', ':'))
        return base64.b64encode(json_str.encode()).decode()

    def get_headers(self):
        """Create HTTP headers to mimic a real browser"""
        return {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "X-Super-Properties": self.super_properties,
            "X-Fingerprint": self.fingerprint,
            "X-Discord-Locale": "en-US",
            "X-Debug-Options": "bugReporterEnabled",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Referer": "https://discord.com/channels/@me",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "TE": "trailers",
            "Origin": "https://discord.com",
            "DNT": "1"
        }

    def validate_token(self):
        """Validate token using Discord API"""
        headers = self.get_headers()
        try:
            response = requests.get("https://discord.com/api/v9/users/@me", headers=headers, timeout=30)
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 401:
                return {"error": "Invalid token"}
            elif response.status_code == 403:
                return {"error": "Token requires 2FA"}
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                logging.warning(f"Rate limited, retrying in {retry_after} seconds")
                time.sleep(retry_after)
                return self.validate_token()
            else:
                return {"error": f"HTTP error {response.status_code}"}
        except Exception as e:
            return {"error": f"Connection error: {str(e)}"}

class AutoReactionBot:
    def __init__(self, token, log_callback=None, scan_interval=15, reaction_delay=(1.5, 3.0)):
        self.token = token
        self.log_callback = log_callback
        self.reaction_count = 0
        self.last_reacted = {}
        self.running = True
        self.user_id = None
        self.headers = DiscordAuth(token).get_headers()
        self.scan_interval = scan_interval
        self.reaction_delay = reaction_delay

    def log_message(self, message, msg_type="INFO"):
        """Log message with callback"""
        if self.log_callback:
            self.log_callback(message, msg_type)
        else:
            logging.info(f"[{msg_type}] {message}")

    def save_to_log(self, message):
        """Save reaction to log file"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(LOG_FILE, 'a', encoding='utf-8') as f:
                f.write(f"[{timestamp}] {message}\n")
        except Exception as e:
            logging.error(f"Failed to save to log: {str(e)}")

    def get_channels(self):
        """Get text channels for the target server"""
        try:
            response = requests.get(
                f"https://discord.com/api/v9/guilds/{SERVER_ID}/channels",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                return [ch for ch in response.json() if ch['type'] == 0 and ch['id'] in CHANNEL_IDS]
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                self.log_message(f"Rate limited, retrying in {retry_after}s", "WARNING")
                time.sleep(retry_after)
                return self.get_channels()
            else:
                self.log_message(f"Failed to get channels: HTTP {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self.log_message(f"Error getting channels: {str(e)}", "ERROR")
            return []

    def get_messages(self, channel_id):
        """Get recent messages from a channel"""
        try:
            response = requests.get(
                f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=50",
                headers=self.headers,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                self.log_message(f"Rate limited, retrying in {retry_after}s", "WARNING")
                time.sleep(retry_after)
                return self.get_messages(channel_id)
            else:
                self.log_message(f"Failed to get messages: HTTP {response.status_code}", "ERROR")
                return []
        except Exception as e:
            self.log_message(f"Error getting messages: {str(e)}", "ERROR")
            return []

    def format_emoji(self, emoji):
        """Format emoji for reaction request"""
        if emoji.get('id'):
            return f"{emoji['name']}:{emoji['id']}"
        return emoji['name']

    def add_reaction(self, channel_id, message_id, emoji):
        """Add a reaction to a message"""
        try:
            formatted_emoji = urllib.parse.quote(self.format_emoji(emoji), safe='')

            response = requests.put(
                f"https://discord.com/api/v9/channels/{channel_id}/messages/{message_id}/reactions/{formatted_emoji}/@me",
                headers=self.headers,
                timeout=30
            )

            if response.status_code in [200, 204]:
                return True
            elif response.status_code == 429:
                retry_after = response.json().get('retry_after', 5)
                self.log_message(f"Rate limited, retrying in {retry_after}s", "WARNING")
                time.sleep(retry_after)
                return self.add_reaction(channel_id, message_id, emoji)
            else:
                self.log_message(f"Failed to add reaction: HTTP {response.status_code}", "ERROR")
                return False
        except Exception as e:
            self.log_message(f"Error adding reaction: {str(e)}", "ERROR")
            return False

    def process_channel(self, channel_id):
        """Process messages in a channel and add reactions"""
        messages = self.get_messages(channel_id)
        for message in messages:
            if not self.running:
                return

            message_id = message['id']
            author_id = message['author']['id']

            if author_id == self.user_id:
                continue

            if not message.get('reactions'):
                continue

            if self.last_reacted.get(message_id):
                continue

            for reaction in message['reactions']:
                if reaction.get('me'):
                    continue

                success = self.add_reaction(channel_id, message_id, reaction['emoji'])
                if success:
                    self.reaction_count += 1
                    self.last_reacted[message_id] = True

                    log_msg = (
                        f"Added {self.format_emoji(reaction['emoji'])} to message\n"
                        f"Author: {message['author']['username']}\n"
                        f"Content: {message['content'][:50]}{'...' if len(message['content']) > 50 else ''}"
                    )
                    self.log_message(log_msg, "SUCCESS")
                    self.save_to_log(log_msg)

                    delay = random.uniform(self.reaction_delay[0], self.reaction_delay[1])
                    time.sleep(delay)

    def start(self):
        """Start monitoring process"""
        auth = DiscordAuth(self.token)
        user_info = auth.validate_token()

        if not user_info or 'error' in user_info:
            error = user_info.get('error', 'Invalid token') if user_info else 'Invalid token'
            self.log_message(f"Login failed: {error}", "ERROR")
            return

        self.user_id = user_info.get('id')
        username = user_info.get('username', 'Unknown')
        self.log_message(f"Authenticated as {username}", "SUCCESS")
        
        while self.running:
            try:
                channels = self.get_channels()
                self.log_message(f"Monitoring {len(channels)} channels", "INFO")

                
                for channel in channels:
                    if not self.running:
                        break

                    self.process_channel(channel['id'])

                
                time.sleep(self.scan_interval)
            except Exception as e:
                self.log_message(f"Error in monitoring: {str(e)}", "ERROR")
                time.sleep(30)

    def stop(self):
        """Stop the bot"""
        self.running = False

class GiftwayAutoJoiner:
    def __init__(self, token, log_callback=None):
        self.token = token
        self.log_callback = log_callback
        self.joined_count = 0
        self.running = True
        self.custom_ids = {}
        self.headers = DiscordAuth(token).get_headers()

    def log_message(self, message, msg_type="INFO"):
        """Log message with callback"""
        if self.log_callback:
            self.log_callback(message, msg_type)
        else:
            logging.info(f"[{msg_type}] {message}")

    def get_messages(self, channel_id):
        """Get recent messages from a channel"""
        try:
            response = requests.get(
                f"https://discord.com/api/v9/channels/{channel_id}/messages?limit=50",
                headers=self.headers,
                timeout=30
            )
            return response.json() if response.status_code == 200 else []
        except Exception as e:
            self.log_message(f"Error getting messages: {str(e)}", "ERROR")
            return []

    def find_giftway_buttons(self, messages):
        """Find Giftway buttons in messages"""
        buttons = []
        for message in messages:
            if not message.get('components'):
                continue

            for component in message['components']:
                for btn in component.get('components', []):
                    if btn.get('custom_id') and 'gift' in btn.get('custom_id', '').lower():
                        buttons.append({
                            'channel_id': message['channel_id'],
                            'message_id': message['id'],
                            'custom_id': btn['custom_id']
                        })
        return buttons

    def click_button(self, channel_id, message_id, custom_id):
        """Click a Giftway button"""
        try:
            payload = {
                "type": 3,
                "nonce": str(int(time.time() * 1000)),
                "guild_id": None,
                "channel_id": channel_id,
                "message_id": message_id,
                "application_id": None,
                "session_id": str(uuid.uuid4()),
                "data": {
                    "component_type": 2,
                    "custom_id": custom_id
                }
            }

            response = requests.post(
                "https://discord.com/api/v9/interactions",
                json=payload,
                headers=self.headers,
                timeout=30
            )

            if response.status_code in [200, 204]:
                self.joined_count += 1
                return True
            return False
        except Exception as e:
            self.log_message(f"Error clicking button: {str(e)}", "ERROR")
            return False

    def process_channel(self, channel_id):
        """Process a channel for Giftway buttons"""
        messages = self.get_messages(channel_id)
        buttons = self.find_giftway_buttons(messages)

        for btn in buttons:
            if btn['custom_id'] in self.custom_ids:
                continue  

            success = self.click_button(
                btn['channel_id'],
                btn['message_id'],
                btn['custom_id']
            )

            if success:
                self.custom_ids[btn['custom_id']] = True
                self.log_message(f"Clicked Giftway button: {btn['custom_id']}", "SUCCESS")
                time.sleep(random.uniform(2, 5))  

    def start(self):
        """Start Giftway joining process"""
        auth = DiscordAuth(self.token)
        user_info = auth.validate_token()

        if not user_info or 'error' in user_info:
            error = user_info.get('error', 'Invalid token') if user_info else 'Invalid token'
            self.log_message(f"Login failed: {error}", "ERROR")
            return

        username = user_info.get('username', 'Unknown')
        self.log_message(f"Authenticated as {username}", "SUCCESS")
        self.log_message("Starting Giftway Auto Joiner...", "INFO")

        while self.running:
            try:
                channels = requests.get(
                    f"https://discord.com/api/v9/guilds/{SERVER_ID}/channels",
                    headers=self.headers,
                    timeout=30
                ).json()

                for channel in [c for c in channels if c['type'] == 0 and c['id'] in CHANNEL_IDS]:
                    if not self.running:
                        break

                    self.process_channel(channel['id'])

                time.sleep(60)

            except Exception as e:
                self.log_message(f"Error in main loop: {str(e)}", "ERROR")
                time.sleep(30)

    def stop(self):
        """Stop the bot"""
        self.running = False

def validate_token_format(token):
    """Validate token format without API call"""
    token = token.strip()
    if len(token) < 59 or len(token) > 100:
        return False

    if token.count('.') != 2:
        return False

    parts = token.split('.')
    if len(parts[0]) < 24 or not parts[0].isalnum():
        return False

    return True

def load_config():
    """Load config from file"""
    tokens = []
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)

            tokens = config.get('tokens', [])
            valid_tokens = []

            for token in tokens:
                if isinstance(token, str):
                    if validate_token_format(token):
                        valid_tokens.append(token)
                elif isinstance(token, dict):
                    if 'token' in token and validate_token_format(token['token']):
                        valid_tokens.append(token['token'])

            return valid_tokens
    except Exception as e:
        logging.error(f"Error loading config: {str(e)}")

    return tokens

def save_config(tokens):
    """Save config to file"""
    try:
        config = {
            'tokens': tokens
        }

        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=2)

        logging.info("Config saved successfully")
    except Exception as e:
        logging.error(f"Error saving config: {str(e)}")

def log_message(message, msg_type="INFO"):
    """Log message handler"""
    logging.info(f"[{msg_type}] {message}")

def main():
    """Main function to run the bots"""
    parser = argparse.ArgumentParser(description='Discord Auto Reaction Bot')
    parser.add_argument('--tokens', nargs='+', help='List of Discord tokens')
    args = parser.parse_args()

    if args.tokens:
        tokens = [token.strip() for token in args.tokens if validate_token_format(token.strip())]
        save_config(tokens)
    else:
        tokens = load_config()

    if not tokens:
        logging.error("No valid tokens provided. Exiting.")
        return

    logging.info(f"Starting with {len(tokens)} tokens")

    ############### هنا لازم تعدل ###############
    scan_interval = 5  # مدة البحث عن رياكشنات جديدة (بالثواني)
    reaction_delay = (1.5, 2.0)  # مدة الضغط على الرياكشن والتأخير بين كل رياكشن (بالثواني)
    ##########################################
    
    bots_ar = []
    for token in tokens:
        logging.info(f"Starting Auto Reaction bot for token: {token[:15]}...")
        bot = AutoReactionBot(
            token, 
            log_message,
            scan_interval=scan_interval,
            reaction_delay=reaction_delay
        )
        bots_ar.append(bot)
        threading.Thread(target=bot.start, daemon=True).start()

    # Start Giftway bots (اختياري)
    # bots_gw = []
    # for token in tokens:
    #     logging.info(f"Starting Giftway bot for token: {token[:15]}...")
    #     bot = GiftwayAutoJoiner(token, log_message)
    #     bots_gw.append(bot)
    #     threading.Thread(target=bot.start, daemon=True).start()

    # Keep the program running
    try:
        while True:
            time.sleep(3600) 
    except KeyboardInterrupt:
        logging.info("Stopping all bots...")
        for bot in bots_ar:
            bot.stop()
        # for bot in bots_gw:
        #     bot.stop()
        logging.info("All bots stopped.")
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "Project Auto Reaction is running!"

app.run(host='0.0.0.0', port=3000)


if __name__ == '__main__':
    main()
