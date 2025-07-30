import asyncio
import time
import threading
from .config_handler import load_config
from .discord_bot import AutoReactionBot, GiftwayAutoJoiner

# حالة البوتات
bots_ar = []
bots_gw = []
running = False

def start_bots():
    """بدء تشغيل البوتات بناءً على التكوين"""
    global bots_ar, bots_gw, running
    
    if running:
        return
    
    config = load_config()
    if not config:
        return
    
    # إيقاف البوتات السابقة إن وجدت
    stop_bots()
    
    # بدء بوتات التفاعل التلقائي
    for token_data in config['tokens']:
        bot = AutoReactionBot(
            token_data['token'],
            guild_ids=token_data['guild_ids'],
            scan_interval=config['settings']['scan_interval'],
            reaction_delay=tuple(config['settings']['reaction_delay'])
        )
        bots_ar.append(bot)
        threading.Thread(target=bot.start).start()
    
    # بدء بوتات جيفت واي
    for token_data in config['tokens']:
        bot = GiftwayAutoJoiner(token_data['token'])
        bots_gw.append(bot)
        threading.Thread(target=bot.start).start()
    
    running = True

def stop_bots():
    """إيقاف جميع البوتات"""
    global bots_ar, bots_gw, running
    
    for bot in bots_ar:
        bot.stop()
    for bot in bots_gw:
        bot.stop()
    
    bots_ar = []
    bots_gw = []
    running = False
