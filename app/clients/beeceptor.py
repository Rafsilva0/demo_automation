"""Beeceptor API client for creating mock endpoints."""

import httpx
import structlog

logger = structlog.get_logger()


class BeeceptorClient:
    """Client for Beeceptor API rule creation."""

    def __init__(self):
        """Initialize Beeceptor client."""
        self.endpoint = "ada-demo"
        self.api_url = "https://api.beeceptor.com/api/v1/endpoints/ada-demo/rules"
        self.auth_token = "3db584716ce6764c1004850ee20e610e470aee7cTnwDhrdgQaknDva"

    async def create_rule(self, rule_json: str):
        """
        Create a Beeceptor rule (Steps 32-33).

        Args:
            rule_json: JSON string of Beeceptor rule object

        Returns:
            Rule creation response
        """
        logger.info("creating_beeceptor_rule")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": self.auth_token,
                    "Content-Type": "application/json"
                },
                content=rule_json,  # Already JSON string
                timeout=30.0
            )
            response.raise_for_status()

            data = response.json()
            logger.info(
                "beeceptor_rule_created",
                rule_id=data.get("id")
            )

            return data
