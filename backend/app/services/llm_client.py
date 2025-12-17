import logging
import json
from typing import Optional
from openai import AsyncOpenAI, OpenAIError, APITimeoutError, RateLimitError
import asyncio

from app.core.config import settings

logger = logging.getLogger(__name__)


class LLMClient:
    """
    Safe LLM client wrapper with timeout, retry, and error handling

    Supports: OpenAI GPT models
    Future: Can extend to support Anthropic, Google, etc.
    """

    def __init__(self):
        """Initialize LLM client with configuration from settings"""
        if not settings.OPENAI_API_KEY:
            logger.warning("OPENAI_API_KEY not set - LLM features will fail")

        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=settings.LLM_TIMEOUT_SECONDS
        )
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.max_retries = settings.LLM_MAX_RETRIES

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str
    ) -> dict:
        """
        Generate JSON response from LLM with retry logic

        Args:
            system_prompt: System/instruction prompt
            user_prompt: User message with context

        Returns:
            dict: Parsed JSON response from LLM

        Raises:
            ValueError: If response is not valid JSON
            RuntimeError: If LLM request fails after retries
            TimeoutError: If request times out
        """
        for attempt in range(self.max_retries + 1):
            try:
                logger.info(
                    f"LLM request attempt {attempt + 1}/{self.max_retries + 1}",
                    extra={"model": self.model}
                )

                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    response_format={"type": "json_object"}  # Force JSON output
                )

                # Extract content
                content = response.choices[0].message.content

                if not content:
                    raise ValueError("LLM returned empty response")

                # Parse JSON strictly
                try:
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from LLM: {str(e)}")
                    raise ValueError(f"LLM response is not valid JSON: {str(e)}")

                logger.info(
                    "LLM request successful",
                    extra={
                        "model": self.model,
                        "tokens_used": response.usage.total_tokens if response.usage else None
                    }
                )

                return result

            except APITimeoutError as e:
                logger.warning(f"LLM request timeout (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries:
                    raise TimeoutError(f"LLM request timed out after {self.max_retries + 1} attempts")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

            except RateLimitError as e:
                logger.warning(f"LLM rate limit hit (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"LLM rate limit exceeded after {self.max_retries + 1} attempts")
                await asyncio.sleep(2 ** (attempt + 1))  # Longer backoff for rate limits

            except OpenAIError as e:
                logger.error(f"LLM API error (attempt {attempt + 1}): {str(e)}")
                if attempt == self.max_retries:
                    raise RuntimeError(f"LLM API error: {str(e)}")
                await asyncio.sleep(2 ** attempt)

            except Exception as e:
                logger.error(f"Unexpected error in LLM request: {str(e)}")
                raise RuntimeError(f"Unexpected LLM error: {str(e)}")

        # Should never reach here due to raises above, but safety fallback
        raise RuntimeError("LLM request failed after all retries")
