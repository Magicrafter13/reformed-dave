 #!/bin/bash

# Navigate to the TabbyAPI directory
cd tabbyAPI

# Activate the virtual environment for TabbyAPI
source venv/bin/activate

# Start TabbyAPI
echo "Starting TabbyAPI..."
./start.sh &

# Wait for TabbyAPI to start (adjust the sleep time if necessary)
sleep 60

# Deactivate the current virtual environment
deactivate

# Activate the virtual environment for the Discord bot
source venv/bin/activate

# Start the Discord bot
echo "Starting Discord bot..."
python discord_bot.py
