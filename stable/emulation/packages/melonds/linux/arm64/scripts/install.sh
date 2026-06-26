#!/bin/sh
MELONDS_URL="https://github.com/melonDS-emu/melonDS/releases/download/1.1/melonDS-1.1-ubuntu-aarch64.zip"

curl -L -o /tmp/melonds.zip $MELONDS_URL

unzip /tmp/melonds.zip -d /usr/bin

rm /tmp/melonds.zip
