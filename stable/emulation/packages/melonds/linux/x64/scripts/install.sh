#!/bin/sh
MELONDS_URL="https://github.com/melonDS-emu/melonDS/releases/download/1.1/melonDS-1.1-ubuntu-x86_64.zip"

curl -o /tmp/melonds.zip $MELONDS_URL

unzip /tmp/melonds.zip -o /usr/bin

rm /tmp/melonds.zip
