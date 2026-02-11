"""
Standalone Ada agent provisioning workflow for Pepsi.
No dependencies on app module - all code inline.
"""

import asyncio
import json
import os
import sys
import re
from typing import List, Dict, Any
from datetime import datetime

# Add path for our utility modules
sys.path.insert(0, '/Users/rafsilva/Desktop/Claude_code/ada_agent_provisioning')

try:
    from playwright.async_api import async_playwright
    import anthropic
    import httpx
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("Install with: pip3 install playwright anthropic httpx python-dotenv")
    sys.exit(1)

# Load environment
load_dotenv()

# Configuration
COMPANY_NAME = "Pepsi"
CLONE_SECRET = "nRk3zkYVe>@Khm?Q2dY8axrR.5ucqPGF"
ADA_EMAIL = "scteam@ada.support"
ADA_PASSWORD = "Adalovelace123!"
BEECEPTOR_TOKEN = "3db584716ce6764c1004850ee20e610e470aee7cTnwDhrdgQaknDva"

# Get Anthropic API key - try environment or prompt user
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    # Try reading from bash environment directly
    import subprocess
    try:
        result = subprocess.run(['bash', '-c', 'echo $ANTHROPIC_API_KEY'], capture_output=True, text=True)
        ANTHROPIC_API_KEY = result.stdout.strip()
    except:
        pass

if not ANTHROPIC_API_KEY or ANTHROPIC_API_KEY == "":
    print("❌ ANTHROPIC_API_KEY environment variable not set")
    print("   Set it with: export ANTHROPIC_API_KEY=your_key")
    print("   Or run from a shell that has it exported")
    sys.exit(1)

print(f"✓ Anthropic API key found: {ANTHROPIC_API_KEY[:10]}...")


def generate_bot_handle(company_name: str) -> str:
    """Generate clean bot handle from company name."""
    clean = company_name.lower()
    clean = re.sub(r'[^a-z0-9-]', '', clean)
    return clean + '-ai-agent-demo'


async def clone_bot(bot_handle: str):
    """Clone bot (ignore error)."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "https://scteam-demo.ada.support/api/clone",
                json={
                    "clone_secret": CLONE_SECRET,
                    "new_handle": bot_handle,
                    "email": ADA_EMAIL,
                    "user_full_name": "Ada SC Team",
                    "user_password": ADA_PASSWORD,
                    "type": "client"
                },
                timeout=30.0
            )
            print(f"   Clone API called: HTTP {response.status_code}")
        except Exception as e:
            print(f"   Clone API error (expected): {e}")


async def get_api_key_playwright(bot_handle: str) -> str:
    """Get API key from Ada dashboard using Playwright."""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        try:
            context = await browser.new_context()
            context.set_default_timeout(60000)
            page = await context.new_page()

            # Login
            login_url = f"https://{bot_handle}.ada.support/"
            print(f"   Navigating to {login_url}")
            await page.goto(login_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)  # Wait for page to stabilize

            await page.fill('input[type="email"], input[name="email"]', ADA_EMAIL)
            await page.fill('input[type="password"], input[name="password"]', ADA_PASSWORD)
            await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")')
            await page.wait_for_timeout(3000)  # Wait for login to complete

            # Navigate to APIs page
            apis_url = f"https://{bot_handle}.ada.support/platform/apis"
            print(f"   Navigating to {apis_url}")
            await page.goto(apis_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)  # Wait for page to stabilize

            # Close any modals that might appear (product announcements, etc.)
            try:
                close_button = await page.wait_for_selector('button:has-text("close")', timeout=3000)
                if close_button:
                    print(f"   Closing modal popup...")
                    await close_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass  # No modal, continue

            # Click Get started (or New API Key)
            try:
                await page.click('button:has-text("Get started")')
                print(f"   Clicked 'Get started'")
            except:
                await page.click('button:has-text("New API Key")')
                print(f"   Clicked 'New API Key'")
            await page.wait_for_timeout(1000)

            # Fill name - wait for modal to appear and find any text input
            await page.wait_for_selector('text="New API key"', timeout=5000)
            await page.wait_for_timeout(500)
            # Find the input field in the modal
            name_input = await page.wait_for_selector('input[type="text"]', timeout=5000)
            await name_input.fill("automation-key")
            print(f"   Filled API key name: automation-key")

            # Click Generate and immediately look for the key
            print(f"   Clicking 'Generate key' button...")

            # Click and DON'T wait - immediately start looking for the modal
            await page.click('button:has-text("Generate key")')

            # Wait for the modal with the actual API key to appear
            print(f"   Waiting for API key to be displayed...")
            try:
                # Wait for the "Copy the key" text which means the key is shown
                await page.wait_for_selector('text="This key will only be shown once"', timeout=10000)
                print(f"   Modal with API key appeared!")
            except:
                print(f"   Warning: Timeout waiting for 'This key will only be shown once' text")

            # Now take screenshot immediately BEFORE extracting
            await page.screenshot(path="/tmp/before_extract.png")
            print(f"   Screenshot saved (before extract) to /tmp/before_extract.png")

            # Extract using multiple methods
            api_key = None

            # Method 1: JavaScript to search ALL text content for hex pattern
            try:
                api_key = await page.evaluate("""
                    () => {
                        // Look for a 32-char hex string anywhere in the page
                        const bodyText = document.body.innerText;
                        const hexPattern = /\b[a-f0-9]{32,40}\b/gi;
                        const matches = bodyText.match(hexPattern);

                        if (matches && matches.length > 0) {
                            console.log('Found hex strings:', matches);
                            // Return the first one that looks like an API key
                            for (const match of matches) {
                                if (match.length >= 32 && match.length <= 40) {
                                    return match;
                                }
                            }
                        }
                        return null;
                    }
                """)

                if api_key:
                    print(f"   ✓ Found API key in page text: {api_key[:8]}...{api_key[-8:]}")
            except Exception as e:
                print(f"   Error extracting via text search: {e}")

            # Take final screenshot
            await page.screenshot(path="/tmp/api_key_page.png")
            print(f"   Screenshot saved to /tmp/api_key_page.png")

            # Fallback: try other selectors
            if not api_key:
                selectors = ['input[readonly]', 'code', 'pre', 'textarea[readonly]']
                for selector in selectors:
                    try:
                        element = await page.wait_for_selector(selector, timeout=2000)
                        if element:
                            tag_name = await element.evaluate('el => el.tagName.toLowerCase()')
                            if tag_name in ['input', 'textarea']:
                                api_key = await element.input_value()
                            else:
                                api_key = await element.text_content()

                            if api_key and api_key.strip() and len(api_key.strip()) >= 32:
                                api_key = api_key.strip()
                                print(f"   Found API key using selector: {selector}")
                                break
                    except:
                        continue

            if not api_key:
                print(f"   ERROR: Could not find API key. Check screenshot at /tmp/api_key_page.png")
                raise Exception("Could not find API key on page")

            return api_key
        finally:
            await browser.close()


async def generate_claude_completion(prompt: str, temperature: float = 0.7, max_tokens: int = 4000) -> str:
    """Generate completion using Claude."""
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}]
    )

    return message.content[0].text


async def main():
    print("\n" + "="*80)
    print("🚀 ADA AGENT PROVISIONING WORKFLOW FOR PEPSI")
    print("="*80 + "\n")

    # Step 1: Generate bot handle
    print("📝 Phase 1: Bot Handle Generation")
    bot_handle = generate_bot_handle(COMPANY_NAME)
    print(f"   ✅ Bot handle: {bot_handle}\n")

    # Step 2: Clone bot
    print("🔄 Phase 2: Bot Cloning")
    await clone_bot(bot_handle)
    print(f"   ✅ Clone initiated\n")

    print("⏳ Waiting 30 seconds for bot provisioning...")
    await asyncio.sleep(30)

    # Step 3: Get API key
    print("\n🎭 Phase 3: API Key Retrieval (Playwright)")
    api_key = await get_api_key_playwright(bot_handle)
    print(f"   ✅ API key: {api_key[:12]}...{api_key[-4:]}\n")

    base_url = f"https://{bot_handle}.ada.support"

    # Step 4: Knowledge Base
    print("📚 Phase 4: Knowledge Base Creation")

    # Create knowledge source
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/v2/knowledge/sources/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={"id": "demosource", "name": "Demo Knowledge Source"},
            timeout=30.0
        )
        response.raise_for_status()
        print("   ✅ Knowledge source created\n")

    # Generate company description
    print("   🤖 Generating company description...")
    company_desc = await generate_claude_completion(
        f"""You are an expert at making a company description for: {COMPANY_NAME}.
Here is a man made description: {COMPANY_NAME} is a global beverage company. Make sure to cross reference yours with this manual one.
Return a brief description about what the company does, who they service and the products they sell.""",
        temperature=0.7
    )
    print(f"   ✅ Company description: {company_desc[:100]}...\n")

    # Generate KB articles
    print("   🤖 Generating 10 knowledge articles (30 sec)...")
    articles_prompt = f"""You are an expert content writer for a company knowledge base.

Your ONLY job is to return a single valid JSON array of 10 FAQ articles for the company: {COMPANY_NAME}

Each article must have:
- A clear, question-style title in the "name" field
- A detailed body (120–200 words) in the "content" field
- The same "knowledge_source_id": "demosource"
- A string "id" from "1" to "10"

The topics should be commonly searched or asked about in a company's knowledge base.

Use the company name {COMPANY_NAME} naturally throughout the text.
Here is a company description: {company_desc}

CRITICAL: Respond with **one single JSON array only**. No markdown. No text outside JSON.

[
  {{"id": "1", "name": "Question 1?", "content": "120-200 word answer...", "knowledge_source_id": "demosource"}},
  ...10 objects total...
]"""

    articles_response = await generate_claude_completion(articles_prompt, temperature=0.5, max_tokens=6000)

    # Clean Claude markdown
    cleaned = articles_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    articles = json.loads(cleaned)
    print(f"   ✅ Generated {len(articles)} articles\n")

    # Upload articles
    print("   📤 Uploading articles to Ada...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/v2/knowledge/bulk/articles/",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=articles,
            timeout=60.0
        )
        response.raise_for_status()
        print(f"   ✅ Uploaded {len(articles)} articles\n")

    # Step 5: Generate Questions
    print("❓ Phase 5: Question Generation")
    print("   🤖 Generating 70 customer questions (45 sec)...")

    articles_text = "\n\n".join([f"Article {a['id']}: {a['name']}\n{a['content']}" for a in articles])

    questions_prompt = f"""Generate exactly 70 realistic customer questions for {COMPANY_NAME}.

Knowledge Base:
{articles_text}

Return ONLY a JSON object:
{{"question_1": "How can I...", "question_2": "What is...", ... "question_70": "When do..."}}

No markdown. No text outside JSON."""

    questions_response = await generate_claude_completion(questions_prompt, temperature=0.7, max_tokens=4000)

    cleaned = questions_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    questions_obj = json.loads(cleaned.strip())
    questions = [questions_obj[k] for k in sorted(questions_obj.keys(), key=lambda x: int(x.split('_')[1]))]
    questions = questions[:70]
    print(f"   ✅ Generated {len(questions)} questions\n")

    # Step 6: Beeceptor Endpoints
    print("📡 Phase 6: Beeceptor Endpoint Creation")
    print("   🤖 Generating endpoint rules...")

    endpoints_prompt = f"""Create 2 Beeceptor rule configurations for {COMPANY_NAME}.

Bot handle: {bot_handle}

Return ONLY this JSON structure:
{{
  "result": {{
    "use_case_1_rule": {{
      "enabled": true,
      "mock": true,
      "delay": 0,
      "match": {{"method": "GET", "value": "/{bot_handle}/status_check", "operator": "SW"}},
      "send": {{"status": 200, "body": "{{\\"status\\": \\"active\\"}}", "headers": {{"Content-Type": "application/json"}}, "templated": false}}
    }},
    "use_case_2_rule": {{
      "enabled": true,
      "mock": true,
      "delay": 0,
      "match": {{"method": "POST", "value": "/{bot_handle}/account_update", "operator": "SW"}},
      "send": {{"status": 200, "body": "{{\\"success\\": true}}", "headers": {{"Content-Type": "application/json"}}, "templated": false}}
    }}
  }}
}}"""

    endpoints_response = await generate_claude_completion(endpoints_prompt, temperature=0.7, max_tokens=2000)

    cleaned = endpoints_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    endpoints = json.loads(cleaned.strip())

    # Create endpoints in Beeceptor
    rule1 = json.dumps(endpoints["result"]["use_case_1_rule"])
    rule2 = json.dumps(endpoints["result"]["use_case_2_rule"])

    async with httpx.AsyncClient() as client:
        await client.post(
            "https://api.beeceptor.com/api/v1/endpoints/ada-demo/rules",
            headers={"Authorization": BEECEPTOR_TOKEN, "Content-Type": "application/json"},
            content=rule1,
            timeout=30.0
        )
        await client.post(
            "https://api.beeceptor.com/api/v1/endpoints/ada-demo/rules",
            headers={"Authorization": BEECEPTOR_TOKEN, "Content-Type": "application/json"},
            content=rule2,
            timeout=30.0
        )
    print("   ✅ Created 2 Beeceptor endpoints\n")

    # Step 7: Channel & Conversations
    print("💬 Phase 7: Conversations Creation")
    print("   📱 Creating channel...")

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/v2/channels/",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"name": "Raf_Channel", "description": "Custom messaging channel", "modality": "messaging"},
            timeout=30.0
        )
        response.raise_for_status()
        channel_id = response.json()["id"]
        print(f"   ✅ Channel created: {channel_id}\n")

    # Create 70 conversations
    print(f"   💬 Creating 70 conversations (3-5 minutes)...")

    successful = 0
    failed = 0

    async with httpx.AsyncClient() as client:
        for i, question in enumerate(questions[:70], 1):
            try:
                # Create conversation
                response = await client.post(
                    f"{base_url}/api/v2/conversations/",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"channel_id": channel_id},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                conv_id = data["id"]
                end_user_id = data["end_user_id"]

                # Post message
                response = await client.post(
                    f"{base_url}/api/v2/conversations/{conv_id}/messages/",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={
                        "author": {"id": end_user_id, "role": "end_user"},
                        "content": {"body": question, "type": "text"}
                    },
                    timeout=30.0
                )
                response.raise_for_status()

                successful += 1
                if i % 10 == 0:
                    print(f"      ✓ {i}/70 conversations...")

                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                failed += 1
                print(f"      ✗ Conversation {i} failed: {e}")

    print(f"   ✅ Created {successful} conversations\n")

    # Completion
    print("\n" + "="*80)
    print("🎉 WORKFLOW COMPLETED!")
    print("="*80)
    print(f"\n📋 Summary:")
    print(f"   • Bot Handle: {bot_handle}")
    print(f"   • Bot URL: https://{bot_handle}.ada.support")
    print(f"   • Login: {ADA_EMAIL} / {ADA_PASSWORD}")
    print(f"   • Knowledge Articles: {len(articles)}")
    print(f"   • Conversations: {successful}/{len(questions)}")
    print(f"   • Beeceptor: https://app.beeceptor.com/console/ada-demo")
    print(f"\n✅ Your checklist:")
    print(f"   - Set up handoff integrations")
    print(f"   - Configure persona settings")
    print(f"   - Brand your agent")
    print(f"   - Set up actions in Ada")
    print(f"   - Add a playbook")
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted")
    except Exception as e:
        print(f"\n\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
