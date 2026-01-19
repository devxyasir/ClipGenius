"""
ClipGenius - Configuration Manager
Handles loading and saving user settings
"""
import json
import os
from pathlib import Path
from .constants import OUTPUT_BASE_DIR, DEFAULT_MIN_CLIP_DURATION, DEFAULT_MAX_CLIP_DURATION


class ConfigManager:
    """Manages application configuration and user settings."""
    
    DEFAULT_CONFIG = {
        "chrome_profile_path": "",
        "chrome_user_data_dir": "",
        "min_clip_duration": DEFAULT_MIN_CLIP_DURATION,
        "max_clip_duration": DEFAULT_MAX_CLIP_DURATION,
        "enable_captions": False,
        "enable_background_music": False,
        "background_music_volume": 30,  # 0-100
        "enable_video_enhancement": True,
        "enable_audio_enhancement": True,
        "output_directory": OUTPUT_BASE_DIR,
        "last_project": "",
        "recent_projects": []
    }
    
    def __init__(self, config_path: str = None):
        """Initialize configuration manager.
        
        Args:
            config_path: Path to config file. Defaults to app directory.
        """
        if config_path is None:
            app_dir = Path(__file__).parent.parent
            config_path = app_dir / "config.json"
        
        self.config_path = Path(config_path)
        self.config = self.load_config()
    
    def load_config(self) -> dict:
        """Load configuration from file or create default."""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to handle new settings
                    return {**self.DEFAULT_CONFIG, **loaded_config}
            except (json.JSONDecodeError, IOError):
                return self.DEFAULT_CONFIG.copy()
        return self.DEFAULT_CONFIG.copy()
    
    def save_config(self) -> bool:
        """Save current configuration to file.
        
        Returns:
            True if successful, False otherwise.
        """
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
        except IOError:
            return False
    
    def get(self, key: str, default=None):
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Configuration value or default
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value) -> None:
        """Set a configuration value and save.
        
        Args:
            key: Configuration key
            value: Value to set
        """
        self.config[key] = value
        self.save_config()
    
    def get_chrome_options(self) -> tuple:
        """Get Chrome profile settings.
        
        Returns:
            Tuple of (user_data_dir, profile_directory)
        """
        profile_path = self.config.get("chrome_profile_path", "")
        if profile_path:
            # Extract user data dir and profile name from full path
            # e.g., C:\Users\Name\AppData\Local\Google\Chrome\User Data\Default
            path = Path(profile_path)
            if "User Data" in str(path):
                parts = str(path).split("User Data")
                user_data_dir = parts[0] + "User Data"
                profile_dir = path.name  # Usually "Default" or "Profile 1"
                return user_data_dir, profile_dir
        return "", ""
    
    def add_recent_project(self, project_path: str) -> None:
        """Add a project to recent projects list.
        
        Args:
            project_path: Path to the project folder
        """
        recent = self.config.get("recent_projects", [])
        if project_path in recent:
            recent.remove(project_path)
        recent.insert(0, project_path)
        self.config["recent_projects"] = recent[:10]  # Keep last 10
        self.save_config()
    
    def detect_chrome_profiles(self) -> list:
        """Detect available Chrome profiles on the system.
        
        Returns:
            List of profile paths found
        """
        profiles = []
        
        # Windows Chrome default location
        chrome_user_data = os.path.join(
            os.environ.get('LOCALAPPDATA', ''),
            'Google', 'Chrome', 'User Data'
        )
        
        if os.path.exists(chrome_user_data):
            for item in os.listdir(chrome_user_data):
                item_path = os.path.join(chrome_user_data, item)
                # Check if it's a valid profile directory
                if os.path.isdir(item_path):
                    if item == "Default" or item.startswith("Profile "):
                        profiles.append(item_path)
        
        return profiles


# Global config instance
config = ConfigManager()
