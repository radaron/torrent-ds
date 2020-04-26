import os
from cryptography.fernet import Fernet

class EncryptException(Exception):
    pass

class Credentials:
    def __init__(self, logger, password, key_path, encrypted=True):
        self._key_path = key_path
        self._logger = logger
        self._key = None
        self._encripted = encrypted
        if not self._key_exists() and encrypted:
            self.logger.error(f"The key file: '{self._key_path}' does not exists, to decrypt password.")
            raise EncryptException(f"The key file: '{self._key_path}' does not exists, to decrypt password.")
        if not self._key_exists():
            self._create_key()
        else:
            self._read_key()
        if not encrypted:
            self._password = self._encrypt(password)

    def _key_exists(self):
        return os.path.exists(self._key_path)
    
    def _create_key(self):
        self._key = Fernet.generate_key()
        with open(self._key_path, 'w') as f:
            f.write(self._key)
    
    def _read_key(self):
        with open(self._key_path, 'r') as f:
            self._key = f.read()

    def _decrypt(self):
        f = Fernet(self._key)
        return f.decrypt(self._password)
        
    def _encrypt(self, password):
        f = Fernet(self._key)
        return f.encrypt(password)

    @property
    def passphrase(self):
        return self._password

    @property
    def password(self):
        return self._decrypt()
            
