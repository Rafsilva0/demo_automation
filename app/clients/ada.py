"""Ada API client for provisioning agents and resources."""

import httpx
import structlog
import re
from typing import Dict, Any, List

from app.config import settings

logger = structlog.get_logger()


class AdaClient:
    """Client for interacting with Ada API."""

    def __init__(self):
        """Initialize Ada API client."""
        self.base_url = settings.ada_api_base_url
        self.headers = {
            "Authorization": f"Bearer {settings.ada_api_key}",
            "Content-Type": "application/json"
        }
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers=self.headers,
            timeout=30.0
        )
        logger.info("ada_client_initialized", base_url=self.base_url)

    async def clone_bot(
        self,
        clone_secret: str,
        new_handle: str,
        email: str = "scteam@ada.support",
        password: str = "Adalovelace123!"
    ):
        """
        Clone bot from template (Step 21).

        Note: This API returns an error but the clone actually works.
        We ignore the error response as instructed by the user.

        Args:
            clone_secret: Secret key for cloning
            new_handle: New bot handle (e.g., "pepsi-ai-agent-demo")
            email: Login email for new bot
            password: Login password for new bot
        """
        logger.info("cloning_bot", new_handle=new_handle)

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://scteam-demo.ada.support/api/clone",
                    json={
                        "clone_secret": clone_secret,
                        "new_handle": new_handle,
                        "email": email,
                        "user_full_name": "Ada SC Team",
                        "user_password": password,
                        "type": "client"
                    },
                    timeout=30.0
                )
                # Don't raise_for_status - user said it errors but works
                logger.info(
                    "clone_bot_api_called",
                    status_code=response.status_code,
                    new_handle=new_handle
                )
            except Exception as e:
                # Log warning but don't fail - clone works despite error
                logger.warning("clone_bot_api_error", error=str(e), new_handle=new_handle)

    async def create_knowledge_source(
        self,
        base_url: str,
        api_key: str,
        source_id: str,
        name: str
    ):
        """
        Create a new knowledge source in Ada (Step 24).

        Args:
            base_url: Bot base URL (e.g., "https://pepsi-ai-agent-demo.ada.support")
            api_key: Bot API key
            source_id: Fixed ID for knowledge source (always "demosource")
            name: Knowledge source name
        """
        logger.info("creating_knowledge_source", source_id=source_id, name=name)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v2/knowledge/sources/",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "id": source_id,
                    "name": name
                },
                timeout=30.0
            )
            response.raise_for_status()
            logger.info("knowledge_source_created", source_id=source_id)

    async def bulk_upload_articles(
        self,
        base_url: str,
        api_key: str,
        articles: List[Dict[str, Any]]
    ):
        """
        Bulk upload knowledge articles (Step 27).

        Args:
            base_url: Bot base URL
            api_key: Bot API key
            articles: List of article objects with id, name, content, knowledge_source_id
        """
        logger.info("bulk_uploading_articles", count=len(articles))

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v2/knowledge/bulk/articles/",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json=articles,
                timeout=60.0
            )

            if not response.is_success:
                error_text = response.text
                raise Exception(
                    f"Ada bulk upsert failed ({response.status_code}): {error_text}"
                )

            logger.info("articles_bulk_uploaded", count=len(articles))
            return {"status": "successful"}

    async def create_endpoint(
        self,
        name: str,
        description: str,
        url: str,
        method: str = "POST",
        headers: Dict[str, str] | None = None
    ) -> str:
        """
        Create an endpoint/action in Ada.

        Args:
            name: Endpoint name
            description: AI-readable description of what the endpoint does
            url: Endpoint URL
            method: HTTP method
            headers: Optional headers

        Returns:
            Endpoint ID
        """
        logger.info("creating_endpoint", name=name, url=url)

        payload = {
            "name": name,
            "description": description,
            "url": url,
            "method": method,
            "headers": headers or {}
        }

        # Placeholder endpoint
        response = await self.client.post(
            "/endpoints",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        endpoint_id = data["id"]

        logger.info("endpoint_created", endpoint_id=endpoint_id, name=name)

        return endpoint_id

    async def create_channel(
        self,
        base_url: str,
        api_key: str,
        name: str,
        description: str
    ) -> str:
        """
        Create a channel in Ada (Step 34).

        Args:
            base_url: Bot base URL
            api_key: Bot API key
            name: Channel name
            description: Channel description

        Returns:
            Channel ID
        """
        logger.info("creating_channel", name=name)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v2/channels/",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={
                    "name": name,
                    "description": description,
                    "modality": "messaging"
                },
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            channel_id = data["id"]

            logger.info("channel_created", channel_id=channel_id, name=name)
            return channel_id

    async def create_conversation(
        self,
        base_url: str,
        api_key: str,
        channel_id: str
    ) -> Dict[str, str]:
        """
        Create a conversation (Step 36).

        Args:
            base_url: Bot base URL
            api_key: Bot API key
            channel_id: Channel ID

        Returns:
            Dict with conversation_id and end_user_id
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v2/conversations/",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={"channel_id": channel_id},
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()

            return {
                "conversation_id": data["id"],
                "end_user_id": data["end_user_id"]
            }

    async def create_message(
        self,
        base_url: str,
        api_key: str,
        conversation_id: str,
        end_user_id: str,
        message_body: str
    ):
        """
        Create a message in conversation (Step 37).

        Args:
            base_url: Bot base URL
            api_key: Bot API key
            conversation_id: Conversation ID (24-char hex)
            end_user_id: End user ID (24-char hex)
            message_body: Message text
        """
        # Validate IDs (24-char hex)
        if not re.match(r'^[a-f0-9]{24}$', conversation_id):
            raise ValueError(f"Invalid conversation_id: {conversation_id}")
        if not re.match(r'^[a-f0-9]{24}$', end_user_id):
            raise ValueError(f"Invalid end_user_id: {end_user_id}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{base_url}/api/v2/conversations/{conversation_id}/messages/",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                },
                json={
                    "author": {
                        "id": end_user_id,
                        "role": "end_user"
                    },
                    "content": {
                        "body": message_body,
                        "type": "text"
                    }
                },
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()

    async def create_conversation_instruction(
        self,
        channel_id: str,
        instruction: str,
        trigger: str | None = None
    ) -> str:
        """
        Create a conversation instruction for a channel.

        Args:
            channel_id: Channel ID
            instruction: Instruction text
            trigger: Optional trigger condition

        Returns:
            Instruction ID
        """
        logger.info(
            "creating_conversation_instruction",
            channel_id=channel_id
        )

        payload = {
            "instruction": instruction,
            "trigger": trigger
        }

        # Placeholder endpoint
        response = await self.client.post(
            f"/channels/{channel_id}/instructions",
            json=payload
        )
        response.raise_for_status()

        data = response.json()
        instruction_id = data["id"]

        logger.info("conversation_instruction_created", instruction_id=instruction_id)

        return instruction_id

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
