#!/usr/bin/bash

PYVER='3.12'
MODEL='https://huggingface.co/sleepdeprived3/Reformed-Christian-Bible-Expert-v2.1-12B_EXL2_5.5bpw_H8'

# Change model if user has modified the variable above
MODEL_NAME=$(basename "$MODEL")
if [ "$MODEL_NAME" != "Reformed-Christian-Bible-Expert-v2.1-12B_EXL2_5.5bpw_H8" ];
then
	sed -i "s/^  model_name: .*/  model_name: $MODEL_NAME/" config.yml
fi

# Get tabbyAPI
git submodule update --init
# Get model
cd tabbyAPI/models
git clone "$MODEL"
cd -

# Setup Discord bot
sed -i "s/python3[^ ]*/python$PYVER/" discord.sh

# Setup tabbyAPI
echo 'Doing first time tabbyAPI setup.'
echo 'Follow on-screen instructions, and when its finally up and running on port 5000,'
echo 'close it with ^C.'
sleep 5
cd tabbyAPI
sed -i "s/python3[^ ]*/python$PYVER/" start.sh
./start.sh
cd -

exit 0
