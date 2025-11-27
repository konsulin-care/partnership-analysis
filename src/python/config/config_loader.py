import os
from dotenv import load_dotenv
import yaml
from .defaults import DEFAULTS

class ConfigLoader:
    def __init__(self, env_path='.env', config_path=None):
        load_dotenv(env_path)
        self.config = {k.lower(): v for k, v in DEFAULTS.items()}
        env_lower = {k.lower(): v for k, v in os.environ.items()}
        self.config.update(env_lower)
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    yaml_lower = {k.lower(): v for k, v in yaml_data.items()}
                    self.config.update(yaml_lower)

    def get(self, key, default=None):
        return self.config.get(key.lower(), default)

    def __getitem__(self, key):
        return self.config[key.lower()]

    def __contains__(self, key):
        return key.lower() in self.config