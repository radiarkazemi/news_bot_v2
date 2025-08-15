#!/usr/bin/env python3
"""
Real-time monitoring dashboard for the Financial News Detector Bot.
Run this alongside your bot to monitor performance and rate limiting.

Usage:
    python monitoring_dashboard.py
    python monitoring_dashboard.py logs/custom_log.log
"""

import asyncio
import time
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict, deque
import re

class BotMonitor:
    """Real-time bot monitoring system."""
    
    def __init__(self, log_file_path="logs/news_detector.log"):
        self.log_file_path = Path(log_file_path)
        self.stats = {
            'messages_processed': 0,
            'news_detected': 0,
            'news_sent_for_approval': 0,
            'news_approved': 0,
            'news_published': 0,
            'errors': 0,
            'flood_waits': 0,
            'rate_limit_delays': 0
        }
        
        # Recent activity tracking
        self.recent_activity = deque(maxlen=100)
        self.error_log = deque(maxlen=50)
        
        # Rate limiting tracking
        self.flood_wait_times = []
        self.last_flood_wait = None
        
        # Channel statistics
        self.channel_stats = defaultdict(lambda: {
            'processed': 0,
            'relevant': 0,
            'sent_for_approval': 0
        })
        
        self.running = False
        self.last_position = 0
        self.start_time = datetime.now()
    
    def parse_log_line(self, line):
        """Parse a log line to extract useful information."""
        try:
            # Basic log format: timestamp - level - message
            parts = line.strip().split(' - ', 2)
            if len(parts) >= 3:
                timestamp_str = parts[0]
                level = parts[1]
                message = parts[2]
                
                # Try to parse timestamp
                try:
                    timestamp = datetime.strptime(timestamp_str, '%H:%M:%S')
                    # Assume today's date
                    timestamp = timestamp.replace(year=datetime.now().year, 
                                                month=datetime.now().month,
                                                day=datetime.now().day)
                except:
                    timestamp = datetime.now()
                
                return {
                    'timestamp': timestamp,
                    'level': level,
                    'message': message,
                    'raw': line
                }
        except:
            pass
        
        return None
    
    async def start_monitoring(self):
        """Start real-time log monitoring."""
        print("🚀 Financial News Bot Monitor")
        print("=" * 60)
        
        if not self.log_file_path.exists():
            print(f"❌ Log file not found: {self.log_file_path}")
            print("💡 Make sure your bot is running and logging to this file")
            return
        
        self.running = True
        
        # Get initial file position
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            f.seek(0, 2)  # Go to end
            self.last_position = f.tell()
        
        print(f"📊 Monitoring: {self.log_file_path}")
        print(f"🕐 Started: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "=" * 60)
        
        # Start monitoring tasks
        monitor_task = asyncio.create_task(self._monitor_logs())
        display_task = asyncio.create_task(self._display_dashboard())
        
        try:
            await asyncio.gather(monitor_task, display_task)
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped by user")
        finally:
            self.running = False
    
    async def _monitor_logs(self):
        """Monitor log file for new entries."""
        while self.running:
            try:
                # Check for new log entries
                with open(self.log_file_path, 'r', encoding='utf-8') as f:
                    f.seek(self.last_position)
                    new_lines = f.readlines()
                    self.last_position = f.tell()
                
                # Process new lines
                for line in new_lines:
                    self._process_log_line(line)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                print(f"❌ Error monitoring logs: {e}")
                await asyncio.sleep(5)
    
    def _process_log_line(self, line):
        """Process a single log line and update statistics."""
        parsed = self.parse_log_line(line)
        if not parsed:
            return
        
        message = parsed['message'].lower()
        level = parsed['level']
        
        # Update statistics based on message content
        if 'messages processed' in message or 'analyzing message' in message:
            self.stats['messages_processed'] += 1
        
        elif 'financial news detected' in message or 'news detected' in message:
            self.stats['news_detected'] += 1
        
        elif 'sent for approval' in message or 'queued' in message:
            self.stats['news_sent_for_approval'] += 1
        
        elif 'approval command' in message or 'published successfully' in message:
            self.stats['news_approved'] += 1
        
        elif 'published to channel' in message or 'message sent to' in message:
            self.stats['news_published'] += 1
        
        elif 'error' in message or level == 'ERROR':
            self.stats['errors'] += 1
            self.error_log.append({
                'timestamp': parsed['timestamp'],
                'message': parsed['message'][:100]
            })
        
        elif 'wait' in message and ('seconds' in message or 'required' in message):
            self.stats['flood_waits'] += 1
            self.last_flood_wait = parsed['timestamp']
            
            # Extract wait time if possible
            wait_match = re.search(r'(\d+)\s+seconds?', message)
            if wait_match:
                wait_time = int(wait_match.group(1))
                self.flood_wait_times.append({
                    'timestamp': parsed['timestamp'],
                    'wait_time': wait_time
                })
        
        elif 'rate limiting' in message or 'waiting' in message:
            self.stats['rate_limit_delays'] += 1
        
        # Track channel processing
        if 'processing financial news from' in message:
            channel_match = re.search(r'from (\w+)', message)
            if channel_match:
                channel = channel_match.group(1)
                self.channel_stats[channel]['processed'] += 1
        
        # Add to recent activity
        if level in ['INFO', 'WARNING', 'ERROR']:
            self.recent_activity.append({
                'timestamp': parsed['timestamp'],
                'level': level,
                'message': parsed['message'][:80] + ('...' if len(parsed['message']) > 80 else '')
            })
    
    async def _display_dashboard(self):
        """Display real-time dashboard."""
        while self.running:
            try:
                # Clear screen
                os.system('cls' if os.name == 'nt' else 'clear')
                self._print_dashboard()
                await asyncio.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"❌ Error displaying dashboard: {e}")
                await asyncio.sleep(5)
    
    def _print_dashboard(self):
        """Print the monitoring dashboard."""
        now = datetime.now()
        uptime = now - self.start_time
        
        print("📈 FINANCIAL NEWS BOT - LIVE MONITOR")
        print("=" * 70)
        print(f"🕐 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"⏱️  Monitor Uptime: {str(uptime).split('.')[0]}")
        print(f"📊 Log File: {self.log_file_path.name}")
        
        # Main statistics
        print("\n📊 STATISTICS")
        print("-" * 40)
        print(f"📝 Messages Processed: {self.stats['messages_processed']}")
        print(f"📰 Financial News Detected: {self.stats['news_detected']}")
        print(f"📤 Sent for Approval: {self.stats['news_sent_for_approval']}")
        print(f"✅ Approved: {self.stats['news_approved']}")
        print(f"📢 Published: {self.stats['news_published']}")
        print(f"❌ Errors: {self.stats['errors']}")
        
        # Rate limiting info
        print("\n⏳ RATE LIMITING")
        print("-" * 40)
        print(f"🚫 Flood Waits: {self.stats['flood_waits']}")
        print(f"⏸️  Rate Limit Delays: {self.stats['rate_limit_delays']}")
        
        if self.last_flood_wait:
            time_since = now - self.last_flood_wait
            print(f"⏰ Last Flood Wait: {time_since.total_seconds():.0f}s ago")
        
        # Recent flood wait times
        if self.flood_wait_times:
            recent_waits = [fw['wait_time'] for fw in self.flood_wait_times[-5:]]
            avg_wait = sum(recent_waits) / len(recent_waits)
            max_wait = max(recent_waits)
            print(f"📊 Avg Wait Time: {avg_wait:.0f}s (Max: {max_wait}s)")
        
        # Channel statistics
        if self.channel_stats:
            print("\n📺 CHANNEL STATISTICS")
            print("-" * 40)
            for channel, stats in self.channel_stats.items():
                print(f"📡 {channel}: {stats['processed']} processed")
        
        # Performance indicators
        print(f"\n🎯 PERFORMANCE INDICATORS")
        print("-" * 40)
        
        if self.stats['messages_processed'] > 0:
            detection_rate = (self.stats['news_detected'] / self.stats['messages_processed']) * 100
            print(f"🔍 Detection Rate: {detection_rate:.1f}%")
        
        if self.stats['news_detected'] > 0:
            approval_rate = (self.stats['news_sent_for_approval'] / self.stats['news_detected']) * 100
            print(f"📤 Approval Rate: {approval_rate:.1f}%")
        
        if self.stats['news_sent_for_approval'] > 0:
            publish_rate = (self.stats['news_published'] / self.stats['news_sent_for_approval']) * 100
            print(f"📢 Publish Rate: {publish_rate:.1f}%")
        
        # Health indicators
        print(f"\n🏥 HEALTH STATUS")
        print("-" * 40)
        
        # Check for recent errors
        recent_errors = [e for e in self.error_log if (now - e['timestamp']).total_seconds() < 300]
        if len(recent_errors) == 0:
            print("✅ No recent errors (5 min)")
        elif len(recent_errors) < 3:
            print(f"⚠️ {len(recent_errors)} errors in last 5 min")
        else:
            print(f"❌ {len(recent_errors)} errors in last 5 min - Check logs!")
        
        # Check for recent flood waits
        recent_floods = [fw for fw in self.flood_wait_times if (now - fw['timestamp']).total_seconds() < 600]
        if len(recent_floods) == 0:
            print("✅ No flood waits (10 min)")
        else:
            total_wait = sum(fw['wait_time'] for fw in recent_floods)
            print(f"⏳ {len(recent_floods)} flood waits ({total_wait}s total)")
        
        # Recent activity
        print("\n🔄 RECENT ACTIVITY")
        print("-" * 40)
        for activity in list(self.recent_activity)[-8:]:
            timestamp = activity['timestamp'].strftime('%H:%M:%S')
            level_icon = {'INFO': '📘', 'WARNING': '⚠️', 'ERROR': '❌'}.get(activity['level'], '📄')
            print(f"{timestamp} {level_icon} {activity['message']}")
        
        # Recent errors
        if self.error_log:
            print("\n❌ RECENT ERRORS")
            print("-" * 40)
            for error in list(self.error_log)[-3:]:
                timestamp = error['timestamp'].strftime('%H:%M:%S')
                print(f"{timestamp} {error['message']}")
        
        print("\n" + "=" * 70)
        print("🔄 Press Ctrl+C to stop monitoring")

class SimpleMonitor:
    """Simplified monitor for basic log watching."""
    
    def __init__(self, log_file_path):
        self.log_file_path = Path(log_file_path)
        self.last_position = 0
    
    def start_simple_monitoring(self):
        """Start simple file monitoring."""
        print(f"📊 Simple Monitor - Watching: {self.log_file_path}")
        print("=" * 60)
        
        if not self.log_file_path.exists():
            print(f"❌ Log file not found: {self.log_file_path}")
            return
        
        # Get initial position
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            f.seek(0, 2)
            self.last_position = f.tell()
        
        try:
            while True:
                self._check_new_lines()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped")
    
    def _check_new_lines(self):
        """Check for new log lines."""
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                f.seek(self.last_position)
                new_lines = f.readlines()
                self.last_position = f.tell()
            
            for line in new_lines:
                # Only show important lines
                if any(keyword in line.lower() for keyword in 
                      ['error', 'flood', 'approval', 'published', 'rate limit', 'warning']):
                    timestamp = datetime.now().strftime('%H:%M:%S')
                    print(f"[{timestamp}] {line.strip()}")
        except Exception as e:
            print(f"Error: {e}")

async def main():
    """Main monitoring function."""
    # Check for custom log file path
    log_file = "logs/news_detector.log"
    simple_mode = False
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--simple":
            simple_mode = True
            if len(sys.argv) > 2:
                log_file = sys.argv[2]
        else:
            log_file = sys.argv[1]
    
    # Check if log file exists
    if not Path(log_file).exists():
        print(f"❌ Log file not found: {log_file}")
        print("\n💡 Available options:")
        print("   python monitoring_dashboard.py")
        print("   python monitoring_dashboard.py logs/custom.log")
        print("   python monitoring_dashboard.py --simple")
        return
    
    if simple_mode:
        # Simple mode - just show important lines
        monitor = SimpleMonitor(log_file)
        monitor.start_simple_monitoring()
    else:
        # Full dashboard mode
        monitor = BotMonitor(log_file)
        await monitor.start_monitoring()

def print_help():
    """Print help information."""
    print("📊 Financial News Bot Monitor")
    print("=" * 40)
    print("Usage:")
    print("  python monitoring_dashboard.py                    # Monitor default log")
    print("  python monitoring_dashboard.py logs/custom.log    # Monitor custom log")
    print("  python monitoring_dashboard.py --simple           # Simple mode")
    print("  python monitoring_dashboard.py --help             # Show this help")
    print("\nFeatures:")
    print("  ✅ Real-time statistics")
    print("  ✅ Rate limiting monitoring")
    print("  ✅ Channel processing stats")
    print("  ✅ Error tracking")
    print("  ✅ Performance indicators")

if __name__ == "__main__":
    # Check for help
    if len(sys.argv) > 1 and sys.argv[1] in ['--help', '-h', 'help']:
        print_help()
        sys.exit(0)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Monitor stopped")
    except Exception as e:
        print(f"\n❌ Monitor error: {e}")