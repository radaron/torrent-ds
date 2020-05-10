import os
import shutil
import logging
import tempfile
from ncoreparser import Client as NcoreClient
from ncoreparser import (
    SearchParamType,
    NcoreCredentialError,
    NcoreConnectionError,
    NcoreDownloadError,
    Size
)
from transmissionrpc.client import Client as TransmissionClient

from torrentds.data import create_session, Torrent
from torrentds.creds import Credential


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
        self._logger = logging.getLogger("root")
        self._credentials_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "credentials.ini")
        self._key_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "key.key")

    def _get_transmission_client(self):
        params = {}
        address = self._config["transmission"].get("ip_address")
        if address:
            params["address"] = address
        port = self._config["transmission"].get("port")
        if port:
            params["port"] = port
        if self._config["transmission"].get("authenticate") == "True":
            cred = Credential("transmission", self._credentials_path, self._key_path)
            params["username"] = cred.username
            params["password"] = cred.password

        try:
            client = TransmissionClient(**params)
        except Exception as e:
            self._logger.exception("Error while connecting to tranmission-rpc. {}".format(e))
            return None
        return client

    def _get_tracker_client(self, credential_title):
        cred = Credential(credential_title, self._credentials_path, self._key_path)
        try:
            client = NcoreClient()
            client.open(cred.username, cred.password)

        except NcoreCredentialError:
            self._logger.exception("Bad credential for label: '{}'.".format(cred.label))
            return None
        except NcoreConnectionError:
            self._logger.exception("Connection error with tracker.")
            return None
        return client

    def _get_download_path(self, torrent, label):
        for path in download_categories:
            for t_type in download_categories[path]:
                if torrent["type"] == t_type:
                    full_path = self._config[label].get(path)
                    return full_path if full_path else None

    def _add_torrent(self, torrent, tracker_client, tranmission_client, label):
        if tracker_client is None:
            return
        tmp_dir = tempfile.mkdtemp()
        os.chmod(tmp_dir, 0o777)
        try:
            file_path = tracker_client.download(torrent, tmp_dir)
        except NcoreConnectionError:
            self._logger.warning("Unable to connect to tracker.")
            return None
        except NcoreDownloadError as e:
            self._logger.warning(e.args[0])
            return None

        d_path = self._get_download_path(torrent, label)
        if d_path:
            args = {
                "download_dir": os.path.abspath(d_path)
            }
        else:
            d_path = "default download dir."
            args = {}
        db_session = create_session()
        if db_session.query(Torrent).filter_by(tracker_id=torrent["id"]).count() == 0:
            new_torrent = tranmission_client.add_torrent(file_path, **args)
            torrent_db = Torrent()
            torrent_db.tracker_id = torrent["id"]
            torrent_db.transmission_id = new_torrent.id
            db_session.add(torrent_db)
            db_session.commit()
            self._logger.info("Download torrent: '{}' to '{}'.".format(torrent['title'], d_path))
        db_session.close()
        shutil.rmtree(tmp_dir)

    def clean_db(self):
        self._logger.info("Cleaning database...")

        client = self._get_transmission_client()
        if client is None:
            return

        client_ids = [torrent.id for torrent in client.get_torrents()]
        deleted_cnt = 0
        db_session = create_session()
        db_torrents = db_session.query(Torrent).all()
        for item in db_torrents:
            if item.transmission_id not in client_ids:
                db_session.delete(item)
                deleted_cnt += 1
        db_session.commit()
        self._logger.info("Deleted {} items from db.".format(deleted_cnt))

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

            torrents = tracker_client.get_by_rss(url)
            for torrent in torrents:
                self._add_torrent(torrent, tracker_client, transmission_client, rss)
            tracker_client.close()

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
                torrents = tracker_client.get_recommended(type)
                for torrent in torrents:
                    if size_cfg and torrent['size'] > Size(size_cfg):
                        self._logger.info("Skipping torrent '{}', it is too large: '{}'.".format(torrent['title'],
                                                                                                 torrent['size']))
                        continue
                    self._add_torrent(torrent, tracker_client, transmission_client, "recommended")

    def start_all(self):
        client = self._get_transmission_client()
        if client is None:
            return
        if len(client.get_torrents()) == 0:
            return
        self._logger.info("Starting all torrents.")
        client.start_all()

    def stop_all(self):
        client = self._get_transmission_client()
        if client is None:
            return
        ids = [torrent.id for torrent in client.get_torrents()]
        self._logger.info("Stopping all torrents.")
        if len(ids) > 0:
            client.stop_torrent(ids)
