"""Ada agent building and configuration service."""

import structlog
from typing import List, Dict, Any

from app.clients.ada import AdaClient
from app.clients.openai_client import OpenAIClient

logger = structlog.get_logger()


class AgentBuilder:
    """Service for building and configuring Ada agents."""

    def __init__(self, ada_client: AdaClient, openai_client: OpenAIClient):
        """
        Initialize agent builder.

        Args:
            ada_client: Ada API client
            openai_client: OpenAI API client
        """
        self.ada = ada_client
        self.openai = openai_client

    async def create_endpoints(
        self,
        endpoints: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Create endpoints/actions in Ada.

        This corresponds to Zapier steps 22-23:
        - Step 22: Webhooks - Create Endpoint AI Description
        - Step 23: Webhooks - Create Endpoint All Subscription

        Args:
            endpoints: List of endpoint configurations

        Returns:
            List of created endpoint IDs

        TODO: Update with actual webhook details from Zapier steps 22-23
        """
        logger.info("creating_endpoints", count=len(endpoints))

        endpoint_ids = []

        for endpoint_config in endpoints:
            endpoint_id = await self.ada.create_endpoint(
                name=endpoint_config["name"],
                description=endpoint_config["description"],
                url=endpoint_config["url"],
                method=endpoint_config.get("method", "POST"),
                headers=endpoint_config.get("headers")
            )
            endpoint_ids.append(endpoint_id)

        logger.info("endpoints_created", count=len(endpoint_ids))

        return endpoint_ids

    async def create_channel(
        self,
        account_name: str,
        channel_type: str = "web"
    ) -> str:
        """
        Create a channel in Ada.

        This corresponds to Zapier step 24: Looping - Create a Channel

        Args:
            account_name: Customer account name
            channel_type: Type of channel to create

        Returns:
            Channel ID

        TODO: Update with details from Zapier step 24
        """
        logger.info(
            "creating_channel",
            account_name=account_name,
            channel_type=channel_type
        )

        channel_name = f"{account_name} - {channel_type.title()}"

        channel_id = await self.ada.create_channel(
            name=channel_name,
            type=channel_type
        )

        logger.info("channel_created", channel_id=channel_id, account_name=account_name)

        return channel_id

    async def setup_conversations(
        self,
        channel_id: str,
        conversation_configs: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Setup conversation instructions for a channel.

        This corresponds to Zapier steps 25-27:
        - Step 25: Looping - Loop TK/Items
        - Step 26: Looping - Create Conversations/Instructions
        - Step 27: Looping - Create Messages

        Args:
            channel_id: Channel ID
            conversation_configs: List of conversation configurations

        Returns:
            List of created instruction IDs

        TODO: Update with details from Zapier steps 25-27
        """
        logger.info(
            "setting_up_conversations",
            channel_id=channel_id,
            count=len(conversation_configs)
        )

        instruction_ids = []

        for config in conversation_configs:
            instruction_id = await self.ada.create_conversation_instruction(
                channel_id=channel_id,
                instruction=config["instruction"],
                trigger=config.get("trigger")
            )
            instruction_ids.append(instruction_id)

        logger.info(
            "conversations_setup_complete",
            channel_id=channel_id,
            count=len(instruction_ids)
        )

        return instruction_ids

    async def generate_cli_commands(
        self,
        channel_id: str,
        account_name: str
    ) -> str:
        """
        Generate CLI commands for SC team.

        This corresponds to Zapier step 30: Code (JS) - Send CLI to SC

        Args:
            channel_id: Created channel ID
            account_name: Customer account name

        Returns:
            CLI commands/instructions for SC team

        TODO: Replace with actual JavaScript code from Zapier step 30
        """
        logger.info(
            "generating_cli_commands",
            channel_id=channel_id,
            account_name=account_name
        )

        # Placeholder - actual logic from Zapier step 30 needed
        cli_commands = f"""
        # Ada Agent Setup Complete for {account_name}

        Channel ID: {channel_id}

        Next steps for SC team:
        1. Review agent configuration
        2. Test conversation flows
        3. Deploy to production

        # Quick access commands:
        ada channel view {channel_id}
        ada channel test {channel_id}
        """

        logger.info("cli_commands_generated")

        return cli_commands
