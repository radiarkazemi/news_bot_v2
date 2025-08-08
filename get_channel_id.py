#!/usr/bin/env python3
"""
Script to get channel ID for @anilnewsonline
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from src.client.telegram_client import TelegramClientManager

async def get_channel_id():
    """Get the channel ID for @anilnewsonline"""
    
    print("🔍 Getting channel ID for @anilnewsonline...")
    
    # Create client
    client_manager = TelegramClientManager()
    
    try:
        # Start client
        if not await client_manager.start():
            print("❌ Failed to start Telegram client")
            return
        
        # Try different channel name formats
        possible_names = ["anilnewsonline", "@anilnewsonline", "anilnewsonline"]
        
        for channel_name in possible_names:
            try:
                print(f"🔍 Trying: {channel_name}")
                entity = await client_manager.client.get_entity(channel_name)
                
                if entity:
                    print(f"✅ Found channel!")
                    print(f"📺 Channel Name: {getattr(entity, 'title', 'Unknown')}")
                    print(f"📺 Channel Username: @{getattr(entity, 'username', 'No username')}")
                    print(f"🆔 Channel ID: {entity.id}")
                    print(f"🆔 Channel ID (negative): -{entity.id}")
                    
                    # The negative ID is what you need for bots
                    target_id = f"-100{entity.id}" if not str(entity.id).startswith('-') else entity.id
                    print(f"🎯 Use this in your .env: TARGET_CHANNEL_ID={target_id}")
                    break
                    
            except Exception as e:
                print(f"❌ Failed to find {channel_name}: {e}")
                continue
        else:
            print("❌ Could not find @anilnewsonline channel")
            print("💡 Make sure:")
            print("   1. The channel username is correct")
            print("   2. You have access to the channel")
            print("   3. The channel is public or you're a member")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        
    finally:
        await client_manager.stop()

if __name__ == "__main__":
    asyncio.run(get_channel_id())