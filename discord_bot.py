#!/usr/bin/env python3
"""Reformed Christian Discord chatbot."""

import asyncio
import os
import random
import traceback
from datetime import datetime

import discord
from discord.ext import commands
from dotenv import load_dotenv
from openai import OpenAI

from config import (
    BOT_PERMISSIONS,
    COMMAND_PREFIX,
    ENABLE_PROMPT_LOGGING,
    HELP_MESSAGE,
    MAX_PROMPT_LENGTH,
    MAX_RETRIES,
    MONITORING_CHANNEL_ID,
    PROMPT_LOG_FILE,
    TIMEOUT_SECONDS
)
from utils.prompt_handler import create_prompt
from utils.response_formatter import format_response
from utils.conversation_manager import ConversationManager
from utils.content_filter import load_blocked_phrases, contains_blocked_phrase
from config import BOT_PERMISSIONS, COMMAND_PREFIX, HELP_MESSAGE, MAX_RETRIES, TIMEOUT_SECONDS

# Initialize conversation manager
conversation_manager = ConversationManager()

# Load environment variables and blocked phrases
blocked_phrases = load_blocked_phrases()
load_dotenv()

# Initialize Discord bot with explicit intents
intents = discord.Intents.default()
intents.message_content = True
intents.guild_messages = True
intents.guilds = True
intents.guild_reactions = True
bot = commands.Bot(
    command_prefix=COMMAND_PREFIX,
    intents=intents,
    help_command=None  # Disable default help command to avoid conflicts
)

# Initialize OpenAI client with TabbyAPI endpoint
client = OpenAI(
    base_url="http://127.0.0.1:5000/v1",
    api_key=os.getenv('TABBYAPI_KEY')  # TabbyAPI doesn't require an API key
)

@bot.event
async def on_ready():
    """Event handler for when the bot is ready."""
    print(f'Bot is ready! Logged in as {bot.user.name}')
    print(f'Bot ID: {bot.user.id}')
    print('Prefix:', COMMAND_PREFIX)

    # Generate bot invite link with required permissions
    invite_link = discord.utils.oauth_url(
        bot.user.id,
        permissions=discord.Permissions(BOT_PERMISSIONS)
    )
    print(f'Invite Link: {invite_link}')
    print('------')

@bot.event
async def on_guild_join(guild):
    """Event handler for when the bot joins a new server."""
    # Check bot permissions in the guild
    me = guild.me
    missing_permissions = []

    if not me.guild_permissions.send_messages:
        missing_permissions.append("Send Messages")
    if not me.guild_permissions.read_messages:
        missing_permissions.append("Read Messages")
    if not me.guild_permissions.embed_links:
        missing_permissions.append("Embed Links")
    if not me.guild_permissions.read_message_history:
        missing_permissions.append("Read Message History")
    if not me.guild_permissions.view_audit_log:
        missing_permissions.append("View Audit Log")

    if missing_permissions:
        print(f"Warning: Missing permissions in {guild.name}: {', '.join(missing_permissions)}")
        try:
            # Try to notify the server owner about missing permissions
            system_channel = guild.system_channel
            if system_channel and system_channel.permissions_for(me).send_messages:
                await system_channel.send(
                    f"⚠️ Warning: I'm missing some required permissions: {', '.join(missing_permissions)}. "
                    "Please ensure I have the correct permissions to function properly."
                )
        except Exception as e:
            print(f"Could not notify about missing permissions: {e!s}")



@bot.command(name='reset')
@commands.has_permissions(administrator=True)  # This ensures only server admins can use the command
async def reset_context(ctx):
    """Reset the client context and conversation history (Admin only)."""
    try:
        conversation_manager.clear_conversation(str(ctx.channel.id))
        print(f"Admin {ctx.author} ({ctx.author.id}) reset context in channel {ctx.channel.name}")
        await ctx.reply("✝️ Context has been reset, brother/sister! Ready for new questions. 🙏")
    except commands.MissingPermissions:
        print(f"Non-admin user {ctx.author} ({ctx.author.id}) attempted to use reset command")
        await ctx.send("⚠️ Sorry brother/sister, only administrators can use this command.")
    except Exception as e:
        error_msg = f"Error resetting context: {e!s}"
        print(f"Error during reset by {ctx.author} ({ctx.author.id}): {error_msg}")
        print(traceback.format_exc())
        await ctx.reply("Sorry brother/sister, there was an error resetting the context. Please try again.")

# Track processed messages
processed_messages = set()

@bot.event
async def on_message(message):
    """Event handler for when a message is received."""
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return

    # Check if message was already processed
    if message.id in processed_messages:
        return

    # Mark message as processed
    processed_messages.add(message.id)

    print(f"\nReceived message: {message.content[:100]}...")
    print(f"Author: {message.author}, Channel: {message.channel.name}")

    # Handle commands first
    if message.content.startswith(COMMAND_PREFIX):
        print(f"Processing command: {message.content}")
        await bot.process_commands(message)
        return

    # Handle non-prefix reset command
    if message.content.lower() == "reset":
        print("Processing text reset command")
        await handle_text_reset(message)
        return

    # Skip if message contains a command even if mentioned
    if any(message.content.lower().startswith(f"{COMMAND_PREFIX}{cmd}") for cmd in ['ask', 'about', 'reset']):
        return

    # Process mentions and replies
    is_reply_to_bot = message.reference and message.reference.resolved and message.reference.resolved.author == bot.user
    was_mentioned = bot.user in message.mentions

    if is_reply_to_bot or was_mentioned:
        print("Processing mention/reply")
        question = message.content.replace(f'<@{bot.user.id}>', '').strip()
        if not question:
            await message.reply("I don't see a question in your message. Please ask me something about the Bible or theology.")
            return
        await process_question(message, question)

async def handle_text_reset(message):
    """Handle the text-based reset command."""
    if message.guild and message.author.guild_permissions.administrator:
        try:
            conversation_manager.clear_conversation(str(message.channel.id))
            print(f"Admin {message.author} ({message.author.id}) reset context via text command")
            await message.reply("✝️ Context has been reset, brother/sister! Ready for new questions. 🙏")
        except Exception as e:
            error_msg = f"Error resetting context: {e!s}"
            print(f"Error during text reset by {message.author} ({message.author.id}): {error_msg}")
            print(traceback.format_exc())
            await message.reply("Sorry brother/sister, there was an error resetting the context. Please try again.")
    else:
        print(f"Non-admin user {message.author} ({message.author.id}) attempted to use text reset command")
        await message.reply("⚠️ Sorry brother/sister, only administrators can use this command.")

async def process_question(message, question):
    """Process questions through TabbyAPI."""
    try:
        # Check input for blocked phrases
        has_blocked, blocked_sentence, blocked_phrase = contains_blocked_phrase(question, blocked_phrases)
        if has_blocked:
            await message.reply("⚠️ Your message contains blocked content. Please rephrase your question.")
            if MONITORING_CHANNEL_ID:
                monitoring_channel = bot.get_channel(MONITORING_CHANNEL_ID)
                if monitoring_channel:
                    await monitoring_channel.send(f"⚠️ Blocked phrase detected in message from {message.author}:\nPhrase: `{blocked_phrase}`\nContext: ```{blocked_sentence}```")
            return

        channel_id = str(message.channel.id)
        print(f"\nProcessing question for channel {channel_id}")
        print(f"Message author: {message.author}")

        async with message.channel.typing():
            prompt = create_prompt(question)
            print(f"\nProcessing question: {question}")
            completion = None

            for attempt in range(MAX_RETRIES):
                try:
                    print(f"\nAttempt {attempt + 1}: Sending request to TabbyAPI")

                    # Get conversation history including system message
                    messages = conversation_manager.get_conversation(channel_id)

                    # Debug log the conversation state
                    print(f"\nCurrent conversation state:")
                    for idx, msg in enumerate(messages):
                        print(f"Message {idx}: {msg['role']} - First 100 chars: {msg['content'][:100]}...")

                    # Get user's gender role
                    gender = None
                    for role in message.author.roles:
                        if role.name.lower() == "male":
                            gender = "male"
                            break
                        elif role.name.lower() == "female":
                            gender = "female"
                            break

                    # Add current question with gender context
                    gender_context = f"[User is {gender}] " if gender else ""
                    messages.append({"role": "user", "content": f"{gender_context}{prompt}"})

                    # Print conversation context for debugging
                    print(f"\nSending conversation with {len(messages)} messages")

                    # Calculate total prompt length
                    total_length = sum(len(msg['content']) for msg in messages)
                    if total_length > MAX_PROMPT_LENGTH:
                        # Remove oldest messages until within limit
                        while total_length > MAX_PROMPT_LENGTH and len(messages) > 2:  # Keep system and latest
                            removed = messages.pop(1)  # Remove second message (after system)
                            total_length -= len(removed['content'])
                        print(f"Trimmed conversation to {len(messages)} messages to meet length limit")

                    # Log prompt if enabled
                    if ENABLE_PROMPT_LOGGING:
                        try:
                            with open(PROMPT_LOG_FILE, "a") as f:
                                f.write(f"\n--- Prompt at {datetime.now().isoformat()} ---\n")
                                for msg in messages:
                                    f.write(f"\n[{msg['role']}]\n{msg['content']}\n")
                                f.write("\n--------------------\n")
                        except Exception as e:
                            print(f"Error logging prompt: {e}")

                    completion = await asyncio.wait_for(
                        asyncio.to_thread(
                            client.chat.completions.create,
                            model="Reformed-Christian-Bible-Expert-v2.1-12B_EXL2_4.5bpw_H8",
                            messages=messages,
                            temperature=0.0,  # Set to 0 for deterministic output
                            max_tokens=15872,
                            top_p=1.0,  # Set to 1.0 to disable nucleus sampling
                            frequency_penalty=0.0,  # Disable frequency penalty
                            presence_penalty=0.0  # Disable presence penalty
                        ),
                        timeout=TIMEOUT_SECONDS
                    )

                    if completion and hasattr(completion, 'choices') and completion.choices:
                        content = completion.choices[0].message.content
                        if content and content.strip():
                            # Store both the prompt and response in conversation history
                            conversation_manager.add_message(channel_id, "user", prompt)
                            conversation_manager.add_message(channel_id, "assistant", content)
                            print(f"\nStored in conversation history:")
                            print(f"User: {prompt[:100]}...")
                            print(f"Assistant: {content[:100]}...")
                            break
                        else:
                            print("Error: Empty content in response")
                            raise Exception("Empty response from API")
                    else:
                        print(f"Error: Invalid completion structure: {completion}")
                        raise Exception("Invalid API response structure")

                    if attempt == MAX_RETRIES - 1:
                        raise Exception("Failed to get valid response after all attempts")

                except asyncio.TimeoutError:
                    print(f"Timeout on attempt {attempt + 1}")
                    if attempt == MAX_RETRIES - 1:
                        raise
                    await asyncio.sleep(1)
                except Exception as e:
                    print(f"TabbyAPI Error (Attempt {attempt + 1}/{MAX_RETRIES}): {e!s}")
                    print(traceback.format_exc())
                    if attempt == MAX_RETRIES - 1:
                        raise
                    await asyncio.sleep(1)

            if completion and hasattr(completion, 'choices') and completion.choices[0].message.content.strip():
                response_chunks = await format_response(completion.choices[0].message.content)
                if response_chunks:
                    # Check output for blocked phrases
                    has_blocked = False
                    for chunk in response_chunks:
                        chunk_blocked, blocked_sentence, blocked_phrase = contains_blocked_phrase(chunk, blocked_phrases)
                        if chunk_blocked:
                            has_blocked = True
                            break

                    if has_blocked:
                        await message.reply("⚠️ Generated response contained blocked content. Please try rephrasing your question.")
                        if MONITORING_CHANNEL_ID:
                            monitoring_channel = bot.get_channel(MONITORING_CHANNEL_ID)
                            if monitoring_channel:
                                await monitoring_channel.send(f"⚠️ Blocked phrase detected in bot response to {message.author}:\nPhrase: `{blocked_phrase}`\nContext: ```{blocked_sentence}```")
                        return

                    # Send chunks with random delays
                    for i, chunk in enumerate(response_chunks):
                        print(f"\nSending response chunk {i+1}/{len(response_chunks)}, length: {len(chunk)}")
                        print(f"First 100 chars: {chunk[:100]}...")
                        if i == 0:
                            await message.reply(chunk)
                        else:
                            await asyncio.sleep(random.uniform(1, 2))
                            await message.channel.send(chunk)
                else:
                    raise Exception("Empty formatted response")
            else:
                raise Exception("Failed to get valid completion after all retries")

    except asyncio.TimeoutError:
        # Get user's gender role
        gender = "brother/sister"
        for role in message.author.roles:
            if role.name.lower() == "male":
                gender = "brother"
                break
            elif role.name.lower() == "female":
                gender = "sister"
                break

        error_message = f"Sorry, {gender}, the response took too long. Please try asking your question again."
        await message.reply(error_message)
        print(f"Timeout while processing question: {question}")
    except Exception as e:
        # Get user's gender role
        gender = "brother/sister"
        for role in message.author.roles:
            if role.name.lower() == "male":
                gender = "brother"
                break
            elif role.name.lower() == "female":
                gender = "sister"
                break

        error_message = f"Sorry, {gender}, I'm experiencing some technical difficulties. Please try again later."
        await message.reply(error_message)
        print(f"Error processing question: {e!s}")
        print(traceback.format_exc())

@bot.command(name='ask')
async def ask_theological_question(ctx, *, question: str):
    """
    Handle theological questions and respond in Pastor style.

    Usage: !ask <your theological question>
    """
    print(f"\nProcessing !ask command from {ctx.author}")
    print(f"Question: {question[:100]}...")

    # Check if this is a duplicate command processing
    if hasattr(ctx.message, '_command_processed'):
        print("Skipping duplicate command processing")
        return

    # Mark the message as processed
    setattr(ctx.message, '_command_processed', True)
    await process_question(ctx, question)

@bot.command(name='about')
async def about_command(ctx):
    """Display help information about the bot."""
    await ctx.send(HELP_MESSAGE)

@bot.event
async def on_command_error(ctx, error):
    """Global error handler for bot commands."""
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("⚠️ Sorry brother/sister, you don't have permission to use this command. Only administrators can use it.")
    elif isinstance(error, commands.CommandNotFound):
        return
        #await ctx.send("Brother/Sister, I don't recognize that command. Please use !about for guidance.")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Please provide a question after the !ask command.")
    elif isinstance(error, commands.PrivilegedIntentsRequired):
        await ctx.send(
            "🚨 **Message Content Intent Not Enabled**\n\n"
            "The bot requires Message Content Intent to be enabled in the Discord Developer Portal. "
            "Please follow these steps:\n"
            "1. Go to https://discord.com/developers/applications\n"
            "2. Select your bot application\n"
            "3. Click on 'Bot' in the left sidebar\n"
            "4. Enable 'Message Content Intent' under 'Privileged Gateway Intents'\n"
            "5. Save your changes\n\n"
            "Once done, the bot will need to be restarted."
        )
    else:
        await ctx.send(f"An error occurred: {error!s}")
        # Log the error for debugging
        print(f"Command error: {error!s}")

def run_bot():
    """Run the Discord bot."""
    token = os.getenv('DISCORD_TOKEN')
    if not token:
        raise ValueError("No Discord token found. Please set the DISCORD_TOKEN environment variable.")
    bot.run(token)

if __name__ == "__main__":
    try:
        run_bot()  # Run the Discord bot
    except Exception as e:
        print(f"Bot error: {e}")
