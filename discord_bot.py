#!/usr/bin/env python3
"""Reformed Christian Discord chatbot."""

import asyncio
import json
import logging
import random
import re
import sys
from datetime import datetime
from os import environ
from pathlib import Path

import discord
import requests
import yaml
from dotenv import load_dotenv
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from urllib3.exceptions import InsecureRequestWarning

# Configuration paths
CONFIG_DIR = Path('config')
SETTINGS_FILE = CONFIG_DIR / 'settings.yaml'
ADMINS_FILE = CONFIG_DIR / 'admins.yaml'
CONVERSATION_DIR = Path('conversations')
DEBUG_PROMPT_FILE = Path('debug_prompt.txt')

BLOCKED_PHRASES_FILE = CONFIG_DIR / 'blocked_phrases.txt'
CHARACTER_CONTEXT_FILE = CONFIG_DIR / 'character_context.txt'
SYSTEM_PROMPT_FILE = CONFIG_DIR / 'system_prompt.txt'
ENV_FILE = CONFIG_DIR / '.env'

# Create directories if needed
CONVERSATION_DIR.mkdir(exist_ok=True)

# Load settings
try:
    with open(SETTINGS_FILE, 'r', encoding='utf-8') as _f:
        settings = yaml.safe_load(_f)
        USE_FILE_STORAGE = settings.get('use_file_storage', True)
        MAX_HISTORY_MESSAGES = settings.get('max_history_messages', 20)
        MAX_CONTEXT_CHARS = settings.get('max_context_chars', 16000)
        MAX_API_TOKENS = settings.get('max_api_tokens', 8192)
except FileNotFoundError:
    logging.critical('Missing required file: %s', SETTINGS_FILE)
    sys.exit(1)
except yaml.YAMLError as e:
    logging.critical('Invalid YAML in %s: %s', SETTINGS_FILE, e)
    sys.exit(1)

# Load report channels
try:
    with open(ADMINS_FILE, 'r', encoding='utf-8') as _f:
        channel_data = yaml.safe_load(_f)
        REPORT_CHANNELS = set(channel_data.get('report_channels', []))
except FileNotFoundError:
    logging.warning('No report channels file found, proceeding without reporting')
    REPORT_CHANNELS = set()
except yaml.YAMLError as e:
    logging.error('Invalid report channels format: %s', e)
    REPORT_CHANNELS = set()

# Load environment variables
load_dotenv(ENV_FILE)

# Suppress only the single InsecureRequestWarning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Discord setup
TOKEN = environ.get('DISCORD_BOT_TOKEN')
if not TOKEN:
    logging.critical('DISCORD_BOT_TOKEN not found in environment variables')
    sys.exit(1)

TABBY_API_URL = 'http://127.0.0.1:5000/v1/chat/completions'

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Logging configuration
logging.basicConfig(level=logging.INFO)

def load_text_file(file_path):
    """Load and validate text file content."""
    try:
        with open(file_path, 'r', encoding='utf-8') as _f:
            content = _f.read().strip()
            if not content:
                logging.error('File %s is empty', file_path)
                raise ValueError(f'Empty file: {file_path}')
            return content
    except FileNotFoundError:
        logging.critical('Missing required file: %s', file_path)
        raise
    except Exception as e:
        logging.critical('Error loading %s: %s', file_path, e)
        raise

# Load content files
try:
    BLOCKED_PHRASES = set()
    if BLOCKED_PHRASES_FILE.exists():
        with open(BLOCKED_PHRASES_FILE, 'r', encoding='utf-8') as _f:
            BLOCKED_PHRASES = {line.strip().lower() for line in _f if line.strip()}

    CHARACTER_CONTEXT = load_text_file(CHARACTER_CONTEXT_FILE)
    SYSTEM_PROMPT = load_text_file(SYSTEM_PROMPT_FILE)
except Exception as e:  # TODO: actually handle specific exceptions pylint: disable=broad-exception-caught
    logging.critical('Initialization failed: %s', str(e))
    sys.exit(1)

# HTTP session configuration
session = requests.Session()
retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
session.mount('http://', HTTPAdapter(max_retries=retries))

class ConversationManager:
    """LLM conversation history."""

    def __init__(self, user_id: int):
        """Create empty conversation, and file if requested."""
        self.user_id = user_id
        self.max_context_chars = MAX_CONTEXT_CHARS
        self.file_path = CONVERSATION_DIR / f'user_{user_id}.jsonl' if USE_FILE_STORAGE else None
        self._history = []  # Used for RAM storage

        if USE_FILE_STORAGE and self.file_path.exists():
            with open(self.file_path, 'r', encoding='utf-8') as _f:
                self._history = [json.loads(line) for line in _f]

    def _trim_history(self):
        """Maintain rolling context window."""
        total_chars = 0
        trimmed = []

        # Process from newest to oldest
        for entry in reversed(self._history):
            if total_chars + entry['chars'] > self.max_context_chars:
                break
            total_chars += entry['chars']
            trimmed.append(entry)

        self._history = list(reversed(trimmed))

        if USE_FILE_STORAGE:
            with open(self.file_path, 'w', encoding='utf-8') as _f:
                for entry in self._history:
                    _f.write(json.dumps(entry) + '\n')

    def add_message(self, role: str, content: str):
        """Add message to conversation log."""
        entry = {
            'role': role,
            'content': content,
            'chars': len(content),
            'timestamp': datetime.now().isoformat()
        }

        self._history.append(entry)
        self._trim_history()

    def get_context(self) -> str:
        """Build conversation history."""
        recent_history = self._history[-MAX_HISTORY_MESSAGES:]

        context_lines = []
        for entry in recent_history:
            role = entry['role'].title()
            context_lines.append(f"{role}: {entry['content']}")

        return '\n'.join(context_lines)

    def reset(self):
        """Clear conversation history."""
        self._history = []
        if USE_FILE_STORAGE and self.file_path.exists():
            self.file_path.unlink()

# Dictionary to store ConversationManager instances
conversation_managers = {}

def contains_prohibited_content(text):
    """Check for blocked phrases using regex word boundaries."""
    text_lower = text.lower()
    matches = []
    for phrase in BLOCKED_PHRASES:
        if re.search(rf'\b{re.escape(phrase)}\b', text_lower):
            matches.append(phrase)
    return matches if matches else False

def validate_response(text):
    """Ensure response ends with proper punctuation."""
    if not text.strip():
        return False
    last_char = text.strip()[-1]
    valid_terminators = ('.', '!', '?', '"', "'", ')', ']', '}', ':', '—')
    return last_char in valid_terminators

def write_debug_prompt(prompt_data: str):
    """Write latest prompt to debug file."""
    with open(DEBUG_PROMPT_FILE, 'w', encoding='utf-8') as _f:
        _f.write(prompt_data)

async def notify_mod_channels(
    message: discord.Message,
    blocked_prompt: str,
    blocked_phrases: list,
    response_text: str = None
):
    """Send detailed blocked content report."""
    if not REPORT_CHANNELS:
        return

    report = (
        f'🚨 Blocked content detected\n'
        f'User: {message.author.mention} (`{message.author.id}`)\n'
        f'Channel: {message.channel.mention}\n'
        f'**Original Message:**\n```\n{blocked_prompt}\n```\n'
    )

    if response_text:
        report += f'**Bot Response:**\n```\n{response_text}\n```\n'

    report += (
        f'**Blocked Phrases Detected:**\n'
        f"{', '.join(f'`{phrase}`' for phrase in blocked_phrases)}"
    )

    for channel_id in REPORT_CHANNELS:
        try:
            channel = client.get_channel(int(channel_id))
            if channel and isinstance(channel, discord.TextChannel):
                await channel.send(report)
        except (discord.NotFound, discord.Forbidden) as e:
            logging.error('Failed to send to channel %s: %s', channel_id, e)
        except ValueError:
            logging.error('Invalid channel ID format: %s', channel_id)

@client.event
async def on_ready():
    """Notify successful login."""
    logging.info('Logged in as %s (ID: %s)', client.user, client.user.id)

@client.event
async def on_message(message):
    """Handle incoming messages."""
    if message.author == client.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        logging.warning('Ignoring DM from %s', message.author)
        return

    if client.user in message.mentions:
        prompt = message.content.replace(f'<@{client.user.id}>', '').strip()
        logging.info('Processing prompt: %s', prompt)

        # Handle reset command
        if prompt == 'RESET':
            user_id = message.author.id
            if user_id in conversation_managers:
                conversation_managers[user_id].reset()
                await message.channel.send(
                    "Conversation history reset. "
                    "'Create in me a clean heart, O God...' (Psalm 51:10)"
                )
            else:
                await message.channel.send('No conversation history to reset.')
            return

        # Check for prohibited content before processing
        blocked_phrases = contains_prohibited_content(prompt)
        if blocked_phrases:
            await message.channel.send(
                "I must decline this request. Please consult church leadership. "
                "'The fear of the LORD is the beginning of knowledge...' (Proverbs 1:7)"
            )
            await notify_mod_channels(message, prompt, blocked_phrases)
            return  # Don't add to history

        user_id = message.author.id
        if user_id not in conversation_managers:
            conversation_managers[user_id] = ConversationManager(user_id)

        cm = conversation_managers[user_id]

        # Handle message references
        original_message = message.reference.resolved if message.reference else None
        if original_message:
            prompt = (
                f'{prompt}\n'
                f'(User is replying to this message: {original_message.content})'
            )

        # Add user message to history
        cm.add_message('user', prompt)

        # Build full prompt
        system_prompt = (
            f"STRICT DIRECTIVE: {SYSTEM_PROMPT}\n"
            "IMPERATIVE: Never use terms like 'child', 'son', or similar when addressing users.\n"
            f"{CHARACTER_CONTEXT}"
        )
        full_prompt = (
            f'<s>[SYSTEM_PROMPT]{system_prompt}[/SYSTEM_PROMPT]\n'
            f'### Conversation History:\n{cm.get_context()}\n'
            f'### Current Question:\n[INST]User: {prompt}[/INST]\n'
            f'Pastor Dave:'
        )

        write_debug_prompt(full_prompt)

        # API payload
        messages = [{'role': 'system', 'content': system_prompt}]
        last_role = None

        # Process history ensuring proper alternation
        for msg in cm._history[-MAX_HISTORY_MESSAGES*2:]:  # Double buffer for pruning
            current_role = msg['role']
            if current_role not in ['user', 'assistant']:
                continue

            if last_role == current_role:
                continue

            messages.append({'role': current_role, 'content': msg['content']})
            last_role = current_role

        # Add current prompt ensuring alternation
        if last_role == 'user':
            logging.debug('Unexpected message sequence, pruning last message')
            messages = messages[:-1]

        messages.append({'role': 'user', 'content': prompt})

        payload = {
            'max_tokens': MAX_API_TOKENS,
            'mode': 'chat',
            'messages': messages,
            'character': 'Pastor Dave',
            'temperature': 0.0,
            'repetition_penalty': 1.01,
            'stopping_strings': ['\n', 'User:', 'Pastor Dave:']
        }

        # API request
        try:
            response = session.post(TABBY_API_URL, json=payload)
            response.raise_for_status()
            response_data = response.json()
            response_text = response_data['choices'][0]['message']['content'].strip()
            response_text = response_text.removeprefix('Pastor Dave: ')

            # Post-process to remove prohibited terms
            cleaned_response = re.sub(
                r'\b(child|son|my dear)\b',
                '',
                response_text,
                flags=re.IGNORECASE
            ).strip()

            # Check response for blocked content
            response_blocked = contains_prohibited_content(cleaned_response)
            if response_blocked:
                logging.warning('Blocked response content')
                await notify_mod_channels(message, prompt, response_blocked, response_text)
                return  # Don't add to history

            if not validate_response(cleaned_response):
                logging.warning('Incomplete response ending with: %s', cleaned_response[-20:])
                return

            # Add bot response to history
            cm.add_message('assistant', cleaned_response)

            footer_text = '[This reply is AI generated, may contain errors, and as such may not represent the opinion of Solas.]'  # pylint: disable=line-too-long
            await send_long_message(message.channel, cleaned_response, footer_text)

        except requests.exceptions.RequestException as e:
            logging.error('API communication error: %s', e)
            await message.channel.send('Response generation failed. Please try again.')
        except KeyError as e:
            logging.error('API response format error: %s', e)
            await message.channel.send('Response format error. Please try again.')

async def send_long_message(channel, response_text, footer_text):
    """Handle message splitting with footer."""
    max_chunk = 1990

    chunks = []
    while response_text:
        if len(response_text) <= max_chunk:
            chunks.append(response_text)
            break

        lookback_start = max(0, max_chunk - 100)
        window = response_text[lookback_start:max_chunk]

        split_candidates = [
            ('\n\n', 2),
            ('. ', 2),
            ('; ', 2),
            (', ', 2),
            (' ', 1)
        ]

        split_at = None
        for marker, offset in split_candidates:
            pos = window.rfind(marker)
            if pos != -1:
                split_at = lookback_start + pos + offset
                break

        if split_at and split_at > 0:
            chunks.append(response_text[:split_at])
            response_text = response_text[split_at:].lstrip()
        else:
            chunks.append(response_text[:max_chunk])
            response_text = response_text[max_chunk:]

    # Send chunks with random delays
    for index, chunk in enumerate(chunks):
        await channel.send(chunk)
        if index < len(chunks) - 1:
            await asyncio.sleep(random.uniform(1.5, 2.5))

    # Send footer
    await channel.send(footer_text)

if __name__ == '__main__':
    client.run(TOKEN)
