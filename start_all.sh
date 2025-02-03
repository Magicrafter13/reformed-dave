#!/bin/bash

# FIRST, make sure files are linked
[ ! -f ./tabbyAPI/config.yml ] && ln ./config.yml ./tabbyAPI/config.yml
[ ! -f ./tabbyAPI/sampler_overrides/dave_preset.yml ] && ln ./dave_preset.yml ./tabbyAPI/sampler_overrides/dave_preset.yml

# Get random session ID
session=$RANDOM

# Start tabbyAPI
echo "Starting TabbyAPI..."
tmux new -d -s "tabby-$session"
tmux send -t "tabby-$session" "cd tabbyAPI" C-m "./start.sh" C-m

# Wait for TabbyAPI to start (adjust the sleep time if necessary)
sleep 60

# Start Discord bot
echo "Starting Discord bot..."
tmux new -d -s "discord-$session"
tmux send -t "discord-$session" "bash discord.sh" C-m

# Handle exit gracefully...
cleanup() {
	err=$?

	tmux send -t "discord-$session" C-c "exit" C-m
	tmux send -t "tabby-$session" C-c "exit" C-m

	exit $err
}

trap "cleanup" EXIT

while true
do
	read command
	if [ "$command" == quit ] || [ "$command" == stop ] || [ "$command" == exit ]
	then
		exit 0
	fi
done
