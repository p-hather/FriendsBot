# F • R • I • E • N • D • S • B • O • T 

## A Friends Quiz Discord Bot

### About
* This bot is built in Python using the `discord.py` package
* The bot sends Friends quotes on a customizable timer into your chosen channel
* Users reply to guess the character that said the line, the bot responds to confirm whether the guess is correct or not
* A running score is kept
* The bot accepts a few commands to prompt actions

### Prerequisites
* All packages in `requirements.txt` installed
* A Discord bot created and added to the relevant server using the Discord Developer Portal
* A `.env` file created as per the example, and stored in the same directory as the other files

### Usage
* Simply clone the repo, add your `.env` file, and run `bot.py`
* This script will need to continue running for the bot to work - a cloud platform or Raspberry Pi acting as a server is ideal
* The bot will send a new quote to the channel every N hours (as specified in `.env`)
* `/logs` subdirectory will be created on the first run, to store the following files -
    * `history.json` to track sent quotes and their status (answered/not answered)
    * `scores.json` to keep a running scoreboard
    * `friends.log` for basic runtime logging

### Commands
* **!ANSWER** - Reveal the answer when sent in reply to a quote
* **!FRIENDS** - Send a new quote on demand
* **!SCORE** - Send the current scores

### Dataset
* Credit to https://fangj.github.io/friends/ for their hand transcribed scripts
* The data was scraped, cleaned, and cut down to a list of 16 characters (see `characters.txt`), and quotes at least 65 characters in length
