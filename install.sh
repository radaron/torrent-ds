#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "Installing torrent-ds..."

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

cd $SCRIPTPATH

echo "Installing pipenv..."
/usr/bin/python3.5 -m pip install pipenv

echo "Installing dependencies..."
/usr/local/bin/pipenv install

echo "Setting daemon..."
echo "[Unit]
Description=Torrent-ds service
After=multi-user.target
Conflicts=getty@tty1.service

[Service]
Type=simple
ExecStart=/usr/local/bin/pipenv run python torrent-ds.py
WorkingDirectory=$SCRIPTPATH
StandardInput=tty-force

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/torrent-ds.service


systemctl daemon-reload
systemctl enable torrent-ds.service
