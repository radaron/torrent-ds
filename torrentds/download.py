import os
import logging
import tempfile
from ncoreparser.client import Client as NcoreClient
from ncoreparser.data import SearchParamType
from ncoreparser.error import (
    NcoreCredentialError, 
    NcoreConnectionError,
    NcoreDownloadError
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
        ip = self._config["transmission"]["ip_address"]
        port = self._config["transmission"]["port"]
        cred = Credential("transmission", self._credentials_path, self._key_path)
        try:
            client = TransmissionClient(
                address=ip,
                port=port,
                user=cred.username,
                password=cred.password)

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
                    full_path = self._config[label][path]
                    return full_path if full_path else None

    def _add_torrent(self, torrent, tracker_client, tranmission_client, label):
        if tracker_client is None:
            return
        tmp_dir = tempfile.mkdtemp()
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
        new_torrent = tranmission_client.add_torrent(file_path, **args)
        
        db_session = create_session()
        if db_session.query(Torrent).filter_by(tracker_id=torrent["id"]).count() == 0:
            torrent_db = Torrent()
            torrent_db.tracker_id = torrent["id"]
            torrent_db.transmission_id = new_torrent.id
            db_session.add(torrent_db)
            db_session.commit()
            self._logger.info("Download torrent: '{}' to '{}'.".format(torrent['title'], d_path))
        db_session.close()
        
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
        rss_list = [rss for rss in self._config.sections() if rss.startswith("rss")]
        for rss in rss_list:
            url = self._config[rss]["url"]
            credential = self._config[rss]["credential"]
            self._logger.info("Get torrents from rss: '{}', label: '{}'.".format(url, rss))
            
            tracker_client = self._get_tracker_client(credential)
            if tracker_client is None:
                return

            transmission_client = self._get_transmission_client()
            if transmission_client is None:
                return
            
            db_session = create_session()
            ids = db_session.query(Torrent.transmission_id).all()
            torrents = tracker_client.get_by_rss(url)
            for torrent in torrents:
                if torrent["id"] not in ids:
                    self._add_torrent(torrent, tracker_client, transmission_client, rss)
            tracker_client.close()
            db_session.close()

    def download_recommended(self):
        tracker_client = self._get_tracker_client(self._config["recommended"]["credential"])
        if tracker_client is None:
            return
        transmission_client = self._get_transmission_client()
        if transmission_client is None:
            return
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
                    download_path = self._config["recommended"].get(category)
                    if download_path is None:
                        self._logger.warning("Download path is not defined for category: '{}' in recommended.".format(category))
                        return
                    self._add_torrent(torrent, tracker_client, transmission_client, "recommended")
    
    def start_all(self):
        client = self._get_transmission_client()
        if client is None:
            return
        if len(client.get_torrents()) == 0:
            return
        client.start_all()
    
    def stop_all(self):
        client = self._get_transmission_client()
        if client is None:
            return
        ids = [torrent.id for torrent in client.get_torrents()]
        client.stop_torrent(ids)
