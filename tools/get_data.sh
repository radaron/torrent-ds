#!/bin/bash

SCRIPTPATH="$( cd "$(dirname "$0")" >/dev/null 2>&1 ; pwd -P )"

export LC_ALL=C.UTF-8
export LANG=C.UTF-8

cd $SCRIPTPATH

pipenv run python "$SCRIPTPATH/read_data.py" "$@"
