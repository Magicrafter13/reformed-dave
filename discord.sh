#!/bin/bash

# Adapted from github:theroyallab/tabbyAPI, commit fa8035ef.
# https://github.com/theroyallab/tabbyAPI/blob/fa8035ef7299293fb8bf70ed28d811ec42138004/start.sh
# While that project is licensed under AGPLv3, and thus this adaptation is as well, I don't think I am required to disclose this nor make the rest of the project AGPLv3 due to the fact that this code is not in ANY way 

if [ ! -d "venv" ]; then
	echo Creating venv
	python3 -m venv venv

	venv/bin/pip install discord python-dotenv requests
fi

echo Activating venv

# shellcheck source=/dev/null
source venv/bin/activate

python discord_bot.py
