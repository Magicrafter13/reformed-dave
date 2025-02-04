#!/usr/bin/bash

# Get random session ID
session=$RANDOM

# Start Discord bot
echo "Starting Discord bot..."
tmux new -d -s "discord-$session"
tmux send -t "discord-$session" "bash discord.sh" C-m

# Handle exit gracefully...
cleanup() {
	err=$?

	tmux send -t "discord-$session" C-c "exit" C-m

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
