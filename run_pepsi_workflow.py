"""
Execute the full Ada agent provisioning workflow for Pepsi.

This script runs all 28 steps of the Zapier workflow in Python:
1. Generate bot handle: "pepsi-ai-agent-demo"
2. Clone bot (ignore error)
3. Login to Ada dashboard via Playwright
4. Retrieve API key
5. Create knowledge base
6. Generate company description
7. Generate 10 KB articles
8. Generate 70 customer questions
9. Create 2 Beeceptor endpoints
10. Create channel
11. Create 70 conversations with messages
12. Send completion notification

Usage:
    python3 run_pepsi_workflow.py
"""

import asyncio
import json
import structlog
from typing import List, Dict, Any

# Configure logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()
    ]
)
logger = structlog.get_logger()


# Import our services
import sys
sys.path.append('/Users/rafsilva/Desktop/Claude_code/ada_agent_provisioning')

from app.utils.handle_generator import generate_bot_handle
from app.services.playwright_service import PlaywrightService
from app.services.content_generator_claude import ContentGeneratorClaude
from app.clients.anthropic_client import AnthropicClient
from app.clients.ada import AdaClient
from app.clients.beeceptor import BeeceptorClient


async def run_pepsi_workflow():
    """Execute the full workflow for Pepsi."""

    # Configuration
    company_name = "Pepsi"
    clone_secret = "nRk3zkYVe>@Khm?Q2dY8axrR.5ucqPGF"
    ada_email = "scteam@ada.support"
    ada_password = "Adalovelace123!"

    logger.info("workflow_started", company=company_name)

    # ========== PHASE 1: Setup & Bot Handle ==========
    logger.info("phase_1_bot_handle_generation")

    # Step 20: Generate clean bot handle
    bot_handle = generate_bot_handle(company_name)
    logger.info("bot_handle_generated", handle=bot_handle)
    print(f"\n✅ Bot handle: {bot_handle}\n")

    # ========== PHASE 2: Clone Bot ==========
    logger.info("phase_2_bot_cloning")

    # Step 21: Clone bot (ignore error)
    ada_client = AdaClient()
    await ada_client.clone_bot(
        clone_secret=clone_secret,
        new_handle=bot_handle,
        email=ada_email,
        password=ada_password
    )
    logger.info("bot_clone_initiated", handle=bot_handle)
    print(f"✅ Bot clone API called (ignoring error as expected)\n")

    # Wait for bot to be provisioned
    print("⏳ Waiting 15 seconds for bot to be provisioned...")
    await asyncio.sleep(15)

    # ========== PHASE 3: API Key Retrieval ==========
    logger.info("phase_3_api_key_retrieval")

    # Step 23 (automated): Get API key via Playwright
    playwright_service = PlaywrightService(
        headless=False,  # Visible browser for first run
        email=ada_email,
        password=ada_password
    )

    print(f"🎭 Launching browser to retrieve API key from {bot_handle}.ada.support...")
    api_key = await playwright_service.get_ada_api_key(bot_handle)
    logger.info("api_key_retrieved", key_preview=f"{api_key[:12]}...")
    print(f"✅ API key retrieved: {api_key[:12]}...{api_key[-4:]}\n")

    # ========== PHASE 4: Knowledge Base ==========
    logger.info("phase_4_knowledge_base")

    # Initialize Claude client
    import os
    from dotenv import load_dotenv
    load_dotenv()

    anthropic_client = AnthropicClient()
    content_generator = ContentGeneratorClaude(anthropic_client)

    # Step 24: Create knowledge source
    base_url = f"https://{bot_handle}.ada.support"
    await ada_client.create_knowledge_source(
        base_url=base_url,
        api_key=api_key,
        source_id="demosource",
        name="Demo Knowledge Source"
    )
    print("✅ Knowledge source created: demosource\n")

    # Step 25: Generate company description
    print("🤖 Generating company description...")
    company_description = await content_generator.generate_company_description(
        account_name=company_name,
        manual_description=f"{company_name} is a global beverage company."
    )
    logger.info("company_description_generated", preview=company_description[:100])
    print(f"✅ Company description: {company_description[:150]}...\n")

    # Step 26: Generate 10 KB articles
    print("🤖 Generating 10 knowledge base articles (this takes ~30 seconds)...")
    kb_articles = await content_generator.generate_kb_articles(
        account_name=company_name,
        company_description=company_description
    )
    print(f"✅ Generated {len(kb_articles)} knowledge articles\n")

    # Step 27: Bulk upload articles
    print("📤 Uploading articles to Ada...")
    await ada_client.bulk_upload_articles(
        base_url=base_url,
        api_key=api_key,
        articles=kb_articles
    )
    print(f"✅ Uploaded {len(kb_articles)} articles to Ada\n")

    # ========== PHASE 5: Question Generation ==========
    logger.info("phase_5_question_generation")

    # Step 28: Generate 70 questions
    print("🤖 Generating 70 customer questions (this takes ~45 seconds)...")
    questions_obj = await content_generator.generate_70_questions(
        account_name=company_name,
        kb_articles=kb_articles
    )

    # Step 29: Convert to array (Python equivalent of JS code)
    questions = []
    for key in sorted(questions_obj.keys(), key=lambda x: int(x.split('_')[1])):
        questions.append(questions_obj[key])

    # Deduplicate
    seen = set()
    unique_questions = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique_questions.append(q)

    questions = unique_questions[:70]
    print(f"✅ Generated {len(questions)} unique questions\n")

    # ========== PHASE 6: Beeceptor Endpoints ==========
    logger.info("phase_6_endpoint_creation")

    # Step 30: Generate endpoints
    print("🤖 Generating Beeceptor endpoint rules...")
    endpoints_json = await content_generator.generate_beeceptor_rules(
        account_description=company_description,
        clean_name=bot_handle
    )

    # Step 31: Split rules
    rule1 = json.dumps(endpoints_json["result"]["use_case_1_rule"])
    rule2 = json.dumps(endpoints_json["result"]["use_case_2_rule"])

    # Steps 32-33: Create in Beeceptor
    beeceptor_client = BeeceptorClient()
    print("📡 Creating Beeceptor endpoints...")
    await beeceptor_client.create_rule(rule1)
    await beeceptor_client.create_rule(rule2)
    print("✅ Created 2 Beeceptor endpoints at https://app.beeceptor.com/console/ada-demo\n")

    # ========== PHASE 7: Channel & Conversations ==========
    logger.info("phase_7_conversations")

    # Step 34: Create channel
    print("📱 Creating Ada channel...")
    channel_id = await ada_client.create_channel(
        base_url=base_url,
        api_key=api_key,
        name="Raf_Channel",
        description="A custom messaging channel for my AI Agent"
    )
    print(f"✅ Channel created: {channel_id}\n")

    # Steps 35-37: Loop 70 times - create conversations + messages
    print(f"💬 Creating 70 conversations with customer questions...")
    print("   (This will take ~3-5 minutes with rate limiting)\n")

    successful_convos = 0
    failed_convos = 0

    for i, question in enumerate(questions[:70], 1):
        try:
            # Step 36: Create conversation
            conv = await ada_client.create_conversation(
                base_url=base_url,
                api_key=api_key,
                channel_id=channel_id
            )

            # Step 37: Post message
            await ada_client.create_message(
                base_url=base_url,
                api_key=api_key,
                conversation_id=conv["conversation_id"],
                end_user_id=conv["end_user_id"],
                message_body=question
            )

            successful_convos += 1

            if i % 10 == 0:
                print(f"   ✓ Created {i}/70 conversations...")

            # Rate limiting - small delay
            await asyncio.sleep(0.5)

        except Exception as e:
            failed_convos += 1
            logger.warning("conversation_creation_failed", iteration=i, error=str(e))

    print(f"\n✅ Created {successful_convos} conversations successfully")
    if failed_convos > 0:
        print(f"⚠️  {failed_convos} conversations failed\n")

    # ========== PHASE 8: Completion ==========
    logger.info("phase_8_completion")

    print("\n" + "="*80)
    print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
    print("="*80)
    print(f"\n📋 Summary:")
    print(f"   • Bot Handle: {bot_handle}")
    print(f"   • Bot URL: https://{bot_handle}.ada.support")
    print(f"   • Login: {ada_email} / {ada_password}")
    print(f"   • Knowledge Articles: {len(kb_articles)}")
    print(f"   • Conversations Created: {successful_convos}")
    print(f"   • Beeceptor Console: https://app.beeceptor.com/console/ada-demo")
    print(f"\n✅ Your checklist:")
    print(f"   - Set up the handoff integrations required")
    print(f"   - Set up the persona settings")
    print(f"   - Brand your agent")
    print(f"   - Set up the actions I created for you in Ada")
    print(f"   - Add a playbook")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 STARTING ADA AGENT PROVISIONING WORKFLOW FOR PEPSI")
    print("="*80 + "\n")

    try:
        asyncio.run(run_pepsi_workflow())
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Workflow failed with error: {e}")
        import traceback
        traceback.print_exc()
