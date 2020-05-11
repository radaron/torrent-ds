import os
import sys
import logging
import time
import inspect
from datetime import datetime, timedelta
from configparser import ConfigParser

import torrentds.error
from torrentds.error import MissingConfigError
from torrentds.data import global_init as db_init
from torrentds.logger import init_logger
from torrentds.creds import Credential
from torrentds.download import DownloadManager
from torrentds.util import check_time, check_between_time

def main(conf_path):
    # Load configuration
    config = ConfigParser()
    config.read(conf_path)

    # Initialize logger
    log_path = os.path.join(os.path.abspath("/var/log/"), "torrent-ds.log")
    init_logger("root", log_path)
    logger = logging.getLogger("root")

    try:
        # Init database
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "database.sqlite")
        db_init(db_path)

        if config["recommended"].get("enable") != "True":
            logger.info("Recommended function is disabled. Check config: '{}'.".format(conf_path))

        start_time = datetime.now()
        start_time_recommended = datetime.now()
        # state of torrents in transmission
        started = True
        while True:

            if check_time(start_time, seconds=int(config["download"]["retry_interval"])):
                DownloadManager(config).clean_db()
                DownloadManager(config).download_rss()
                start_time = datetime.now()

            if config["recommended"].get("enable") == "True":
                if check_time(start_time_recommended, hours=int(config["recommended"]["retry_interval"])):
                    DownloadManager(config).download_recommended()
                    start_time_recommended = datetime.now()

            sleep_time = config["transmission"].get("sleep_time")
            if sleep_time:
                if check_between_time(sleep_time.split('-')[0],
                                      sleep_time.split('-')[1]):
                    if started:
                        DownloadManager(config).stop_all()
                        started = False
                else:
                    if not started:
                        DownloadManager(config).start_all()
                        started = True

            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Exiting application.")
        sys.exit(0)

    except Exception as e:
        for _, obj in inspect.getmembers(torrentds.error):
            if inspect.isclass(obj) and isinstance(e, obj):
                sys.exit(1)
        logger.exception("Unhandled exception: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    config_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "config.ini")
    if not os.path.exists(config_path):
        raise MissingConfigError("Config file is not exist: '{}'".format(config_path))
    main(config_path)
