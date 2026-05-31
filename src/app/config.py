"""Configuration manager for API Tree."""

import json
from pathlib import Path


class Config:
    """Configuration manager that reads from ~/.config/api-tree/config.json."""

    _instance = None
    _config = None

    def __new__(cls):
        """Singleton pattern to ensure only one config instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from ~/.config/api-tree/config.json."""
        self._config = {}
        config_path = Path.home() / ".config" / "api-tree" / "config.json"

        try:
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    self._config = json.load(f)
        except (json.JSONDecodeError, IOError):
            # If config file is invalid or unreadable, use empty config
            self._config = {}

    @property
    def output_dir(self) -> Path:
        """Get output directory from config or use default."""
        output_dir = self._config.get("output_dir")
        if output_dir:
            output_path = Path(output_dir).expanduser()
            try:
                output_path.mkdir(parents=True, exist_ok=True)
                return output_path
            except (OSError, PermissionError):
                pass
        # Default to Downloads directory
        default_dir = Path.home() / "Downloads"
        default_dir.mkdir(parents=True, exist_ok=True)
        return default_dir

    @property
    def default_url(self) -> str:
        """Get default URL from config or use default."""
        return self._config.get("default_url", "http://localhost:8080")

    def get(self, key: str, default=None):
        """Get a config value by key."""
        return self._config.get(key, default)


# Global config instance
config = Config()
