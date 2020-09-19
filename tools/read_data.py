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

parser.add_argument('--number', '-n',
                    action="store_true",
                    help="Print number of torrents.")

parser.add_argument('--label', '-l',
                    metavar='LABEL',
                    type=str,
                    help="Filter the labels.")

parser.add_argument('--title', '-t',
                    metavar='TITLE',
                    type=str,
                    help="Filter the title.")


args = parser.parse_args()

global_init(os.path.join(os.path.abspath(os.path.dirname(__file__)), "..", "database.sqlite"))

session = create_session()

torrents = session.query(Torrent).order_by(Torrent.date.desc())
if args.label or args.title:
    if args.label:
        torrents = torrents.filter(Torrent.label.contains(args.label))
    if args.title:
        torrents = torrents.filter(Torrent.title.contains(args.title))
else:
    torrents = torrents.all()

if args.number:
    print("Number of torrents: "
          "{}.".format(len(list(torrents))))
    sys.exit(0)

elif args.json:
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
    row = "|{:^40}|{:^90}|{:^40}|{:^15}|{:^15}|"
    separate = "{}".format('-'*206)

    print(separate)
    print(row.format("Label", "Title", "Date", "Tracker id", "Client id"))
    print(separate)
    for t in torrents:
        print(separate)
        title = t.title if len(t.title) <= 80 else "{}...".format(t.title[:77])
        print(row.format(t.label, title, str(t.date), t.tracker_id,
                         t.transmission_id))
    print(separate)


