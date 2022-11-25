import os
import sys
import logging
import time
import inspect
from datetime import datetime

import torrent_ds.error
from torrent_ds.error import MissingConfigError
from torrent_ds.data import global_init as db_init
from torrent_ds.logger import init_logger
from torrent_ds.download import DownloadManager
from torrent_ds.config import load_config
from torrent_ds.util import (
    check_time,
    check_between_time,
    check_sleep_day
)

def main():
    # Initialize logger
    init_logger()

    # Load configuration
    _, config = load_config()

    logger = logging.getLogger("torrent-ds")
    try:
        db_init()

        if config["recommended"].get("enable") != "True":
            logger.info("Recommended function is disabled. Skip.")

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

            sleep_days = config["transmission"].get("sleep_days")
            sleep_time = config["transmission"].get("sleep_time")
            if sleep_time and sleep_days:
                if (check_between_time(sleep_time.split('-')[0], sleep_time.split('-')[1])
                    and check_sleep_day(sleep_days.split(';'))):
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
        for _, obj in inspect.getmembers(torrent_ds.error):
            if inspect.isclass(obj) and isinstance(e, obj):
                sys.exit(1)
        logger.exception("Unhandled exception: {}".format(e))
        sys.exit(1)


if __name__ == "__main__":
    main()
