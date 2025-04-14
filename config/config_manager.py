import json
from utils.logging_setup import logger


class ConfigManager:
    def __init__(self, config_path="config.json"):
        self.config = self._load_config(config_path)
        
    def _load_config(self, config_path):
        try:
            with open(config_path, "r") as f:
                return json.load(f)
        except FileNotFoundError as e:
            logger.critical(f"Config file not found: {config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.critical(f"Invalid JSON in config file: {e}")
            raise
        except Exception as e:
            logger.critical(f"Unexpected error loading config: {e}")
            raise
