import os
import shutil
import logging
import tempfile
from datetime import datetime
from calendar import monthrange
from ncoreparser import Client as NcoreClient
from ncoreparser import (
    SearchParamType,
    NcoreCredentialError,
    NcoreConnectionError,
    NcoreDownloadError,
    NcoreParserError,
    Size
)
from transmissionrpc import Client as TransmissionClient

from torrent_ds.data import create_session, Torrent
from torrent_ds.creds import Credential


download_categories = {
    "movies": [
        SearchParamType.SD_HUN,
        SearchParamType.SD,
        SearchParamType.DVD_HUN,
        SearchParamType.DVD,
        SearchParamType.DVD9_HUN,
        SearchParamType.DVD9,
        SearchParamType.HD_HUN,
        SearchParamType.HD
    ], "series": [
        SearchParamType.SDSER_HUN,
        SearchParamType.SDSER,
        SearchParamType.DVDSER_HUN,
        SearchParamType.DVDSER,
        SearchParamType.HDSER_HUN,
        SearchParamType.HDSER
    ], "musics": [
        SearchParamType.MP3_HUN,
        SearchParamType.MP3,
        SearchParamType.LOSSLESS_HUN,
        SearchParamType.LOSSLESS
    ], "clips": [
        SearchParamType.CLIP,
    ], "games": [
        SearchParamType.GAME_ISO,
        SearchParamType.GAME_RIP,
        SearchParamType.CONSOLE
    ], "books": [
        SearchParamType.EBOOK_HUN,
        SearchParamType.EBOOK
    ], "programs": [
        SearchParamType.ISO,
        SearchParamType.MISC,
        SearchParamType.MOBIL
    ], "xxx": [
        SearchParamType.XXX_IMG,
        SearchParamType.XXX_SD,
        SearchParamType.XXX_DVD,
        SearchParamType.XXX_HD
    ]
}


class DownloadManager:
    def __init__(self, config):
        self._config = config
        self._logger = logging.getLogger("torrent-ds")

    def _get_transmission_client(self):
        params = {}
        address = self._config["transmission"].get("ip_address")
        if address:
            params["address"] = address
        port = self._config["transmission"].get("port")
        if port:
            params["port"] = port
        if self._config["transmission"].get("authenticate") == "True":
            cred = Credential("transmission")
            params["user"] = cred.username
            params["password"] = cred.password

        try:
            client = TransmissionClient(**params)
        except Exception as e:
            self._logger.error("Error while connecting to tranmission-rpc. {}.".format(e))
            return None
        return client

    def _get_tracker_client(self, credential_title):
        cred = Credential(credential_title)
        try:
            client = NcoreClient(timeout=2)
            client.login(cred.username, cred.password)

        except NcoreCredentialError:
            self._logger.error("Bad credential for label: '{}'.".format(cred.label))
            return None
        except NcoreConnectionError:
            self._logger.warning("Connection error with tracker.")
            return None
        except NcoreParserError as e:
            self._logger.warning("Error while parsing web page. {}".format(e))
            return None
        return client

    def _get_download_path(self, torrent, label):
        for path in download_categories:
            for t_type in download_categories[path]:
                if torrent["type"] == t_type:
                    full_path = self._config[label].get(path)
                    return full_path if full_path else None

    def _reached_limit(self, db_session, label):
        # Get number of torrents for label in the target month
        # Returns True if reached the limit
        now = datetime.now()
        last_day = monthrange(now.year, now.month)[1]
        start_date = datetime(year=now.year, month=now.month, day=1)
        end_date = datetime(year=now.year, month=now.month, day=last_day)
        torrents = db_session.query(Torrent).filter(Torrent.date.between(start_date, end_date)) \
                                            .filter(Torrent.label.contains(label)).count()
        limit = self._config[label].get("limit")
        if limit:
            limit = int(limit)
            if torrents >= limit:
                self._logger.info("The download limit is reached. Label: {}, limit: {}/{}".format(label, torrents, limit))
                return True
        return False

    def _add_torrent(self, torrent, tracker_client, tranmission_client, label):
        if tracker_client is None:
            return
        db_session = create_session()

        if db_session.query(Torrent).filter(Torrent.tracker_id==torrent["id"]).count() != 0:
            db_session.close()
            return

        if self._reached_limit(db_session, label):
            db_session.close()
            return

        tmp_dir = tempfile.mkdtemp()
        os.chmod(tmp_dir, 0o777)
        try:
            file_path = tracker_client.download(torrent, tmp_dir)
        except NcoreConnectionError:
            self._logger.warning("Unable to connect to tracker while"
                                 " downloading '{}'.".format(torrent['title']))
            return None
        except NcoreDownloadError as e:
            self._logger.warning(e.args[0])
            return None
        except NcoreParserError as e:
            self._logger.warning("Error while parsing web page. {}".format(e))
            return None

        d_path = self._get_download_path(torrent, label)
        if d_path:
            args = {
                "download_dir": os.path.abspath(d_path)
            }
        else:
            d_path = "default download dir."
            args = {}
        new_torrent = tranmission_client.add_torrent(file_path, **args)
        torrent_db = Torrent()
        torrent_db.tracker_id = torrent["id"]
        torrent_db.transmission_id = new_torrent.id
        torrent_db.title = torrent["title"]
        torrent_db.label = label
        db_session.add(torrent_db)
        db_session.commit()
        self._logger.info("Download torrent: '{}' to '{}'.".format(torrent['title'], d_path))
        shutil.rmtree(tmp_dir)
        db_session.close()

    def clean_db(self):
        client = self._get_transmission_client()
        if client is None:
            return

        try:
            client_ids = [torrent.id for torrent in client.get_torrents()]
        except Exception: # Error while get torrents (timeout)
            self._logger.warning("Unable to clean database (time out)")
            return
        deleted_cnt = 0
        db_session = create_session()
        db_torrents = db_session.query(Torrent).all()
        for item in db_torrents:
            if item.transmission_id not in client_ids:
                db_session.delete(item)
                deleted_cnt += 1
        db_session.commit()
        self._logger.info("Cleaned {} items from db.".format(deleted_cnt))

        db_session.close()

    def download_rss(self):
        transmission_client = self._get_transmission_client()
        if transmission_client is None:
            return
        rss_list = [rss for rss in self._config.sections() if rss.startswith("rss")]
        for rss in rss_list:
            url = self._config[rss]["url"]
            credential = self._config[rss]["credential"]
            self._logger.info("Get torrents from rss: '{}', label: '{}'.".format(url, rss))

            tracker_client = self._get_tracker_client(credential)
            if tracker_client is None:
                return

            try:
                torrents = tracker_client.get_by_rss(url)
            except NcoreConnectionError:
                self._logger.warning("Unable to connect to tracker, "
                                     "while get rss.")
                return
            except NcoreParserError as e:
                self._logger.warning("Error while parsing web page. {}".format(e))
                return

            for torrent in torrents:
                self._add_torrent(torrent, tracker_client, transmission_client, rss)
            tracker_client.logout()

    def download_recommended(self):
        tracker_client = self._get_tracker_client(self._config["recommended"]["credential"])
        if tracker_client is None:
            return
        transmission_client = self._get_transmission_client()
        if transmission_client is None:
            return
        size_cfg = self._config["recommended"].get("max_size")
        self._logger.info("Downloading recommended...")
        categories = self._config["recommended"]["categories"].split(";")
        for category in categories:
            types = download_categories.get(category)
            if types is None:
                self._logger.warning("Unknown category: '{}'.".format(category))
                return
            for type in types:
                try:
                    torrents = tracker_client.get_recommended(type)
                except NcoreConnectionError:
                    self._logger.warning("Unable to connect to tracker,"
                                         " while getting recommended.")
                    continue
                except NcoreParserError as e:
                    self._logger.warning("Error while parsing web page. {}".format(e))
                    continue
                for torrent in torrents:
                    if size_cfg and torrent['size'] > Size(size_cfg):
                        self._logger.info("Skipping torrent '{}', it is too large: '{}'.".format(torrent['title'],
                                                                                                 torrent['size']))
                        continue
                    self._add_torrent(torrent, tracker_client, transmission_client, "recommended")
        tracker_client.logout()

    def start_all(self):
        client = self._get_transmission_client()
        if client is None:
            return
        self._logger.info("Starting all torrents.")
        if len(client.get_torrents()) == 0:
            return
        client.start_all()

    def stop_all(self):
        client = self._get_transmission_client()
        if client is None:
            return
        ids = [torrent.id for torrent in client.get_torrents()]
        self._logger.info("Stopping all torrents.")
        if len(ids) > 0:
            client.stop_torrent(ids)
