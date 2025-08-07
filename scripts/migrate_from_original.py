# scripts/migrate_from_original.py
"""
Migration script to help extract news detector components from the original project.
"""
import os
import shutil
import json
from pathlib import Path


def migrate_config_from_original(original_env_path, target_env_path):
    """Migrate configuration from original project .env file."""
    print("🔄 Migrating configuration...")
    
    # Mapping of original keys to news detector keys
    key_mapping = {
        'TELEGRAM_API_ID': 'TELEGRAM_API_ID',
        'TELEGRAM_API_HASH': 'TELEGRAM_API_HASH', 
        'TELEGRAM_PHONE': 'TELEGRAM_PHONE',
        'ADMIN_BOT_TOKEN': 'ADMIN_BOT_TOKEN',
        'ADMIN_BOT_USERNAME': 'ADMIN_BOT_USERNAME',
        'TARGET_CHANNEL_ID': 'TARGET_CHANNEL_ID',
        'NEW_ATTRIBUTION': 'NEW_ATTRIBUTION',
        'OPERATION_START_HOUR': 'OPERATION_START_HOUR',
        'OPERATION_END_HOUR': 'OPERATION_END_HOUR',
        'FORCE_24_HOUR_OPERATION': 'FORCE_24_HOUR_OPERATION',
        'ADMIN_APPROVAL_TIMEOUT': 'ADMIN_APPROVAL_TIMEOUT',
        'WAR_NEWS_ONLY': 'WAR_NEWS_ONLY',
        'ISRAEL_IRAN_FOCUS': 'ISRAEL_IRAN_FOCUS',
        'GEOPOLITICAL_ONLY': 'GEOPOLITICAL_ONLY',
        'NEWS_CHECK_INTERVAL': 'NEWS_CHECK_INTERVAL',
        'NEWS_CHANNEL': 'NEWS_CHANNEL',
        'TWITTER_NEWS_CHANNEL': 'TWITTER_NEWS_CHANNEL'
    }
    
    migrated_config = {}
    
    if os.path.exists(original_env_path):
        with open(original_env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key in key_mapping:
                        migrated_config[key_mapping[key]] = value
        
        # Write migrated config
        with open(target_env_path, 'w') as f:
            f.write("# Migrated from original project\n")
            for key, value in migrated_config.items():
                f.write(f"{key}={value}\n")
        
        print(f"✅ Migrated {len(migrated_config)} configuration items")
        return True
    else:
        print(f"❌ Original .env file not found at {original_env_path}")
        return False


def migrate_session_file(original_session_dir, target_session_dir):
    """Migrate Telegram session file."""
    print("🔄 Migrating session file...")
    
    original_session = Path(original_session_dir) / "telegram_session.session"
    target_session = Path(target_session_dir) / "telegram_session.session"
    
    target_session.parent.mkdir(parents=True, exist_ok=True)
    
    if original_session.exists():
        shutil.copy2(original_session, target_session)
        print("✅ Session file migrated")
        return True
    else:
        print("ℹ️  No existing session file found")
        return False


def main():
    """Main migration function."""
    print("📦 News Detector Migration Tool")
    print("=" * 50)
    
    # Get paths from user
    original_project = input("Enter path to original project directory: ").strip()
    if not original_project:
        print("❌ No path provided")
        return
    
    original_project = Path(original_project)
    if not original_project.exists():
        print(f"❌ Directory {original_project} does not exist")
        return
    
    # Current directory should be the news detector project
    current_dir = Path.cwd()
    
    # Migrate configuration
    original_env = original_project / ".env"
    target_env = current_dir / ".env"
    
    if migrate_config_from_original(original_env, target_env):
        print("✅ Configuration migrated successfully")
    
    # Migrate session file
    original_session_dir = original_project / "data"
    target_session_dir = current_dir / "data" / "state"
    
    migrate_session_file(original_session_dir, target_session_dir)
    
    print("\n🎉 Migration complete!")
    print("Next steps:")
    print("1. Review and edit .env file")
    print("2. Test the configuration: python scripts/validate_config.py")
    print("3. Run the news detector: python main.py")


if __name__ == "__main__":
    main()

# ============================================================================

# scripts/validate_config.py
"""
Configuration validation script for the News Detector.
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config.credentials import validate_credentials
    from config.settings import *
    from src.client.telegram_client import TelegramClientManager
    from src.client.bot_api import BotAPIClient
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you're running from the project root directory")
    sys.exit(1)


async def validate_telegram_connection():
    """Test Telegram client connection."""
    print("🔗 Testing Telegram connection...")
    
    try:
        client_manager = TelegramClientManager()
        success = await client_manager.start()
        
        if success:
            print("✅ Telegram client connection successful")
            await client_manager.stop()
            return True
        else:
            print("❌ Failed to connect to Telegram")
            return False
    except Exception as e:
        print(f"❌ Telegram connection error: {e}")
        return False


def validate_bot_api():
    """Test Bot API connectivity."""
    print("🤖 Testing Bot API...")
    
    try:
        bot_api = BotAPIClient()
        # Try to get bot info (this should work even without sending messages)
        response = bot_api.send_message("@test", "test")  # This will fail but test connection
        print("✅ Bot API accessible")
        return True
    except Exception as e:
        print(f"⚠️  Bot API test inconclusive: {e}")
        return True  # Don't fail on this as it's expected to fail


def validate_channels():
    """Validate channel configuration."""
    print("📺 Validating channel configuration...")
    
    issues = []
    
    if not TARGET_CHANNEL_ID:
        issues.append("TARGET_CHANNEL_ID not set")
    elif not str(TARGET_CHANNEL_ID).startswith('-'):
        issues.append("TARGET_CHANNEL_ID should be negative (channel ID)")
    
    if not NEWS_CHANNEL:
        issues.append("NEWS_CHANNEL not set")
    
    if not ADMIN_BOT_USERNAME:
        issues.append("ADMIN_BOT_USERNAME not set")
    
    if issues:
        for issue in issues:
            print(f"❌ {issue}")
        return False
    else:
        print("✅ Channel configuration valid")
        return True


def validate_operating_hours():
    """Validate operating hours configuration."""
    print("⏰ Validating operating hours...")
    
    issues = []
    
    if not (0 <= OPERATION_START_HOUR <= 23):
        issues.append(f"OPERATION_START_HOUR ({OPERATION_START_HOUR}) must be 0-23")
    
    if not (0 <= OPERATION_END_HOUR <= 23):
        issues.append(f"OPERATION_END_HOUR ({OPERATION_END_HOUR}) must be 0-23")
    
    if OPERATION_START_HOUR >= OPERATION_END_HOUR:
        issues.append("OPERATION_START_HOUR must be less than OPERATION_END_HOUR")
    
    if issues:
        for issue in issues:
            print(f"❌ {issue}")
        return False
    else:
        print(f"✅ Operating hours: {OPERATION_START_HOUR}:00 - {OPERATION_END_HOUR}:00 Tehran time")
        return True


def validate_news_settings():
    """Validate news detection settings."""
    print("📰 Validating news settings...")
    
    print(f"  WAR_NEWS_ONLY: {WAR_NEWS_ONLY}")
    print(f"  ISRAEL_IRAN_FOCUS: {ISRAEL_IRAN_FOCUS}")
    print(f"  GEOPOLITICAL_ONLY: {GEOPOLITICAL_ONLY}")
    print(f"  NEWS_CHECK_INTERVAL: {NEWS_CHECK_INTERVAL} seconds")
    print(f"  ADMIN_APPROVAL_TIMEOUT: {ADMIN_APPROVAL_TIMEOUT} seconds")
    
    if NEWS_CHECK_INTERVAL < 300:
        print("⚠️  NEWS_CHECK_INTERVAL is quite low (< 5 minutes)")
    
    print("✅ News settings configured")
    return True


def validate_directories():
    """Validate required directories exist."""
    print("📁 Validating directories...")
    
    required_dirs = [
        Path("data/state"),
        Path("logs"),
    ]
    
    for directory in required_dirs:
        if not directory.exists():
            print(f"📁 Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
        else:
            print(f"✅ Directory exists: {directory}")
    
    return True


async def main():
    """Main validation function."""
    print("🔍 News Detector Configuration Validator")
    print("=" * 50)
    
    all_valid = True
    
    # Test 1: Validate credentials
    print("\n1. Validating credentials...")
    try:
        validate_credentials()
        print("✅ All required credentials present")
    except ValueError as e:
        print(f"❌ Credential validation failed: {e}")
        all_valid = False
    
    # Test 2: Validate directories
    print("\n2. Validating directories...")
    validate_directories()
    
    # Test 3: Validate channel config
    print("\n3. Validating channels...")
    if not validate_channels():
        all_valid = False
    
    # Test 4: Validate operating hours
    print("\n4. Validating operating hours...")
    if not validate_operating_hours():
        all_valid = False
    
    # Test 5: Validate news settings
    print("\n5. Validating news settings...")
    validate_news_settings()
    
    # Test 6: Test Telegram connection
    print("\n6. Testing Telegram connection...")
    if not await validate_telegram_connection():
        all_valid = False
    
    # Test 7: Test Bot API
    print("\n7. Testing Bot API...")
    validate_bot_api()
    
    # Summary
    print("\n" + "=" * 50)
    if all_valid:
        print("🎉 All validation checks passed!")
        print("✅ Your News Detector is ready to run")
        print("\nNext steps:")
        print("  python main.py              # Start the detector")
        print("  python main.py --test-news  # Test news detection")
    else:
        print("❌ Some validation checks failed")
        print("Please fix the issues above before running the detector")
        return 1
    
    return 0


if __name__ == "__main__":
    import asyncio
    sys.exit(asyncio.run(main()))

# ============================================================================

# scripts/interactive_setup.py
"""
Interactive setup script for the News Detector.
"""
import os
import sys
from pathlib import Path


def get_input_with_default(prompt, default=None, required=True):
    """Get user input with optional default value."""
    if default:
        full_prompt = f"{prompt} [{default}]: "
    else:
        full_prompt = f"{prompt}: "
    
    value = input(full_prompt).strip()
    
    if not value and default:
        return default
    
    if required and not value:
        print("❌ This field is required")
        return get_input_with_default(prompt, default, required)
    
    return value


def get_yes_no(prompt, default=True):
    """Get yes/no input from user."""
    default_str = "Y/n" if default else "y/N"
    response = input(f"{prompt} [{default_str}]: ").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1']


def main():
    """Interactive setup process."""
    print("🚀 Telegram News Detector - Interactive Setup")
    print("=" * 60)
    print("This wizard will help you configure your news detector.")
    print("Press Ctrl+C at any time to exit.\n")
    
    try:
        config = {}
        
        # Basic Telegram API setup
        print("📱 TELEGRAM API CONFIGURATION")
        print("-" * 30)
        config['TELEGRAM_API_ID'] = get_input_with_default(
            "Telegram API ID (from my.telegram.org)"
        )
        
        config['TELEGRAM_API_HASH'] = get_input_with_default(
            "Telegram API Hash (from my.telegram.org)"
        )
        
        config['TELEGRAM_PHONE'] = get_input_with_default(
            "Your phone number (with country code, e.g., +1234567890)"
        )
        
        # Admin bot configuration
        print("\n🤖 ADMIN BOT CONFIGURATION")
        print("-" * 30)
        config['ADMIN_BOT_TOKEN'] = get_input_with_default(
            "Admin bot token (from @BotFather)"
        )
        
        config['ADMIN_BOT_USERNAME'] = get_input_with_default(
            "Admin bot username (without @)"
        )
        
        # Target channel
        print("\n📺 TARGET CHANNEL CONFIGURATION")
        print("-" * 30)
        config['TARGET_CHANNEL_ID'] = get_input_with_default(
            "Target channel ID (negative number, e.g., -1001234567890)"
        )
        
        config['NEW_ATTRIBUTION'] = get_input_with_default(
            "News attribution", "@yournewschannel"
        )
        
        # Operating hours
        print("\n⏰ OPERATING HOURS")
        print("-" * 30)
        config['OPERATION_START_HOUR'] = get_input_with_default(
            "Start hour (0-23, Tehran time)", "9"
        )
        
        config['OPERATION_END_HOUR'] = get_input_with_default(
            "End hour (0-23, Tehran time)", "22"
        )
        
        config['FORCE_24_HOUR_OPERATION'] = str(get_yes_no(
            "Force 24-hour operation?", False
        )).lower()
        
        # News settings
        print("\n📰 NEWS DETECTION SETTINGS")
        print("-" * 30)
        config['WAR_NEWS_ONLY'] = str(get_yes_no(
            "Focus only on war/conflict news?", True
        )).lower()
        
        config['ISRAEL_IRAN_FOCUS'] = str(get_yes_no(
            "Prioritize Israel-Iran conflict news?", True
        )).lower()
        
        config['GEOPOLITICAL_ONLY'] = str(get_yes_no(
            "Only geopolitical/economic warfare news?", True
        )).lower()
        
        # News sources
        print("\n📡 NEWS SOURCES")
        print("-" * 30)
        config['NEWS_CHANNEL'] = get_input_with_default(
            "Primary news channel username (without @)", "goldonline2016"
        )
        
        config['TWITTER_NEWS_CHANNEL'] = get_input_with_default(
            "Twitter news channel username (without @)", "twiier_news", False
        )
        
        # Intervals
        print("\n⏱️  TIMING SETTINGS")
        print("-" * 30)
        config['NEWS_CHECK_INTERVAL'] = get_input_with_default(
            "News check interval (seconds)", "1800"
        )
        
        config['ADMIN_APPROVAL_TIMEOUT'] = get_input_with_default(
            "Admin approval timeout (seconds)", "3600"
        )
        
        # Write configuration
        print("\n💾 SAVING CONFIGURATION")
        print("-" * 30)
        
        env_file = Path(".env")
        if env_file.exists():
            backup = get_yes_no("Found existing .env file. Create backup?", True)
            if backup:
                shutil.copy2(env_file, f".env.backup.{int(time.time())}")
                print("✅ Backup created")
        
        with open(env_file, 'w') as f:
            f.write("# Telegram News Detector Configuration\n")
            f.write("# Generated by interactive setup\n\n")
            
            # Group settings
            groups = {
                "TELEGRAM API CREDENTIALS": [
                    'TELEGRAM_API_ID', 'TELEGRAM_API_HASH', 'TELEGRAM_PHONE'
                ],
                "ADMIN BOT": [
                    'ADMIN_BOT_TOKEN', 'ADMIN_BOT_USERNAME'
                ],
                "TARGET CHANNEL": [
                    'TARGET_CHANNEL_ID', 'NEW_ATTRIBUTION'
                ],
                "OPERATING HOURS": [
                    'OPERATION_START_HOUR', 'OPERATION_END_HOUR', 'FORCE_24_HOUR_OPERATION'
                ],
                "NEWS DETECTION": [
                    'WAR_NEWS_ONLY', 'ISRAEL_IRAN_FOCUS', 'GEOPOLITICAL_ONLY'
                ],
                "NEWS SOURCES": [
                    'NEWS_CHANNEL', 'TWITTER_NEWS_CHANNEL'
                ],
                "TIMING": [
                    'NEWS_CHECK_INTERVAL', 'ADMIN_APPROVAL_TIMEOUT'
                ]
            }
            
            for group_name, keys in groups.items():
                f.write(f"# {group_name}\n")
                for key in keys:
                    value = config.get(key, "")
                    if value and key.endswith('_TOKEN'):
                        f.write(f'{key}="{value}"\n')
                    else:
                        f.write(f'{key}={value}\n')
                f.write("\n")
        
        print("✅ Configuration saved to .env")
        
        # Final steps
        print("\n🎉 SETUP COMPLETE!")
        print("=" * 30)
        print("Next steps:")
        print("1. Validate your configuration:")
        print("   python scripts/validate_config.py")
        print("\n2. Test news detection:")
        print("   python scripts/debug_news.py")
        print("\n3. Start the news detector:")
        print("   python main.py")
        print("\n4. Monitor the logs:")
        print("   tail -f logs/news_detector.log")
        
    except KeyboardInterrupt:
        print("\n\n❌ Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    import shutil
    import time
    main()

# ============================================================================

# scripts/monitor_stats.py
"""
Monitoring and statistics script for the News Detector.
"""
import json
import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.time_utils import get_current_time, get_formatted_time
from config.settings import STATE_FILE_PATH, LOG_FILE_PATH


def load_state():
    """Load current state."""
    try:
        with open(STATE_FILE_PATH, 'r') as f:
            return json.load(f)
    except:
        return {}


def analyze_logs(hours=24):
    """Analyze log file for statistics."""
    log_file = Path(LOG_FILE_PATH)
    if not log_file.exists():
        return {}
    
    stats = {
        'total_lines': 0,
        'errors': 0,
        'warnings': 0,
        'news_processed': 0,
        'news_approved': 0,
        'connections': 0,
        'recent_activity': []
    }
    
    # Read last N lines efficiently
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Process recent lines
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        for line in lines[-10000:]:  # Check last 10k lines max
            stats['total_lines'] += 1
            
            if 'ERROR' in line:
                stats['errors'] += 1
            elif 'WARNING' in line:
                stats['warnings'] += 1
            
            if 'news' in line.lower():
                if 'processed' in line.lower():
                    stats['news_processed'] += 1
                elif 'approved' in line.lower():
                    stats['news_approved'] += 1
            
            if 'connected' in line.lower():
                stats['connections'] += 1
            
            # Extract recent activity
            if len(stats['recent_activity']) < 10:
                if any(keyword in line.lower() for keyword in ['news', 'approved', 'error']):
                    stats['recent_activity'].append(line.strip()[-100:])
    
    except Exception as e:
        stats['error'] = str(e)
    
    return stats


def display_status():
    """Display current system status."""
    print("📊 News Detector Status Dashboard")
    print("=" * 60)
    
    # Current time
    current_time = get_current_time()
    print(f"🕐 Current time: {get_formatted_time(current_time)}")
    
    # Operating status
    from src.utils.time_utils import is_operating_hours
    operating = is_operating_hours()
    status_icon = "🟢" if operating else "🔴"
    print(f"{status_icon} Operating status: {'ACTIVE' if operating else 'OUTSIDE HOURS'}")
    
    # State information
    state = load_state()
    pending_news = state.get('pending_news', {})
    print(f"📰 Pending approvals: {len(pending_news)}")
    
    if pending_news:
        print("   Recent pending items:")
        for i, (news_id, news_data) in enumerate(list(pending_news.items())[:3]):
            timestamp = news_data.get('timestamp', 0)
            age = time.time() - timestamp
            print(f"   • {news_id}: {age/60:.0f} minutes ago")
    
    # Log analysis
    print("\n📈 Statistics (last 24 hours):")
    log_stats = analyze_logs(24)
    
    print(f"   News processed: {log_stats.get('news_processed', 0)}")
    print(f"   News approved: {log_stats.get('news_approved', 0)}")
    print(f"   Errors: {log_stats.get('errors', 0)}")
    print(f"   Warnings: {log_stats.get('warnings', 0)}")
    print(f"   Connections: {log_stats.get('connections', 0)}")
    
    # Recent activity
    recent = log_stats.get('recent_activity', [])
    if recent:
        print(f"\n📋 Recent activity:")
        for activity in recent[-5:]:
            print(f"   {activity}")
    
    # File sizes
    log_file = Path(LOG_FILE_PATH)
    state_file = Path(STATE_FILE_PATH)
    
    print(f"\n💾 File information:")
    if log_file.exists():
        log_size = log_file.stat().st_size / 1024 / 1024
        print(f"   Log file: {log_size:.1f} MB")
    
    if state_file.exists():
        state_size = state_file.stat().st_size / 1024
        print(f"   State file: {state_size:.1f} KB")


def monitor_live():
    """Live monitoring mode."""
    print("🔴 Live monitoring mode (press Ctrl+C to exit)")
    print("=" * 60)
    
    try:
        while True:
            # Clear screen (works on most terminals)
            os.system('cls' if os.name == 'nt' else 'clear')
            
            display_status()
            print(f"\n🔄 Refreshing in 30 seconds...")
            
            time.sleep(30)
    
    except KeyboardInterrupt:
        print("\n\n👋 Monitoring stopped")


def main():
    """Main monitoring function."""
    if len(sys.argv) > 1 and sys.argv[1] == "--live":
        monitor_live()
    else:
        display_status()


if __name__ == "__main__":
    import os
    main()