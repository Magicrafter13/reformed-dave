#!/bin/bash

if [ ! -d "venv" ]; then
	echo Creating venv
	python3 -m venv venv

	venv/bin/pip install -r requirements.txt
fi

echo Activating venv

source venv/bin/activate

python3 discord_bot.py
