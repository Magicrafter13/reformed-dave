# Reformed Dave
Discord bot to allow users to ask theological questions and get answers through
an LLM. The intended personality of Reformed Dave is a Christian whose beliefs
align with Reformed Presbyterians.

# Running
## First Time Setup
### With included tabbyAPI scripts/setup.
Requirements:
- git-lfs
- Python 3.10-3.12
- tmux

Some basic setup is done by `init_all.sh`. Before running it, keep reading.

TabbyAPI currently requires Python 3.10, 3.11, or 3.12. This repo will assume
that 3.12 is installed. You can change this in `init_all.sh`.

Before automating this with systemd or some other such service, please run
`start_all.sh` in an interactive session. The first time it is run through, it
will setup tabbyAPI.

### With existing tabbyAPI setup.
If you do not wish to use the tabbyAPI setup included in this repository (or you
already have one setup you want to use), then the steps above are essentially
the same, except you only need to run `init.sh` to get the Discord bot ready,
and then `start.sh` to start the Discord bot. By taking this route you are
responsible for properly connecting the bot to the API (for example if you
changed the port, or run it on a different IP), as well as getting the Pastor
Dave model working in tabby.

Consider this the advanced route - but it is understandable that someone may
wish to use an existing tabbyAPI installation.

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
