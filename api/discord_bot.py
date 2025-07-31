import requests
import time
import random
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AutoReactionBot:
    def __init__(self, token, guild_ids=None, scan_interval=15, reaction_delay=(1.5, 3.0)):
        self.token = token
        self.guild_ids = guild_ids or []
        self.scan_interval = scan_interval
        self.reaction_delay = reaction_delay
        self.running = True
        self.headers = self.get_headers()
    
    def get_headers(self):
        return {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
    
    def start(self):
        logger.info(f"Starting AutoReactionBot for token: {self.token[:10]}...")
        while self.running:
            try:
                self.process_cycle()
                time.sleep(self.scan_interval)
            except Exception as e:
                logger.error(f"Error in AutoReactionBot: {str(e)}")
                time.sleep(30)
    
    def process_cycle(self):
        # هنا يأتي كود معالجة الرسائل
        # تم اختصاره للتوضيح
        logger.info(f"Processing cycle for token: {self.token[:10]}...")
        time.sleep(5)  # محاكاة العمل
    
    def stop(self):
        self.running = False
        logger.info(f"Stopped AutoReactionBot for token: {self.token[:10]}")

class GiftwayAutoJoiner:
    def __init__(self, token):
        self.token = token
        self.running = True
        self.headers = self.get_headers()
    
    def get_headers(self):
        return {
            "Authorization": self.token,
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        }
    
    def start(self):
        logger.info(f"Starting GiftwayAutoJoiner for token: {self.token[:10]}...")
        while self.running:
            try:
                self.process_cycle()
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error in GiftwayAutoJoiner: {str(e)}")
                time.sleep(30)
    
    def process_cycle(self):
        # هنا يأتي كود معالجة جيفت واي
        # تم اختصاره للتوضيح
        logger.info(f"Processing giftway cycle for token: {self.token[:10]}...")
        time.sleep(5)  # محاكاة العمل
    
    def stop(self):
        self.running = False
        logger.info(f"Stopped GiftwayAutoJoiner for token: {self.token[:10]}")
