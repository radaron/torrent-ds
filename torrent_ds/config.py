import os
import logging
from configparser import ConfigParser


CONFIG_PATH_DIR = os.path.expanduser("~/.config/torrent_ds")
CONFIG_PATH = os.path.join(CONFIG_PATH_DIR, "config.ini")
CREDENTIAL_PATH = os.path.join(CONFIG_PATH_DIR, "credentials.ini")
KEY_PATH = os.path.join(CONFIG_PATH_DIR, "key")
CREDENTIALS_SAMPLE = """
[transmission]
user_name = username
raw_password = password
password =

[cred1]
user_name = username
raw_password = password
password =

[cred2]
user_name = username
raw_password = password
password =
"""

CONFIG_SAMPLE = """
[transmission]
authenticate = False
ip_address =
port =
sleep_days =
sleep_time =

[download]
# second
retry_interval = 10

[recommended]
enable = False
credential = cred1
categories = movies;series;musics;games;programs;books;xxx
max_size = 3 GiB
# hour
retry_interval = 5
movies =
series =
musics =
games =
books =
programs =
xxx =

[rss bookmark1]
credential = cred1
limit =
url =
movies =
series =
musics =
clips =
games =
books =
programs =
xxx =

[rss bookmark2]
credential = cred2
limit =
url =
movies =
series =
musics =
clips =
games =
books =
programs =
xxx =
"""


logger = logging.getLogger("torrent-ds")


def check_conf_dir():
    if not os.path.exists(CONFIG_PATH_DIR):
        logger.info(f"Creating directory: '{CONFIG_PATH_DIR}'")
        os.makedirs(CONFIG_PATH_DIR)


def load_config():
    check_conf_dir()
    config = ConfigParser()
    if not config.read(CONFIG_PATH):
        with open(CONFIG_PATH, 'w') as f:
            f.write(CONFIG_SAMPLE)
        config.read(CONFIG_PATH)
    logger.info(f"Read config file: '{CONFIG_PATH}'")
    return CONFIG_PATH, config


def load_credentials():
    check_conf_dir()
    credentials = ConfigParser()
    if not credentials.read(CREDENTIAL_PATH):
        with open(CREDENTIAL_PATH, 'w') as f:
            f.write(CREDENTIALS_SAMPLE)
        credentials.read(CREDENTIAL_PATH)
    logger.info(f"Read credentials file: '{CREDENTIAL_PATH}'")
    return CREDENTIAL_PATH, credentials


def get_key_path():
    check_conf_dir()
    return KEY_PATH