# SpueBox
It plays audio from youtube and other sources into Discord channels. Built using python 3 and [discord.py](https://github.com/Rapptz/discord.py).

## Features
The bot is limited to playing music and managing tags. It doesn't welcome people, moderate your chat, or take your temperature. While it has some playlist features, its mostly designed as a voiceclip spam bot, with every play being an instant stop and play the new song operation.

All audio playing commands work only if the user is in a voice channel. The bot will join the voice channel of the user.

It supports the following commands:

- !addtag \<name> \<value> - Adds a value to the bots db that can be fetched. Tags are associated with the user that created it.
- !tag \<name> - Displays the value of the tag for the user.
- !taglist - Displays your tags
- !play \<link or tag> [loop?] - Plays audio in a voice call. This wipes the playlist. If a tag name is given, the value will be used as the link. Use loop as an optional argument to make it replay the same song.
- !playlist \<link> [loop?] [shuffle?]- Adds a youtube playlist to be played as a queue. Loop and shuffle are optional arguments
- !skip - skips to the next song if there is a queue
- !stop - Stops all songs and flushes any existing queues.

## Setup
In order to use it, you must first register and create a discord bot account.  You can create one at https://discordapp.com/developers/applications/me.

FFMpeg needs to be available in your system path. In Windows I recommend finding the binaries, dumping them into a bin folder somewhere, and adding that folder to your path. In Linux, install it using your package manager with something like `sudo apt install ffmpeg`.

Opus also needs to be available in your path. In Windows the [discord.py](https://github.com/Rapptz/discord.py) library I'm using already comes with opus included, but in Linux you have to install them. `sudo apt install libopus0` should do the job.

- Clone/download the project, copy `config.py.example` to `config.py` and configure it
- Open a terminal in the directory where you cloned/downloaded the repo
- *Optional* - set up and run a virtual environment
- `pip install -r requirements.txt`
- `python main.py`



### Python and Virtual env setup on Ubuntu
These notes are mostly for myself, but to run on a linux machine you can do the following. Python 3 may already be on your system as `python3`, but I use pyenv.

Some info is available in this askubuntu answer [here](https://askubuntu.com/questions/865554/how-do-i-install-python-3-6-using-apt-get).

#### To install PyEnv and Python
prerequisites are:
```
sudo apt-get install -y build-essential libbz2-dev libssl-dev libreadline-dev \
                        libsqlite3-dev tk-dev

# optional scientific package headers (for Numpy, Matplotlib, SciPy, etc.)
sudo apt-get install -y libpng-dev libfreetype6-dev   
```
[Pyenv](https://github.com/pyenv/pyenv) can be installed in the following way. Instructions from https://github.com/pyenv/pyenv-installer

Run the following command:

	curl -L https://raw.githubusercontent.com/pyenv/pyenv-installer/master/bin/pyenv-installer | bash

Then add the lines it tells you to add to ~/.bash_profile. Afterwards restart and run `pyenv install 3.6.3` 

If you use screen, follow the instructions [here](https://stackoverflow.com/a/20421710) as well. Specifically, add `shell -$SHELL` to `~/.screenrc`.

#### Setup the actual virtualenv
Pyenv virtual environments are managed by pyenv instead of being in any specific directory. The following creates one for the bot

	pyenv virtualenv 3.6.3 spuebox
	
and the following activates/deactivates it

	pyenv activate spuebox
	pyenv deactivate spuebox
	
and the following deletes it if you just want a clean start
	
	pyenv uninstall spuebox

Afterwards just follow the normal setup instructions. I use `screen` to run it in the background, but I may run it in some sort of manager like pm2 in the future.
	