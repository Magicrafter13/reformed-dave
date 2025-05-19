"""LLM Prompt Utilities."""

def create_prompt(question: str) -> str:
    """Create a properly formatted prompt for the LLM."""
    return f"""Answer the following theological question as a Reformed pastor. Do not use any tools, functions, or external calls. Respond directly to the query.

Question: {question}
Answer:"""
