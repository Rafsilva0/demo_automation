"""Anthropic Claude API client for content generation."""

import structlog
import anthropic
import os

logger = structlog.get_logger()


class AnthropicClient:
    """Client for interacting with Anthropic Claude API."""

    def __init__(self):
        """Initialize Anthropic client."""
        # Use environment variable or fallback
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

        self.client = anthropic.Anthropic(api_key=api_key)
        logger.info("anthropic_client_initialized")

    async def generate_completion(
        self,
        prompt: str,
        model: str = "claude-sonnet-4-5-20250929",
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        Generate a completion using Claude.

        Args:
            prompt: User prompt
            model: Claude model to use
            temperature: Temperature for generation (0-1)
            max_tokens: Maximum tokens to generate

        Returns:
            Generated text completion
        """
        logger.info("generating_completion_with_claude", prompt_length=len(prompt))

        # Synchronous API call (Anthropic SDK doesn't have async yet)
        message = self.client.messages.create(
            model=model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        completion = message.content[0].text

        logger.info(
            "completion_generated",
            model=model,
            completion_length=len(completion) if completion else 0,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens
        )

        return completion or ""
