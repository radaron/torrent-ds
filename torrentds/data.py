import logging
import datetime
import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.ext.declarative as dec
from torrentds.error import DataBaseError

SqlAlchemyBase = dec.declarative_base()
__factory = None


def global_init(db_file: str):
    global __factory

    if __factory:
        return
    
    logger = logging.getLogger("root")

    if not db_file or not db_file.strip():
        raise DataBaseError("You must specify a db file.")

    conn_str = 'sqlite:///' + db_file.strip()
    logger.info("Connecting to DB with {}".format(conn_str))

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
    date = sa.Column(sa.DateTime, default=datetime.datetime.utcnow)
