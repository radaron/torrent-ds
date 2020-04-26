from configparser import ConfigParser


class Section:
    pass


class Config:
    def __init__(self, config_path):
        self._config = ConfigParser()
        self._config.read(config_path)
        self._load_config()

    def _load_config(self):
        for section in self._config:
            print(section)
            sec = Section()
            for param in self._config[section]:
                print(param, self._config[section][param])
                sec.__setattr__(param, self._config[section][param])
            self.__setattr__(section, sec)

