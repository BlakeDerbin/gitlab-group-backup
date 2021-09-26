import yaml
import sys


def config_yaml():
    # Read in config.yaml
    try:
        with open('./config.yaml') as f:
            return yaml.load(f, Loader=yaml.FullLoader)
    except OSError as e:
        print(f"Config error: {e}")
        sys.exit(1)
