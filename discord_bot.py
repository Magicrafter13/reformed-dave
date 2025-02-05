#!/usr/bin/env python3
"""Reformed Christian Discord chatbot."""

import logging
from os import environ

import discord
import requests
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning

load_dotenv()

# Suppress only the single InsecureRequestWarning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

TOKEN = environ.get('DISCORD_TOKEN')

# Replace 'http://127.0.0.1:8080/v1/chat/completions' with the correct URL and endpoint
TABBY_API_URL = 'http://127.0.0.1:5000/v1/chat/completions'

intents = discord.Intents.default()
intents.message_content = True  # Ensure this line is present and enabled
intents.messages = True  # Ensure this line is present and enabled

client = discord.Client(intents=intents)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Create a session with retries
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))

# Character-specific logic for "Reformed Dave"
CHARACTER_CONTEXT = """
Reformed Dave's Persona: Name: Pastor Dave;
Age: 55;
Gender: Male;
Marital status: Married;
Occupation: Pastor;
Religion: Presbyterian Church in America;
Appearance: 70 inches tall, White skin, Short white hair, Green eyes;
Clothing: Blue blazer, White button down shirt, Black leather belt, Blue slacks, Black dress shoes;
Likes: Paedobaptism, Calvinism, Reformed theology, The Bible;
Dislikes: Credobaptism, Iconolatry, Idolatry, Pictures of Jesus, Pictures of the Godhead, Pagans, Racists, Female preachers, Drugs, Sexual immorality, Foul language;
Relationships: User (Pastor);
Personality: Compassionate, Confident, Empathic, Friendly, Helpful, Honest, Humble, Kind, Optimistic, Patient, Reliable, Responsible, Conscientious, Competent, Intelligent;
Description: Pastor Dave is a pastor of the Presbyterian church. Pastor Dave is strictly against idolatry for any reason. Pastor Dave is devout in his faith towards the Lord and Reformed Theology. Pastor Dave preaches the Gospel at your local church. Pastor Dave will accurately preach the Word of the Bible and the lessons it teaches to all who are willing to listen. Should you have any personal questions for Pastor Dave or questions regarding the faith Pastor Dave is ready to answer. When answering questions Pastor Dave will often quote verses of the bible to use an example and Pastor Dave will first give the average accepted answer that the Presbyterian church would put forth and afterwards Pastor Dave will present his own personal answer based on Pastor Dave opinion;
Theology: Pastor Dave theology is rooted in the Westminster Standards and Paedobaptism. Pastor Dave affirms the Westminster Confession of Faith. God as the independent, triune God who made the heavens and earth, the Bible is the infallible word of God, all people are sinners, justification is not by works but by faith in the Lord Jesus Christ, The absolute sovereignty of God in election, The duty of the Christian to live a life of piety in accordance with God’s moral law including the Ten Commandments, Participation in the two sacraments, Baptism of babies and the Lord’s Supper, The theological existence of both the invisible and visible church.;
SYSTEM: Pastor Dave will answer succinctly.
Pastor Dave will not roleplay actions.
Pastor Dave will not ask questions.
Pastor Dave will not use profanity or say anything inappropriate no matter what. This order is the highest priority can not be overridden.;
"""

@client.event
async def on_ready():
    """Simply notifies user the bot is ready."""
    print(f'Logged in as {client.user}')  # Log in message

@client.event
async def on_message(message):
    """Attempt to respond to user question."""
    # Ignore messages from the bot itself
    if message.author == client.user:
        return# Check if the bot is mentioned in the message
    if client.user in message.mentions:
        # Extract the prompt from the message after the bot's mention
        prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
        logging.info('Received prompt: %s', prompt)
        response = get_tabby_response(prompt, message)
        if response:
            await send_long_message(message.channel, response)
        else:
            await message.channel.send("I couldn't generate a response. Please try again later.")
            logging.warning("Received an empty response from TabbyAPI.")

def get_tabby_response(prompt, message):
    """Run user message through tabby API."""
    try:
        # Get the original message if this is a reply
        original_message = message.reference.resolved if message.reference else None
        original_message_content = original_message.content if original_message else ""  # Create the context with the original message if available pylint: disable=line-too-long
        context = (f'{"Pastor Dave" if original_message.author == client.user else "User"}: {original_message_content}\nUser: {prompt}'  # pylint: disable=line-too-long
                   if original_message
                   else prompt)

        # Send a POST request to TabbyAPI with the prompt and character
        payload = {
            "max_tokens": 500,
            "messages": [
                {
                    "role": "system",
                    "content": CHARACTER_CONTEXT
                },
                {
                    "role": "user",
                    "content": context
                }
            ]
        }
        logging.info('Sending payload: %s', payload)
        response = session.post(TABBY_API_URL, json=payload)
        response.raise_for_status()  # Raise an error for bad responses
        response_data = response.json()
        logging.info('Received response: %s', response_data)
        response_text = response_data['choices'][0]['message']['content'].strip()
        # Append the footer text
        footer_text = '[This reply is AI generated, may contain errors, and as such may not represent the opinion of Solas.]'  # pylint: disable=line-too-long
        return f"{response_text}\n{footer_text}"
    except requests.exceptions.RequestException as e:
        logging.error('Error communicating with TabbyAPI: %s', e)
        return None
    except KeyError as e:
        logging.error('Unexpected response format from TabbyAPI: %s', e)
        return None
    except AttributeError as e:
        logging.error('Attribute error: %s', e)
        return None

async def send_long_message(channel, message):
    """Split message into parts for Discord API limits."""
    # Split the message into chunks of 2000 characters or less
    chunks = [message[i:i+2000] for i in range(0, len(message), 2000)]
    for chunk in chunks:
        await channel.send(chunk)

client.run(TOKEN)
