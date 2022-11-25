import logging
import os
import datetime
import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.ext.declarative as dec
from torrent_ds.error import DataBaseError

DB_FILE_DIR = os.path.expanduser("~/.local/share/torrent_ds")
DB_FILE_PATH = os.path.join(DB_FILE_DIR, "database.db")
SqlAlchemyBase = dec.declarative_base()
__factory = None



def global_init():
    global __factory

    if __factory:
        return

    logger = logging.getLogger("torrent-ds")

    if not os.path.exists(DB_FILE_DIR):
        os.makedirs(DB_FILE_DIR)

    conn_str = 'sqlite:///' + DB_FILE_PATH
    logger.info("Connecting to DB -> {}".format(conn_str))

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    SqlAlchemyBase.metadata.create_all(engine)


def create_session():
    global __factory
    return __factory()


class Torrent(SqlAlchemyBase):
    __tablename__ = "torrents"

    tracker_id = sa.Column(sa.Integer, primary_key=True, nullable=False)
    transmission_id = sa.Column(sa.Integer, nullable=False)
    title = sa.Column(sa.String)
    label = sa.Column(sa.String)
    date = sa.Column(sa.DateTime, default=datetime.datetime.now)
