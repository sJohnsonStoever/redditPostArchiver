#!/bin/sh
set -e

python3 entrypoint.py

if [ -e "$1" ] ; then
  set -- python3 "$@"
fi

exec "$@"