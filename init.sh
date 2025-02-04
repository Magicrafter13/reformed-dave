#!/usr/bin/bash

PYVER='3.12'

# Setup Discord bot
sed -i "s/python3/python$PYVER/" discord.sh
