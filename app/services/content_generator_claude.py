"""
Content generation service using Claude (Anthropic).

This implements the exact prompts from the Zapier workflow, but uses Claude instead of OpenAI:
- Step 25: Company Description
- Step 26: KB Articles
- Step 28: 70 Questions
- Step 30: Beeceptor Endpoints
"""

import json
import structlog
from typing import List, Dict, Any

from app.clients.anthropic_client import AnthropicClient

logger = structlog.get_logger()


class ContentGeneratorClaude:
    """Content generator using Claude API."""

    def __init__(self, anthropic_client: AnthropicClient):
        """Initialize with Anthropic client."""
        self.claude = anthropic_client

    async def generate_company_description(
        self,
        account_name: str,
        manual_description: str = ""
    ) -> str:
        """
        Step 25: Create Company Description.

        Uses Claude 3.5 Sonnet instead of GPT-3.5-turbo-instruct.
        """
        logger.info("generating_company_description", account_name=account_name)

        prompt = f"""You are an expert at making a company description for : {account_name}.
Here is a man made description: {manual_description}. Make sure to cross reference yours with this manual one. It may give insight into the company.
Return a brief description about what the company does, who they service and the products they sell."""

        response = await self.claude.generate_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=500
        )

        logger.info("company_description_generated", account_name=account_name)
        return response.strip()

    async def generate_kb_articles(
        self,
        account_name: str,
        company_description: str
    ) -> List[Dict[str, Any]]:
        """
        Step 26: Create Knowledge Articles.

        Returns exactly 10 articles as JSON array.
        Uses Claude instead of GPT-3.5-turbo-instruct.
        """
        logger.info("generating_kb_articles", account_name=account_name)

        prompt = f"""You are an expert content writer for a company knowledge base.

Your ONLY job is to return a single valid JSON array of 10 FAQ articles for the company: {account_name}

Each article must have:
- A clear, question-style title in the "name" field
- A detailed body (120–200 words) in the "content" field
- The same "knowledge_source_id": "demosource"
- A string "id" from "1" to "10"

The topics should be commonly searched or asked about in a company's knowledge base — such as billing, account management, troubleshooting, security, integrations, setup, or company policies.

Use the company name {account_name} naturally throughout the text to make the content feel tailored to {account_name}. The tone should be helpful, professional, and easy to read.
Here is a company description you should use to understand the context and the type of company for this task: {company_description}

CRITICAL FORMAT RULES:

- Respond with **one single JSON array only**.
- The JSON must contain exactly 10 objects.
- No text, explanations, numbering, or comments outside the JSON.
- No markdown formatting.
- Each object must have exactly these keys: "id", "name", "content", "knowledge_source_id".
- "id" values must be strings from "1" to "10".
- "knowledge_source_id" must always be "demosource".

Follow this exact example structure:

[
  {{
    "id": "1",
    "name": "How do I set up automatic contributions to my Wealthsimple account?",
    "content": "…120–200 word paragraph-style explanation here…",
    "knowledge_source_id": "demosource"
  }},
  {{
    "id": "2",
    "name": "How does Wealthsimple charge fees for managed accounts?",
    "content": "…120–200 word paragraph-style explanation here…",
    "knowledge_source_id": "demosource"
  }}
  // ...objects 3 through 10...
]

Now generate and return ONLY this JSON array with objects 1 through 10 filled in."""

        response = await self.claude.generate_completion(
            prompt=prompt,
            temperature=0.5,
            max_tokens=6000  # Need more tokens for 10 articles
        )

        # Parse JSON
        try:
            # Claude might wrap in markdown code blocks, remove them
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            articles = json.loads(cleaned)
            if not isinstance(articles, list) or len(articles) != 10:
                raise ValueError(f"Expected 10 articles, got {len(articles) if isinstance(articles, list) else 'non-list'}")

            logger.info("kb_articles_generated", count=len(articles))
            return articles

        except json.JSONDecodeError as e:
            logger.error("kb_articles_json_parse_error", error=str(e), response_preview=response[:500])
            raise Exception(f"Failed to parse Claude response as JSON: {e}")

    async def generate_70_questions(
        self,
        account_name: str,
        kb_articles: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Step 28: Build 70 Questions.

        Returns JSON object with flat structure: {"question_1": "...", "question_2": "...", ...}
        Uses Claude instead of GPT-3.5-turbo-instruct.
        """
        logger.info("generating_70_questions", account_name=account_name)

        # Build articles context
        articles_text = "\n\n".join([
            f"Article {a['id']}: {a['name']}\n{a['content']}"
            for a in kb_articles
        ])

        prompt = f"""You are an expert at generating customer questions for an AI agent knowledge base.

Company: {account_name}

Knowledge Base Articles:
{articles_text}

Generate exactly 70 realistic customer questions that an end-user might ask about {account_name}.

The questions should:
- Cover topics from the knowledge base articles above
- Be natural, conversational questions
- Vary in complexity and phrasing
- Include common variations and synonyms

Return ONLY a JSON object with this exact structure:
{{
  "question_1": "How can I...",
  "question_2": "What is...",
  ...
  "question_70": "When do..."
}}

No text outside the JSON. No markdown formatting."""

        response = await self.claude.generate_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=4000
        )

        # Parse JSON
        try:
            # Claude might wrap in markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            questions_obj = json.loads(cleaned)
            if not isinstance(questions_obj, dict):
                raise ValueError("Expected JSON object")

            logger.info("70_questions_generated", count=len(questions_obj))
            return questions_obj

        except json.JSONDecodeError as e:
            logger.error("questions_json_parse_error", error=str(e), response_preview=response[:500])
            raise Exception(f"Failed to parse Claude response as JSON: {e}")

    async def generate_beeceptor_rules(
        self,
        account_description: str,
        clean_name: str
    ) -> Dict[str, Any]:
        """
        Step 30: Build Endpoints (Beeceptor Rules).

        Returns JSON with 2 Beeceptor rule objects.
        Uses Claude instead of GPT-3.5-turbo-instruct.
        """
        logger.info("generating_beeceptor_rules", clean_name=clean_name)

        prompt = f"""You are an expert at creating mock API endpoints for demo purposes.

Create 2 realistic Beeceptor rule configurations for a company with this description:
{account_description}

Bot handle: {clean_name}

Each rule should be a realistic use case that an AI agent might call (e.g., check order status, update account, verify eligibility).

Return ONLY a JSON object with this structure:
{{
  "result": {{
    "use_case_1_rule": {{
      "enabled": true,
      "mock": true,
      "delay": 0,
      "match": {{
        "method": "GET",
        "value": "/{clean_name}/status_check",
        "operator": "SW"
      }},
      "send": {{
        "status": 200,
        "body": "{{\\"status\\": \\"active\\", \\"message\\": \\"System operational\\"}}",
        "headers": {{"Content-Type": "application/json"}},
        "templated": false
      }}
    }},
    "use_case_2_rule": {{
      "enabled": true,
      "mock": true,
      "delay": 0,
      "match": {{
        "method": "POST",
        "value": "/{clean_name}/account_update",
        "operator": "SW"
      }},
      "send": {{
        "status": 200,
        "body": "{{\\"success\\": true, \\"updated_at\\": \\"{{{{now}}}}\\"}}",
        "headers": {{"Content-Type": "application/json"}},
        "templated": true
      }}
    }}
  }}
}}

Make the endpoints relevant to the company's business. Return ONLY valid JSON."""

        response = await self.claude.generate_completion(
            prompt=prompt,
            temperature=0.7,
            max_tokens=2000
        )

        # Parse JSON
        try:
            # Claude might wrap in markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()

            rules = json.loads(cleaned)
            logger.info("beeceptor_rules_generated")
            return rules

        except json.JSONDecodeError as e:
            logger.error("beeceptor_rules_json_parse_error", error=str(e), response_preview=response[:500])
            raise Exception(f"Failed to parse Claude response as JSON: {e}")
