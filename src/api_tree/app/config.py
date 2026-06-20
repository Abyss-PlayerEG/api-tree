"""
配置管理器
Configuration manager for API Tree.
"""

import json
from pathlib import Path


class Config:
    """
    配置管理器(单例模式),读取 ~/.config/api-tree/config.json
    Configuration manager that reads from ~/.config/api-tree/config.json.
    """
    
    _instance: "Config | None" = None
    _config: dict[str, object]
    
    def __new__(cls):
        """
        单例模式:确保全局只有一个 Config 实例
        Singleton pattern to ensure only one config instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """
        从配置文件加载,文件不存在或格式错误时使用空配置
        Load configuration from ~/.config/api-tree/config.json.
        """
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
        """
        获取输出目录:优先使用用户配置,否则回退到 Downloads
        Get output directory from config or use default.
        """
        output_dir = self._config.get("output_dir")
        if output_dir and isinstance(output_dir, str):
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
        """
        获取默认 URL:优先使用用户配置,否则回退到 localhost:8080
        Get default URL from config or use default.
        """
        val = self._config.get("default_url", "http://localhost:8080")
        return str(val)
    
    def get(
            self,
            key: str,
            default: object = None
    ) -> object:
        """
        按键获取配置值
        Get a config value by key.
        """
        return self._config.get(key, default)


# Global config instance
config = Config()
