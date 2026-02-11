"""Slack API client for notifications."""

import httpx
import structlog
from typing import Dict, Any

from app.config import settings

logger = structlog.get_logger()


class SlackClient:
    """Client for sending Slack notifications."""

    def __init__(self):
        """Initialize Slack client."""
        self.webhook_url = settings.slack_webhook_url
        self.channel = settings.slack_channel
        self.client = httpx.AsyncClient(timeout=10.0)
        logger.info("slack_client_initialized", channel=self.channel)

    async def send_message(
        self,
        text: str,
        blocks: list[Dict[str, Any]] | None = None,
        channel: str | None = None
    ) -> None:
        """
        Send a message to Slack.

        Args:
            text: Plain text message (fallback)
            blocks: Optional Slack Block Kit blocks for rich formatting
            channel: Optional channel override
        """
        logger.info("sending_slack_message", channel=channel or self.channel)

        payload = {
            "text": text,
            "channel": channel or self.channel
        }

        if blocks:
            payload["blocks"] = blocks

        response = await self.client.post(
            self.webhook_url,
            json=payload
        )
        response.raise_for_status()

        logger.info("slack_message_sent")

    async def send_workflow_start_notification(
        self,
        account_name: str,
        opportunity_id: str,
        workflow_id: str
    ) -> None:
        """
        Notify Slack that workflow has started.

        Args:
            account_name: Customer account name
            opportunity_id: Salesforce Opportunity ID
            workflow_id: Workflow identifier
        """
        text = f"🚀 Ada agent provisioning started for {account_name}"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "🚀 Agent Provisioning Started"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Account:*\n{account_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Opportunity ID:*\n{opportunity_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Workflow ID:*\n{workflow_id}"
                    }
                ]
            }
        ]

        await self.send_message(text=text, blocks=blocks)

    async def send_completion_notification(
        self,
        account_name: str,
        workflow_id: str,
        agent_url: str
    ) -> None:
        """
        Notify Slack that workflow has completed successfully.

        Args:
            account_name: Customer account name
            workflow_id: Workflow identifier
            agent_url: URL to the provisioned Ada agent
        """
        text = f"✅ Ada agent provisioning completed for {account_name}"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "✅ Agent Provisioning Complete"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Account:*\n{account_name}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Workflow ID:*\n{workflow_id}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"<{agent_url}|View Agent in Ada Dashboard>"
                }
            }
        ]

        await self.send_message(text=text, blocks=blocks)

    async def send_error_notification(
        self,
        workflow_id: str,
        opportunity_id: str,
        error: str
    ) -> None:
        """
        Notify Slack that workflow has failed.

        Args:
            workflow_id: Workflow identifier
            opportunity_id: Salesforce Opportunity ID
            error: Error message
        """
        text = f"❌ Ada agent provisioning failed for opportunity {opportunity_id}"

        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": "❌ Agent Provisioning Failed"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Opportunity ID:*\n{opportunity_id}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Workflow ID:*\n{workflow_id}"
                    }
                ]
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Error:*\n```{error}```"
                }
            }
        ]

        await self.send_message(text=text, blocks=blocks)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.client.aclose()
