import os

from torrentds.logger import init_logger
from torrentds.creds import Credentials
from torrentds.config import Config


def main(conf_path):
    config = Config(conf_path)


    

if __name__ == "__main__":
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config.ini")
    if not os.path.exists(config_path):
        raise Exception(f"Config file is not exist {config_path}")
    main(config_path)
