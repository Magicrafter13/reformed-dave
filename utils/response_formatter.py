"""LLM Response Formatting Tools."""

import re
import asyncio
import random

def strip_think_tags(text: str) -> str:
    """Remove content between <think> and </think> tags."""
    # Match everything between and including <think> and </think> tags
    cleaned_text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # In case there are any orphaned tags, remove them too
    cleaned_text = re.sub(r'<think>.*', '', cleaned_text, flags=re.DOTALL)
    cleaned_text = re.sub(r'</think>', '', cleaned_text)
    return cleaned_text.strip()

def split_into_chunks(text: str, chunk_size: int) -> list[str]:
    """Split text into chunks of specified size at sentence boundaries."""
    chunks = []
    current_chunk = ""
    
    sentences = re.split(r'([.!?][\s\n]+)', text)
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += sentence
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence
            
    if current_chunk:
        chunks.append(current_chunk.strip())
        
    return chunks

async def format_response(response: str) -> list[str]:
    """
    Format the LLM response and handle long messages.

    Returns a list of formatted strings for sequential sending
    """
    # Strip any think tags from the response first
    response = strip_think_tags(response)

    if not response.strip():
        return ["I seem to be having trouble formulating a response. Could you please rephrase your question?"]

    # Add disclaimer footer
    disclaimer = "\n\n⚠️ *AI-generated response - Please verify with the Bible and your Elders*"

    # Maximum size for each chunk (leaving room for continuation marks and disclaimer)
    MAX_CHUNK_SIZE = 1900

    # If response plus disclaimer fits in one message, return it as is
    if len(response) + len(disclaimer) <= MAX_CHUNK_SIZE:
        return [f"{response.strip()}{disclaimer}"]

    # Split into chunks
    chunks = split_into_chunks(response, MAX_CHUNK_SIZE - 50)  # Leave room for markers
    formatted_chunks = []

    # Format chunks, adding disclaimer only to last chunk
    for i, chunk in enumerate(chunks):
        if i == len(chunks) - 1:
            formatted_chunks.append(f"{chunk.strip()}{disclaimer}")
        else:
            formatted_chunks.append(chunk.strip())

    return formatted_chunks
