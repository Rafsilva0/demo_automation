"""Knowledge base building service."""

import structlog
from typing import List, Dict, Any

from app.clients.ada import AdaClient
from app.clients.openai_client import OpenAIClient

logger = structlog.get_logger()


class KnowledgeBuilder:
    """Service for building knowledge bases in Ada."""

    def __init__(self, ada_client: AdaClient, openai_client: OpenAIClient):
        """
        Initialize knowledge builder.

        Args:
            ada_client: Ada API client
            openai_client: OpenAI API client
        """
        self.ada = ada_client
        self.openai = openai_client

    async def create_knowledge_source(
        self,
        account_name: str,
        description: str | None = None
    ) -> str:
        """
        Create a knowledge source in Ada.

        This corresponds to Zapier step 14: Webhooks - Create Knowledge Source

        Args:
            account_name: Customer account name
            description: Optional description

        Returns:
            Knowledge source ID

        TODO: Update with actual webhook details from Zapier step 14
        """
        logger.info("creating_knowledge_source", account_name=account_name)

        source_name = f"{account_name} Knowledge Base"

        source_id = await self.ada.create_knowledge_source(
            name=source_name,
            description=description
        )

        logger.info(
            "knowledge_source_created",
            source_id=source_id,
            account_name=account_name
        )

        return source_id

    async def upload_articles(
        self,
        source_id: str,
        articles: List[Dict[str, str]]
    ) -> List[str]:
        """
        Upload knowledge articles to Ada.

        This corresponds to Zapier step 17: Looping - Upload All Services

        Args:
            source_id: Knowledge source ID
            articles: List of articles with 'title' and 'content'

        Returns:
            List of created article IDs

        TODO: Confirm article format and API details from Zapier step 17
        """
        logger.info(
            "uploading_articles",
            source_id=source_id,
            count=len(articles)
        )

        article_ids = []

        for article in articles:
            article_id = await self.ada.create_knowledge_article(
                source_id=source_id,
                title=article["title"],
                content=article["content"],
                metadata=article.get("metadata")
            )
            article_ids.append(article_id)

        logger.info(
            "articles_uploaded",
            source_id=source_id,
            count=len(article_ids)
        )

        return article_ids
