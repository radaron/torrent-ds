#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

echo "Installing torrent-ds..."

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"


echo "Installing os dependencies..."
apt install python3-pip python-dev python3-dev build-essential libssl-dev

echo "Installing setuptools..."
/usr/bin/python3.5 -m pip install setuptools

echo "Installing pipenv..."
/usr/bin/python3.5 -m pip install pipenv

cd $SCRIPTPATH

echo "Installing dependencies..."
/usr/local/bin/pipenv install

echo "Setting torrent-ds daemon..."
echo "[Unit]
Description=Torrent-ds service
After=multi-user.target
Conflicts=getty@tty1.service

[Service]
Type=simple
Environment="LC_ALL=C.UTF-8"
Environment="LANG=C.UTF-8"
ExecStart=/usr/local/bin/pipenv run python torrent-ds.py
WorkingDirectory=$SCRIPTPATH
StandardOutput=syslog
StandardError=syslog

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/torrent-ds.service


systemctl daemon-reload
systemctl enable torrent-ds.service
systemctl start torrent-ds.service
