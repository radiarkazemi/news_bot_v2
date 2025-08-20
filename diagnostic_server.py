#!/usr/bin/env python3
"""
Server Diagnostic Script for Message Deletion Issues
Run this on your server to diagnose what's wrong.
"""
import asyncio
import sys
import os
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

async def diagnose_server_issues():
    """Comprehensive server diagnostics."""
    print("🔍 SERVER DIAGNOSTICS for Message Deletion")
    print("=" * 60)
    
    # Test 1: Check file permissions and paths
    print("📁 1. CHECKING FILE SYSTEM")
    print("-" * 30)
    
    # Check data directory
    data_dir = Path("data/state")
    print(f"Data directory: {data_dir.absolute()}")
    print(f"Exists: {'✅' if data_dir.exists() else '❌'}")
    
    if not data_dir.exists():
        print("🔧 Creating data directory...")
        data_dir.mkdir(parents=True, exist_ok=True)
    
    # Check state file
    state_file = data_dir / "news_handler_state.json"
    print(f"State file: {state_file.absolute()}")
    print(f"Exists: {'✅' if state_file.exists() else '❌'}")
    
    if state_file.exists():
        try:
            with open(state_file, 'r') as f:
                data = json.load(f)
            pending_count = len(data.get('pending_news', {}))
            print(f"Pending news in file: {pending_count}")
            
            # Show first few pending IDs
            if pending_count > 0:
                pending_ids = list(data.get('pending_news', {}).keys())[:5]
                print(f"Sample pending IDs: {pending_ids}")
        except Exception as e:
            print(f"❌ Error reading state file: {e}")
    
    # Check permissions
    print(f"Directory writable: {'✅' if os.access(data_dir, os.W_OK) else '❌'}")
    
    # Test 2: Test imports
    print(f"\n🐍 2. TESTING IMPORTS")
    print("-" * 30)
    
    try:
        from src.client.telegram_client import TelegramClientManager
        print("✅ TelegramClientManager imported")
    except Exception as e:
        print(f"❌ TelegramClientManager import failed: {e}")
        return False
    
    try:
        from src.handlers.news_handler import NewsHandler
        print("✅ NewsHandler imported")
    except Exception as e:
        print(f"❌ NewsHandler import failed: {e}")
        return False
    
    try:
        from config.credentials import validate_credentials, ADMIN_BOT_USERNAME
        print("✅ Credentials imported")
        print(f"Admin bot username: {ADMIN_BOT_USERNAME}")
    except Exception as e:
        print(f"❌ Credentials import failed: {e}")
        return False
    
    # Test 3: Test Telegram connection
    print(f"\n📱 3. TESTING TELEGRAM CONNECTION")
    print("-" * 30)
    
    try:
        client_manager = TelegramClientManager()
        
        if await client_manager.start():
            print("✅ Telegram client connected")
            
            # Test getting admin bot
            news_handler = NewsHandler(client_manager)
            admin_bot = await news_handler.get_admin_bot_entity()
            
            if admin_bot:
                print(f"✅ Admin bot found: {admin_bot.username if hasattr(admin_bot, 'username') else admin_bot.id}")
                
                # Test reading messages
                message_count = 0
                async for message in client_manager.client.iter_messages(admin_bot, limit=3):
                    message_count += 1
                
                print(f"✅ Can read {message_count} messages from admin bot")
                
                # Test sending a message
                try:
                    test_msg = await client_manager.client.send_message(
                        admin_bot,
                        "🧪 SERVER DIAGNOSTIC TEST - Will be deleted in 3 seconds"
                    )
                    print(f"✅ Test message sent: ID {test_msg.id}")
                    
                    await asyncio.sleep(3)
                    await test_msg.delete()
                    print(f"✅ Test message deleted successfully")
                    
                except Exception as send_error:
                    print(f"❌ Cannot send/delete messages: {send_error}")
                    
            else:
                print(f"❌ Admin bot not found with username: {ADMIN_BOT_USERNAME}")
            
            await client_manager.stop()
            
        else:
            print("❌ Failed to connect to Telegram")
            return False
            
    except Exception as e:
        print(f"❌ Telegram connection test failed: {e}")
        return False
    
    # Test 4: Test state loading/saving
    print(f"\n💾 4. TESTING STATE PERSISTENCE")
    print("-" * 30)
    
    try:
        # Create test data
        test_data = {
            'pending_news': {
                'test123': {
                    'text': 'Test news',
                    'timestamp': 1234567890
                }
            },
            'processed_messages': ['test1', 'test2'],
            'admin_messages': {
                'test123': {
                    'chat_id': 123456,
                    'message_id': 789,
                    'timestamp': 1234567890
                }
            }
        }
        
        # Test writing
        with open(state_file, 'w') as f:
            json.dump(test_data, f, indent=2)
        print("✅ Test data written to state file")
        
        # Test reading
        with open(state_file, 'r') as f:
            loaded_data = json.load(f)
        
        if loaded_data == test_data:
            print("✅ Test data read correctly")
        else:
            print("❌ Test data mismatch")
            
        # Clean up
        state_file.unlink()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ State persistence test failed: {e}")
    
    # Test 5: Environment check
    print(f"\n🌍 5. ENVIRONMENT CHECK")
    print("-" * 30)
    
    print(f"Python version: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    print(f"User: {os.getenv('USER', 'unknown')}")
    print(f"HOME: {os.getenv('HOME', 'unknown')}")
    
    # Check telethon session files
    session_files = list(Path(".").glob("*.session*"))
    print(f"Session files found: {len(session_files)}")
    for session_file in session_files:
        print(f"  - {session_file}")
    
    print("\n" + "=" * 60)
    print("🎯 DIAGNOSIS COMPLETE")
    print("=" * 60)
    
    return True

async def test_deletion_functionality():
    """Test the deletion functionality specifically."""
    print("\n🗑️ TESTING DELETION FUNCTIONALITY")
    print("=" * 40)
    
    try:
        from src.client.telegram_client import TelegramClientManager
        from src.handlers.news_handler import NewsHandler
        
        client_manager = TelegramClientManager()
        
        if await client_manager.start():
            news_handler = NewsHandler(client_manager)
            
            # Test admin bot connection
            print("🧪 Testing admin bot connection...")
            result = await news_handler.test_admin_bot_connection()
            
            if result:
                print("✅ Admin bot connection test passed")
            else:
                print("❌ Admin bot connection test failed")
            
            await client_manager.stop()
        else:
            print("❌ Could not start Telegram client")
            
    except Exception as e:
        print(f"❌ Deletion test failed: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Main diagnostic function."""
    success = await diagnose_server_issues()
    
    if success:
        await test_deletion_functionality()
    
    print("\n🔧 RECOMMENDATIONS:")
    print("-" * 20)
    print("1. If file system tests failed: Check directory permissions")
    print("2. If Telegram tests failed: Check credentials and network")
    print("3. If state tests failed: Check disk space and permissions")
    print("4. If deletion tests failed: Check bot permissions in admin chat")

if __name__ == "__main__":
    asyncio.run(main())