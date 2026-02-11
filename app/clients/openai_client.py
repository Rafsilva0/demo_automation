"""OpenAI API client for content generation."""

import structlog
from openai import AsyncOpenAI
from typing import List, Dict, Any

from app.config import settings

logger = structlog.get_logger()


class OpenAIClient:
    """Client for interacting with OpenAI API."""

    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.temperature = settings.openai_temperature
        logger.info(
            "openai_client_initialized",
            model=self.model,
            temperature=self.temperature
        )

    async def generate_completion(
        self,
        prompt: str,
        system_message: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        model: str | None = None
    ) -> str:
        """
        Generate a completion using OpenAI.

        Supports both chat models (gpt-4, gpt-3.5-turbo) and completion models (gpt-3.5-turbo-instruct).

        Args:
            prompt: User prompt
            system_message: Optional system message for context (chat models only)
            temperature: Optional temperature override
            max_tokens: Optional max tokens override
            model: Optional model override (defaults to settings.openai_model)

        Returns:
            Generated text completion
        """
        logger.info("generating_completion", prompt_length=len(prompt))

        target_model = model or self.model

        # Use legacy completions API for gpt-3.5-turbo-instruct
        if target_model == "gpt-3.5-turbo-instruct":
            response = await self.client.completions.create(
                model=target_model,
                prompt=prompt,
                temperature=temperature or self.temperature,
                max_tokens=max_tokens or 1000
            )
            completion = response.choices[0].text

            logger.info(
                "completion_generated",
                model=target_model,
                completion_length=len(completion) if completion else 0,
                tokens_used=response.usage.total_tokens if response.usage else 0
            )

            return completion or ""

        # Use chat completions API for other models
        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        response = await self.client.chat.completions.create(
            model=target_model,
            messages=messages,
            temperature=temperature or self.temperature,
            max_tokens=max_tokens
        )

        completion = response.choices[0].message.content

        logger.info(
            "completion_generated",
            model=target_model,
            completion_length=len(completion) if completion else 0,
            tokens_used=response.usage.total_tokens if response.usage else 0
        )

        return completion or ""

    async def generate_structured_completion(
        self,
        prompt: str,
        system_message: str | None = None,
        response_format: Dict[str, Any] | None = None
    ) -> str:
        """
        Generate a structured completion (e.g., JSON) using OpenAI.

        Args:
            prompt: User prompt
            system_message: Optional system message
            response_format: Optional response format specification

        Returns:
            Generated structured completion
        """
        logger.info("generating_structured_completion", prompt_length=len(prompt))

        messages = []
        if system_message:
            messages.append({"role": "system", "content": system_message})
        messages.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)

        completion = response.choices[0].message.content

        logger.info(
            "structured_completion_generated",
            completion_length=len(completion) if completion else 0
        )

        return completion or ""

    async def generate_batch_completions(
        self,
        prompts: List[str],
        system_message: str | None = None
    ) -> List[str]:
        """
        Generate multiple completions in parallel.

        Args:
            prompts: List of prompts
            system_message: Optional system message for all prompts

        Returns:
            List of completions in the same order as prompts
        """
        logger.info("generating_batch_completions", count=len(prompts))

        import asyncio
        tasks = [
            self.generate_completion(prompt, system_message)
            for prompt in prompts
        ]

        completions = await asyncio.gather(*tasks)

        logger.info("batch_completions_generated", count=len(completions))

        return completions
