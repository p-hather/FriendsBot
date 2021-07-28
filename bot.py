from dotenv import load_dotenv
import os
import discord
import random
from discord.ext import tasks
from json_dict import *
import pandas as pd
import logging


load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')  # Bot token
CHANNEL = os.getenv('CHANNEL')  # Discord channel ID
N_HOURS = os.getenv('HOURS')  # How frequently should quotes be sent?

if not os.path.isdir('./logs'):
    os.mkdir('./logs')

logging.basicConfig(level=logging.INFO, filename="./logs/friends.log", filemode="a+",
                    format="%(asctime)-15s %(levelname)-8s %(message)s")


class FriendsBot(discord.Client):
    """
    Connects to Discord via a bot that needs to be preconfigured
    through the Discord Developer Portal and authenticated with
    a token in a .env file.

    Sends a new Friends quote to the chosen channel every N hours,
    users reply to guess the character. Responds to guesses, as
    well as keeping a running score.

    Accepts the following commands:

    !ANSWER - Reveal the answer when sent in reply to a quote
    !FRIENDS - Send a new quote
    !SCORE - Send the current scores
    """
    def __init__(self, **options):
        super().__init__(**options)
        self.source_fp = './dataset/friends.csv'
        self.source_df = pd.read_csv(self.source_fp)
        self.db_fp = './logs/history.json'
        self.scores_fp = './logs/scores.json'

    def generate_quote(self):
        """Selects a random quote and returns a dict object"""
        length = len(self.source_df)
        row = random.randint(0, length)
        return {"character": self.source_df.character[row],
                "line": self.source_df.line[row],
                "ep_code": self.source_df.ep_code[row],
                "ep_name": self.source_df.ep_name[row],
                "answered": False,
                "answered_by": None}

    def update_score(self, user_id, name, points):
        """
        Adds one point to the passed user ID's entry in scores.json,
        and updates the username with the name from the message
        """
        try:
            scores = read_json(self.scores_fp)
            try:
                scores[user_id]['name'] = name
                scores[user_id]['score'] += points
            except KeyError:
                scores.update({user_id: {'name': name, 'score': points}})
        except FileNotFoundError:
            scores = {user_id: {'name': name, 'score': points}}
            logging.info(f'Creating {self.scores_fp}')
        write_json(scores, self.scores_fp)
        logging.info(f'Added one point to {name} - {self.scores_fp}')

    async def send_scores(self):
        """Sorts and sends current scoreboard, stored in scores.json"""
        channel = bot.get_channel(int(CHANNEL))
        try:
            sd = read_json(self.scores_fp)
            scores = dict(sorted(sd.items(), key=lambda x: x[1]['score'], reverse=True))
            lb_list = [f"{scores[k]['name']}: {scores[k]['score']}" for k in scores]
            lb = '\n'.join(lb_list)
            message = f':coffee: The scores are:\n{lb}'
            logging.info(f'Sending scores:\n{lb}')
        except FileNotFoundError:
            message = 'No scores recorded yet...'
        await channel.send(message)

    async def on_ready(self):
        """Logs successful connection"""
        logging.info(f'{self.user} has connected to Discord')

    async def send_quote(self):
        """Sends a new quote and logs it in history.json"""
        channel = bot.get_channel(int(CHANNEL))
        quote = self.generate_quote()
        line = quote['line']
        receipt = await channel.send(line)
        logging.info("Sent quote: '{}'".format(line))
        rw_json({receipt.id: quote}, self.db_fp)

    @staticmethod
    async def get_username(user_id):
        """Unused - for reference only. Returns current username from user ID"""
        user = await bot.fetch_user(user_id)
        return user.name

    @tasks.loop(hours=int(N_HOURS))
    async def timer(self):
        """Sends new quote every N hours (variable from .env)"""
        logging.info('Sending new quote on timer')
        await self.send_quote()

    @timer.before_loop
    async def before(self):
        """Waits until the bot is ready"""
        await bot.wait_until_ready()
        logging.info("Finished waiting")

    async def on_message(self, message):
        """
        Runs every time a message is received in server.
        This method does most of the heavy lifting for the bot.
        Accepts commands (see comments) and responds to users
        guesses by looking up message IDs against history.json.
        """
        author = message.author
        channel = str(message.channel.id)

        if author == bot.user or channel != CHANNEL:
            # Message is from the bot or in a different channel
            return
        else:
            text_raw = message.content
            text = text_raw.upper().strip()
            ref = message.reference
            m_name = author.name
            user_id = str(author.id)

        if text.startswith('!FRIENDS'):  # User requested new quote
            logging.info(f'New quote requested by {m_name}')
            await self.send_quote()
        elif text.startswith('!SCORE'):  # User requested scoreboard
            logging.info(f'Scores requested by {m_name}')
            await self.send_scores()
        else:
            if ref:
                ref_id = str(ref.message_id)
                db = read_json(self.db_fp)  # Reads latest json data every time

                if ref_id in db:  # Replied message is in sent quote db
                    entry = db[ref_id]
                    answer = entry['character']
                    line = entry['line']
                    ep_code = entry['ep_code']
                    ep_name = entry['ep_name']

                    def mark_answered(revealed=False):
                        """Nested function to mark quotes as answered"""
                        entry['answered'] = True
                        if not revealed:
                            entry['answered_by'] = user_id
                            self.update_score(user_id, m_name, 1)
                        rw_json(db, self.db_fp)

                    if text.startswith('!ANSWER'):  # Reveal the answer
                        logging.info(f"Answer to '{line}' is {answer}  - reveal requested by {m_name}")
                        reply = f':bulb: The answer is {answer}, from {ep_code} - {ep_name}'
                        mark_answered(revealed=True)
                    elif entry['answered']:  # Quote already answered
                        logging.info(f'Quote has already been answered - rejecting guess from {m_name}')
                        reply = ':x: This quote has already been answered'
                    elif text in answer.upper():  # Answer matches
                        logging.info(f"Answer '{text_raw}' from {m_name} matches '{answer}' from database!")
                        reply = f':white_check_mark: The answer is {answer}, from {ep_code} - {ep_name}. ' \
                                f'+1 to {m_name} :trophy: '
                        mark_answered()
                    else:  # Incorrect answer
                        logging.info(f"Incorrect answer '{text_raw}' submitted by {m_name}")
                        reply = f':x: Incorrect, -1 to {m_name}'
                        self.update_score(user_id, m_name, -1)

                    await message.reply(reply)


if __name__ == '__main__':
    bot = FriendsBot()
    bot.timer.start()
    bot.run(TOKEN)
