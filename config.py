"""Example Discord Bot Configuration."""

# Bot configuration
COMMAND_PREFIX = "!"
MONITORING_CHANNEL_ID = None  # Replace with your monitoring channel ID (as integer)

# Prompt Configuration
ENABLE_PROMPT_LOGGING = True  # Set to True to log prompts
PROMPT_LOG_FILE = "prompt_logs.txt"  # Path to prompt log file
MAX_PROMPT_LENGTH = 55000  # Maximum length of the entire prompt in characters

# Required Bot Permissions Integer
BOT_PERMISSIONS = 114816

# API Configuration
MAX_RETRIES = 3
TIMEOUT_SECONDS = 30

# Help message
HELP_MESSAGE = """
🙏 **Reformed Pastor Bot Help** 🙏

Commands:
- `!ask <question>`: Ask a theological question
- `!about`: Display this help message
- `!reset`: Reset conversation context (Admin only)

Examples:
- `!ask What does the Bible say about election?`
- `!ask How should we understand covenant theology?`

As a Reformed Pastor, I'll provide Biblical answers based on:
- Westminster Standards
- Reformed Biblical Interpretation
- Reformed distinctives:
  • The Doctrines of Grace (TULIP)
  • Covenant Theology
  • Biblical Authority and Sufficiency
  • Infant Baptism
  • Presbyterian polity
- Reformed systematic theology

Required Permissions:
- Send Messages
- Read Messages/View Channels
- Send Messages in Threads
- Embed Links
- Read Message History

Note: Some commands require Administrator permissions.

Soli Deo Gloria!
"""
