"""
Enhanced state management for persisting application state.
"""
import json
import logging
import time
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from config.settings import STATE_FILE_PATH
except ImportError:
    STATE_FILE_PATH = "./data/state/news_detector_state.json"


class StateManager:
    """Enhanced state manager with backup and recovery capabilities."""

    def __init__(self):
        """Initialize state manager."""
        self.state_file = Path(STATE_FILE_PATH)
        self.backup_file = Path(str(self.state_file) + ".backup")
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Cache for frequently accessed state
        self._state_cache = {}
        self._cache_timestamp = 0
        self._cache_duration = 30  # Cache for 30 seconds

    def save_state(self, state_data):
        """Save state data to file with backup."""
        try:
            # Add metadata
            enhanced_state = {
                'data': state_data,
                'metadata': {
                    'last_updated': time.time(),
                    'version': '1.0',
                    'timestamp_iso': datetime.now().isoformat()
                }
            }
            
            # Create backup of existing state
            if self.state_file.exists():
                try:
                    self.state_file.rename(self.backup_file)
                except OSError as e:
                    logger.warning(f"Could not create backup: {e}")
            
            # Save new state
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(enhanced_state, f, ensure_ascii=False, indent=2)
            
            # Update cache
            self._state_cache = state_data
            self._cache_timestamp = time.time()
            
            logger.debug(f"💾 State saved successfully ({len(json.dumps(state_data))} bytes)")
            
        except Exception as e:
            logger.error(f"Error saving state: {e}")
            # Try to restore backup if save failed
            if self.backup_file.exists() and not self.state_file.exists():
                try:
                    self.backup_file.rename(self.state_file)
                    logger.info("Restored state from backup after save failure")
                except Exception as restore_error:
                    logger.error(f"Could not restore backup: {restore_error}")

    def load_state(self):
        """Load state data from file with caching and recovery."""
        try:
            # Check cache first
            if (self._state_cache and 
                time.time() - self._cache_timestamp < self._cache_duration):
                logger.debug("Returning cached state")
                return self._state_cache
            
            # Load from file
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                
                # Handle both old format (direct data) and new format (with metadata)
                if isinstance(loaded_data, dict) and 'data' in loaded_data:
                    # New format with metadata
                    state_data = loaded_data['data']
                    metadata = loaded_data.get('metadata', {})
                    logger.debug(f"Loaded state with metadata: {metadata}")
                else:
                    # Old format - direct data
                    state_data = loaded_data
                
                # Update cache
                self._state_cache = state_data
                self._cache_timestamp = time.time()
                
                logger.debug(f"📂 State loaded successfully ({len(json.dumps(state_data))} bytes)")
                return state_data
            
            # Try backup if main file doesn't exist
            elif self.backup_file.exists():
                logger.warning("Main state file missing, trying backup")
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    backup_data = json.load(f)
                
                # Restore main file from backup
                self.save_state(backup_data)
                logger.info("✅ Restored state from backup")
                return backup_data
            
            # No state file found
            logger.info("No existing state file found, starting with empty state")
            return {}
            
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            
            # Try to recover from backup
            if self.backup_file.exists():
                try:
                    logger.info("Attempting recovery from backup...")
                    with open(self.backup_file, 'r', encoding='utf-8') as f:
                        backup_data = json.load(f)
                    logger.info("✅ Recovered state from backup")
                    return backup_data
                except Exception as backup_error:
                    logger.error(f"Backup recovery failed: {backup_error}")
            
            # Return empty state as last resort
            logger.warning("Returning empty state due to errors")
            return {}

    def get_state_value(self, key, default=None):
        """Get a specific value from state."""
        try:
            state = self.load_state()
            return state.get(key, default)
        except Exception as e:
            logger.error(f"Error getting state value '{key}': {e}")
            return default

    def set_state_value(self, key, value):
        """Set a specific value in state."""
        try:
            state = self.load_state()
            state[key] = value
            self.save_state(state)
            logger.debug(f"Set state value: {key} = {value}")
        except Exception as e:
            logger.error(f"Error setting state value '{key}': {e}")

    def delete_state_value(self, key):
        """Delete a specific value from state."""
        try:
            state = self.load_state()
            if key in state:
                del state[key]
                self.save_state(state)
                logger.debug(f"Deleted state value: {key}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting state value '{key}': {e}")
            return False

    def get_state_keys(self):
        """Get all keys in the current state."""
        try:
            state = self.load_state()
            return list(state.keys())
        except Exception as e:
            logger.error(f"Error getting state keys: {e}")
            return []

    def clear_state(self):
        """Clear all state data."""
        try:
            self.save_state({})
            logger.info("🗑️  State cleared")
            return True
        except Exception as e:
            logger.error(f"Error clearing state: {e}")
            return False

    def export_state(self, export_path):
        """Export state to a different file."""
        try:
            state = self.load_state()
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📤 State exported to {export_path}")
            return True
        except Exception as e:
            logger.error(f"Error exporting state: {e}")
            return False

    def import_state(self, import_path):
        """Import state from a file."""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.error(f"Import file does not exist: {import_path}")
                return False
            
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_state = json.load(f)
            
            self.save_state(imported_state)
            logger.info(f"📥 State imported from {import_path}")
            return True
        except Exception as e:
            logger.error(f"Error importing state: {e}")
            return False

    def get_state_size(self):
        """Get the size of the state file in bytes."""
        try:
            if self.state_file.exists():
                return self.state_file.stat().st_size
            return 0
        except Exception as e:
            logger.error(f"Error getting state size: {e}")
            return 0

    def get_state_info(self):
        """Get information about the state file."""
        try:
            info = {
                'exists': self.state_file.exists(),
                'size_bytes': 0,
                'last_modified': None,
                'backup_exists': self.backup_file.exists(),
                'cache_age': time.time() - self._cache_timestamp if self._cache_timestamp else None
            }
            
            if self.state_file.exists():
                stat = self.state_file.stat()
                info['size_bytes'] = stat.st_size
                info['last_modified'] = datetime.fromtimestamp(stat.st_mtime).isoformat()
            
            return info
        except Exception as e:
            logger.error(f"Error getting state info: {e}")
            return {'error': str(e)}

    def cleanup_old_backups(self, keep_count=5):
        """Clean up old backup files, keeping only the most recent ones."""
        try:
            backup_pattern = f"{self.state_file.name}.backup*"
            backup_dir = self.state_file.parent
            backup_files = list(backup_dir.glob(backup_pattern))
            
            if len(backup_files) > keep_count:
                # Sort by modification time (newest first)
                backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                # Remove old backups
                for old_backup in backup_files[keep_count:]:
                    old_backup.unlink()
                    logger.debug(f"🗑️  Removed old backup: {old_backup.name}")
                
                logger.info(f"🧹 Cleaned up {len(backup_files) - keep_count} old backup files")
                
        except Exception as e:
            logger.error(f"Error cleaning up backups: {e}")

    def invalidate_cache(self):
        """Invalidate the state cache to force reload on next access."""
        self._state_cache = {}
        self._cache_timestamp = 0
        logger.debug("State cache invalidated")