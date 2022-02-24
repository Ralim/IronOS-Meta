#! /bin/sh
echo $1
echo $2
set -e
find Images/ -type f -exec python3 img2logo.py {} "$1" "$2" \;
