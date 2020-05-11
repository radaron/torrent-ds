import os
import sys
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
from torrentds.data import (
        global_init,
        create_session,
        Torrent
)


global_init(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "database.sqlite"))

session = create_session()

torrents = session.query(Torrent).all()

row = "|{:^50}|{:^50}|{:^50}|"
separate = "{}".format('-'*154)

print(separate)
print(row.format("Label", "Title", "Date"))
print(separate)
for t in torrents:
    print(separate)
    print(row.format(t.label, t.title, str(t.date)))
print(separate)

