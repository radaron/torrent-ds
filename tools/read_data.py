import os
import sys
import json
import argparse
sys.path.append(os.path.join(os.path.abspath(os.path.dirname(__file__)), ".."))
from torrentds.data import (
        global_init,
        create_session,
        Torrent
)

parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('--json', '-j',
                    action="store_true",
                    help="Output format is json.")

parser.add_argument('--label', '-l',
                    metavar='LABEL',
                    type=str,
                    help="Filter the labels.")

args = parser.parse_args()

global_init(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "database.sqlite"))

session = create_session()

torrents = session.query(Torrent).order_by(Torrent.date.desc())
if args.label:
    torrents = torrents.filter(Torrent.label.contains(args.label))
torrents = torrents.all()


if args.json:
    json_data = {}
    for t in torrents:
        if t.label not in json_data:
            json_data[t.label] = []
        json_data[t.label].append({
            "title": t.title,
            "tracker_id": t.tracker_id,
            "client_id": t.transmission_id,
            "date": str(t.date)
        })
    print(json.dumps(json_data, indent=2))

else:
    row = "|{:^50}|{:^70}|{:^50}|{:^15}|{:^15}|"
    separate = "{}".format('-'*206)

    print(separate)
    print(row.format("Label", "Title", "Date", "Tracker id", "Client id"))
    print(separate)
    for t in torrents:
        print(separate)
        print(row.format(t.label, t.title, str(t.date), t.tracker_id,
                         t.transmission_id))
    print(separate)
