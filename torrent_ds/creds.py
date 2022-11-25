import logging
import os
from cryptography.fernet import Fernet

from torrent_ds.error import EncryptException
from torrent_ds.config import load_credentials, get_key_path

class Credential:
    def __init__(self, name):
        self._name = name
        self._key_path = get_key_path()
        self._key = None
        self._logger = logging.getLogger("torrent-ds")
        self._credential_path, self._config = load_credentials()

        self._check_key()
        if not self._is_encrypted:
            self._encrypt()
        self._username = self._config[self._name]["user_name"]
        self._password = self._config[self._name]["password"]

    def _check_key(self):
        if not self._key_exists and self._is_encrypted:
            msg = "The key file: '{}' does not exists, to decrypt password.".format(self._key_path)
            self._logger.error(msg)
            raise EncryptException(msg)

        if not self._key_exists:
            self._create_key()
        else:
            self._read_key()

    def _create_key(self):
        self._key = Fernet.generate_key()
        with open(self._key_path, 'w') as f:
            f.write(self._key.decode())

    def _read_key(self):
        with open(self._key_path, 'r') as f:
            self._key = f.read().encode()

    def _decrypt(self):
        f = Fernet(self._key)
        return f.decrypt(self._password.encode()).decode()

    def _encrypt(self):
        f = Fernet(self._key)
        self._config[self._name]["password"] = f.encrypt(self._config[self._name]["raw_password"].encode()).decode()
        self._config[self._name]["raw_password"] = ""
        self._write_creds()

    def _write_creds(self):
        with open(self._credential_path, "w") as f:
            self._config.write(f)

    @property
    def _is_encrypted(self):
        if len(self._config[self._name]["raw_password"]) > 0:
            return False
        else:
            if len(self._config[self._name]["password"]) > 0:
                return True
            else:
                msg = "Missing password or raw password field in credential: '{}' for '{}'.".format(self._credential_path, self._name)
                self._logger.error(msg)
                raise EncryptException(msg)

    @property
    def _key_exists(self):
        return os.path.exists(self._key_path)

    @property
    def passphrase(self):
        return self._password

    @property
    def password(self):
        return self._decrypt()

    @property
    def username(self):
        return self._username

    @property
    def label(self):
        return self._name
