#!/bin/bash

if [ ! -d "venv" ]; then
	echo Creating venv
	python3 -m venv venv

	venv/bin/pip install discord python-dotenv requests
fi

echo Activating venv

source venv/bin/activate

python3 discord_bot.py
