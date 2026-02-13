"""Config Manager - Handle YAML configuration file operations."""

import os
from pathlib import Path
from typing import Optional

import yaml


class ConfigManager:
    """Manages notification configuration files."""

    def __init__(self, configs_dir: Optional[Path] = None, base_dir: Optional[Path] = None):
        """Initialize the config manager.
        
        Args:
            configs_dir: Path to the configs directory. Defaults to configs/ in project root.
            base_dir: Path to the project root. Defaults to parent of web_ui.
        """
        if base_dir is None:
            base_dir = Path(__file__).parent.parent
        self.base_dir = base_dir
        
        if configs_dir is None:
            configs_dir = base_dir / "configs"
        self.configs_dir = configs_dir
        
        self.error_webhook_path = base_dir / "error_webhook.yaml"
        self.notifier_script = base_dir / "discord_notifier.py"

    def list_configs(self) -> list[dict]:
        """List all notification config files.
        
        Returns:
            List of dicts with 'name', 'path', and config contents.
        """
        configs = []
        
        if not self.configs_dir.exists():
            return configs
        
        for file_path in sorted(self.configs_dir.glob("*.yaml")):
            # Skip example files
            if file_path.suffix == ".example" or file_path.name.endswith(".example"):
                continue
            if ".example." in file_path.name:
                continue
                
            config = self.load_config(file_path.stem)
            if config:
                configs.append({
                    "name": file_path.stem,
                    "path": str(file_path),
                    "webhook_url": config.get("webhook_url", ""),
                    "message": config.get("message", ""),
                })
        
        return configs

    def load_config(self, name: str) -> Optional[dict]:
        """Load a specific config file by name.
        
        Args:
            name: Config file name without .yaml extension.
            
        Returns:
            Config dict or None if not found.
        """
        config_path = self.configs_dir / f"{name}.yaml"
        
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except yaml.YAMLError:
            return None

    def save_config(self, name: str, webhook_url: str, message: str) -> bool:
        """Save a notification config.
        
        Args:
            name: Config file name without .yaml extension.
            webhook_url: Discord webhook URL.
            message: Notification message content.
            
        Returns:
            True if saved successfully.
        """
        config_path = self.configs_dir / f"{name}.yaml"
        
        # Ensure configs directory exists
        self.configs_dir.mkdir(parents=True, exist_ok=True)
        
        config = {
            "webhook_url": webhook_url,
            "message": message,
        }
        
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False, allow_unicode=True)
            return True
        except OSError:
            return False

    def delete_config(self, name: str) -> bool:
        """Delete a config file.
        
        Args:
            name: Config file name without .yaml extension.
            
        Returns:
            True if deleted successfully.
        """
        config_path = self.configs_dir / f"{name}.yaml"
        
        if not config_path.exists():
            return False
        
        try:
            config_path.unlink()
            return True
        except OSError:
            return False

    def config_exists(self, name: str) -> bool:
        """Check if a config file exists.
        
        Args:
            name: Config file name without .yaml extension.
        """
        config_path = self.configs_dir / f"{name}.yaml"
        return config_path.exists()

    def load_error_webhook(self) -> Optional[str]:
        """Load the error webhook URL.
        
        Returns:
            Webhook URL or None if not configured.
        """
        if not self.error_webhook_path.exists():
            return None
        
        try:
            with open(self.error_webhook_path, "r", encoding="utf-8") as f:
                config = yaml.safe_load(f)
                return config.get("webhook_url") if config else None
        except yaml.YAMLError:
            return None

    def save_error_webhook(self, webhook_url: str) -> bool:
        """Save the error webhook URL.
        
        Args:
            webhook_url: Discord webhook URL for errors.
            
        Returns:
            True if saved successfully.
        """
        config = {"webhook_url": webhook_url}
        
        try:
            with open(self.error_webhook_path, "w", encoding="utf-8") as f:
                yaml.dump(config, f, default_flow_style=False)
            return True
        except OSError:
            return False

    def get_notifier_command(self, config_name: str) -> str:
        """Get the full command to run a notification.
        
        Args:
            config_name: Config file name without .yaml extension.
            
        Returns:
            Full command string for cron.
        """
        venv_python = self.base_dir / "venv" / "bin" / "python3"
        config_path = self.configs_dir / f"{config_name}.yaml"
        
        # Use venv python if it exists, otherwise system python3
        if venv_python.exists():
            python_path = str(venv_python)
        else:
            python_path = "python3"
        
        return f"{python_path} {self.notifier_script} {config_path}"

