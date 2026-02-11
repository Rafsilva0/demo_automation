"""Content generation service using OpenAI."""

import structlog
from typing import List, Dict, Any

from app.clients.openai_client import OpenAIClient

logger = structlog.get_logger()


class ContentGenerator:
    """Service for generating AI agent content using OpenAI."""

    def __init__(self, openai_client: OpenAIClient):
        """
        Initialize content generator.

        Args:
            openai_client: OpenAI API client
        """
        self.openai = openai_client

    async def generate_company_description(
        self,
        account_name: str,
        industry: str | None = None,
        additional_context: str | None = None
    ) -> str:
        """
        Generate a company description for the Ada agent.

        This corresponds to Zapier step 15: ChatGPT - Create Company Description

        Args:
            account_name: Customer account name
            industry: Optional industry information
            additional_context: Optional additional context

        Returns:
            Generated company description

        TODO: Replace with actual prompt from Zapier step 15
        """
        logger.info("generating_company_description", account_name=account_name)

        # Placeholder prompt - needs to be replaced with actual Zapier prompt
        system_message = """You are an expert at writing company descriptions for AI customer service agents.
        Create a concise, informative description that will help the AI agent understand the company's business."""

        prompt = f"""Create a company description for {account_name}.

        Industry: {industry or 'Not specified'}
        Additional context: {additional_context or 'None'}

        The description should be 2-3 paragraphs and cover:
        1. What the company does
        2. Key products/services
        3. Target customers
        """

        description = await self.openai.generate_completion(
            prompt=prompt,
            system_message=system_message
        )

        logger.info(
            "company_description_generated",
            account_name=account_name,
            length=len(description)
        )

        return description

    async def generate_knowledge_articles(
        self,
        company_description: str,
        account_name: str,
        num_articles: int = 5
    ) -> List[Dict[str, str]]:
        """
        Generate knowledge base articles for the Ada agent.

        This corresponds to Zapier step 16: ChatGPT - Create knowledge articles

        Args:
            company_description: Company description
            account_name: Customer account name
            num_articles: Number of articles to generate

        Returns:
            List of articles, each with 'title' and 'content' keys

        TODO: Replace with actual prompt from Zapier step 16
        """
        logger.info(
            "generating_knowledge_articles",
            account_name=account_name,
            num_articles=num_articles
        )

        # Placeholder prompt - needs to be replaced with actual Zapier prompt
        system_message = """You are an expert at creating knowledge base articles for AI customer service agents.
        Generate comprehensive, well-structured articles."""

        prompt = f"""Based on this company description, generate {num_articles} knowledge base articles:

        {company_description}

        For each article, provide:
        - A clear title
        - Detailed content covering common customer questions

        Format as JSON array: [{{"title": "...", "content": "..."}}]
        """

        response = await self.openai.generate_structured_completion(
            prompt=prompt,
            system_message=system_message,
            response_format={"type": "json_object"}
        )

        # Parse JSON response
        import json
        articles = json.loads(response).get("articles", [])

        logger.info(
            "knowledge_articles_generated",
            account_name=account_name,
            count=len(articles)
        )

        return articles

    async def generate_tk_questions(
        self,
        company_description: str,
        num_questions: int = 10
    ) -> List[str]:
        """
        Generate troubleshooting/knowledge questions.

        This corresponds to Zapier step 18: ChatGPT - Scale TK Questions

        Args:
            company_description: Company description
            num_questions: Number of questions to generate

        Returns:
            List of TK questions

        TODO: Replace with actual prompt from Zapier step 18
        """
        logger.info("generating_tk_questions", num_questions=num_questions)

        # Placeholder implementation
        system_message = """Generate common troubleshooting questions that customers might ask."""

        prompt = f"""Based on this company description, generate {num_questions} common troubleshooting questions:

        {company_description}

        Format as a JSON array of strings.
        """

        response = await self.openai.generate_structured_completion(
            prompt=prompt,
            system_message=system_message,
            response_format={"type": "json_object"}
        )

        import json
        questions = json.loads(response).get("questions", [])

        logger.info("tk_questions_generated", count=len(questions))

        return questions

    async def generate_endpoints(
        self,
        company_description: str,
        tk_questions: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Generate endpoint configurations.

        This corresponds to Zapier step 20: ChatGPT - Build Endpoints

        Args:
            company_description: Company description
            tk_questions: List of TK questions

        Returns:
            List of endpoint configurations

        TODO: Replace with actual prompt from Zapier step 20
        """
        logger.info("generating_endpoints")

        # Placeholder implementation
        system_message = """Generate API endpoint configurations for the AI agent."""

        prompt = f"""Based on this company description and common questions, generate endpoint configurations:

        Company: {company_description}

        Common questions: {', '.join(tk_questions[:5])}

        Format as JSON array with: name, description, url, method
        """

        response = await self.openai.generate_structured_completion(
            prompt=prompt,
            system_message=system_message,
            response_format={"type": "json_object"}
        )

        import json
        endpoints = json.loads(response).get("endpoints", [])

        logger.info("endpoints_generated", count=len(endpoints))

        return endpoints
