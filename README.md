# Reformed Dave
Discord bot to allow users to ask theological questions and get answers through
an LLM. The intended personality of Reformed Dave is a Christian whose beliefs
align with Reformed Presbyterians.

# Running
## First Time Setup
Requirements:
- git-lfs
- Python 3.10-3.12
- tmux

Some basic setup is done by `init.sh`. Before running it, keep reading.

TabbyAPI currently requires Python 3.10, 3.11, or 3.12. This repo will assume
that 3.12 is installed. You can change this in `init.sh`.

Before automating this with systemd or some other such service, please run
`start_all.sh` in an interactive session. The first time it is run through, it
will setup tabbyAPI.

## Standard Operation
Simply run `start_all.sh`. It will launch tabbyAPI in a tmux session, wait for a
bit, then start the Discord bot. You can exit the script by typing
quit/stop/exit, or sending an interrupt signal, and it should cleanup by closing
the bot and the API.

# Credits/Notes
- Based on the work of "D20joy".
- Original setup/version by "sleepdeprived3".
- Deployability and touch-ups by Matthew Rease.

<div align="center">
In loving memory of "D20joy".
</div>
<br />
<div align="center">
Romans 8:37-39 LSB

But in all these things we overwhelmingly conquer through Him who loved us.  
For I am convinced that neither death, nor life, nor angels, nor rulers, nor
things present, nor things to come, nor powers,  
nor height, nor depth, nor any other created thing, will be able to separate us
from the love of God, which is in Christ Jesus our Lord.
</div>
