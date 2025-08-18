#!/usr/bin/env python3
"""
Quick cleanup script for admin bot messages
"""
import asyncio
from telethon import TelegramClient
from config.credentials import API_ID, API_HASH, PHONE_NUMBER, ADMIN_BOT_USERNAME

async def cleanup():
    client = TelegramClient('cleanup_session', API_ID, API_HASH)
    await client.start(phone=PHONE_NUMBER)
    
    admin_bot = await client.get_entity(f"@{ADMIN_BOT_USERNAME}")
    
    deleted = 0
    async for message in client.iter_messages(admin_bot, limit=1000):
        if message.text and ("FINANCIAL NEWS PENDING APPROVAL" in message.text or
                           message.text.startswith('/submit') or
                           message.text.startswith('/reject')):
            try:
                await message.delete()
                deleted += 1
                if deleted % 10 == 0:
                    print(f"Deleted {deleted} messages...")
            except:
                pass
    
    print(f"✅ Deleted {deleted} messages")
    await client.disconnect()

asyncio.run(cleanup())