import os
from dotenv import load_dotenv
import yaml
from .defaults import DEFAULTS

class ConfigLoader:
    def __init__(self, env_path='.env', config_path=None):
        load_dotenv(env_path)
        self.config = DEFAULTS.copy()
        self.config.update(os.environ)
        if config_path and os.path.exists(config_path):
            with open(config_path, 'r') as f:
                yaml_data = yaml.safe_load(f)
                if yaml_data:
                    self.config.update(yaml_data)

    def get(self, key, default=None):
        return self.config.get(key, default)

    def __getitem__(self, key):
        return self.config[key]

    def __contains__(self, key):
        return key in self.config