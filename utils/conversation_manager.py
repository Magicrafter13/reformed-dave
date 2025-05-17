"""Manages conversation history for the bot."""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Dict


@dataclass
class Message:
    """Discord chat message."""

    role: str
    content: str
    timestamp: datetime


class ConversationManager:
    """Manages a client's conversation history."""

    def __init__(self, max_messages: int = 12, max_age_minutes: int = 120):
        """Clear conversation history."""
        self.conversations: Dict[str, List[Message]] = {}
        self.max_messages = max_messages
        self.max_age = timedelta(minutes=max_age_minutes)

    def add_message(self, channel_id: str, role: str, content: str) -> List[Dict[str, str]]:
        """Add a message to the conversation history and return the full conversation."""
        if channel_id not in self.conversations:
            self.conversations[channel_id] = []
            print(f"\nInitializing new conversation for channel {channel_id}")
        else:
            print(f"\nAdding to existing conversation in channel {channel_id} (current size: {len(self.conversations[channel_id])})")  # pylint: disable=line-too-long

        # Add the new message
        message = Message(role=role, content=content, timestamp=datetime.now())
        self.conversations[channel_id].append(message)
        print(f"Added {role} message, length: {len(content)} chars")

        # Trim old messages
        self._cleanup_conversation(channel_id)
        print(f"After cleanup: {len(self.conversations[channel_id])} messages in conversation")

        # Return the updated conversation history
        return self.get_conversation(channel_id)

    def get_conversation(self, channel_id: str) -> List[Dict[str, str]]:
        """Get conversation history formatted for API."""
        if channel_id not in self.conversations:
            print(
                f"\nNo existing conversation for channel {channel_id}, returning system prompt only"
            )
            return [{"role": "system", "content": self._get_system_prompt()}]

        # Clean up old messages first
        self._cleanup_conversation(channel_id)

        # Start with system message
        conversation = [{
            "role": "system",
            "content": self._get_system_prompt()
        }]
        print(f"\nBuilding conversation for channel {channel_id}")
        print(f"Starting with system prompt ({len(self._get_system_prompt())} chars)")

        # Add conversation history
        for idx, msg in enumerate(self.conversations[channel_id], 1):
            if not msg.content.strip():
                print(f"Skipping empty message at position {idx}")
                continue
            print(f"Adding message {idx}: {msg.role} ({len(msg.content)} chars)")
            conversation.append({"role": msg.role, "content": msg.content})

        print(f"Final conversation has {len(conversation)} messages")
        return conversation

    def _get_system_prompt(self) -> str:
        """Get the system prompt for the Reformed Pastor bot."""
        try:
            with open("config/system_prompt.txt", "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error reading system prompt: {e}")
            return "You are a Reformed Pastor holding to the Westminster Standards."

    def _cleanup_conversation(self, channel_id: str):
        """Remove old messages and limit conversation size."""
        if channel_id not in self.conversations:
            return

        original_size = len(self.conversations[channel_id])
        current_time = datetime.now()

        # Remove messages older than max_age
        self.conversations[channel_id] = [
            msg
            for msg in self.conversations[channel_id]
            if (current_time - msg.timestamp) <= self.max_age
        ]

        # Keep only the most recent messages up to max_messages
        if len(self.conversations[channel_id]) > self.max_messages:
            self.conversations[channel_id] = self.conversations[channel_id][-self.max_messages:]

        if original_size != len(self.conversations[channel_id]):
            print(f"Cleaned up conversation: {original_size} -> {len(self.conversations[channel_id])} messages")  # pylint: disable=line-too-long

    def clear_conversation(self, channel_id: str):
        """Clear the conversation history for a channel."""
        if channel_id in self.conversations:
            print(f"\nClearing conversation history for channel {channel_id}")
            del self.conversations[channel_id]
