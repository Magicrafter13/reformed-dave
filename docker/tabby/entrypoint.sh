#!/usr/bin/sh

# Set model
MODEL_NAME=$(basename "$MODEL")
if [ "$MODEL_NAME" != "Reformed-Christian-Bible-Expert-v2.1-12B_EXL2_5.5bpw_H8" ]
then
	sed -i "s/^  model_name: .*/  model_name: $MODEL_NAME/" /app/tabbyAPI/config.yml
fi

if [ -d "/app/tabbyAPI/models/$MODEL_NAME" ]
then
	cd /app/tabbyAPI/models
	git clone "$MODEL"
fi

cd /app/tabbyAPI
python start.py &

cd /app
python discord_bot.py
