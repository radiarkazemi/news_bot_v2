"""
State management for persisting application state.
"""
import json
import logging
from pathlib import Path

try:
    from config.settings import STATE_FILE_PATH
except ImportError:
    STATE_FILE_PATH = "./data/state/news_detector_state.json"

logger = logging.getLogger(__name__)


class StateManager:
    """Manages application state persistence."""

    def __init__(self):
        """Initialize state manager."""
        self.state_file = Path(STATE_FILE_PATH)
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

    def save_state(self, state_data):
        """Save state data to file."""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            logger.debug("State saved successfully")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

    def load_state(self):
        """Load state data from file."""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return {}

    def get_state_value(self, key, default=None):
        """Get a specific value from state."""
        state = self.load_state()
        return state.get(key, default)

    def set_state_value(self, key, value):
        """Set a specific value in state."""
        state = self.load_state()
        state[key] = value
        self.save_state(state)
