#!/usr/bin/env python3
"""
Ada Agent Provisioning - Production CLI Tool

Usage:
    python3 provision.py --company "Pepsi" --ada-key "abc123..." [options]
    python3 provision.py --company "Coca-Cola" --auto [options]
    python3 provision.py --config config.yaml [options]
"""

import asyncio
import argparse
import json
import sys
import os
import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from pathlib import Path

import anthropic
import httpx
from dotenv import load_dotenv

# Load environment variables from script directory
env_path = Path(__file__).parent / ".env"
load_dotenv(env_path, override=True)

# Constants
BEECEPTOR_TOKEN = os.getenv("BEECEPTOR_AUTH_TOKEN", "3db584716ce6764c1004850ee20e610e470aee7cTnwDhrdgQaknDva")
ADA_EMAIL = os.getenv("ADA_EMAIL", "scteam@ada.support")
ADA_PASSWORD = os.getenv("ADA_PASSWORD", "Adalovelace123!")
CLONE_SECRET = os.getenv("ADA_CLONE_SECRET", "nRk3zkYVe>@Khm?Q2dY8axrR.5ucqPGF")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_status(emoji: str, message: str, color: str = ""):
    """Print formatted status message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{color}[{timestamp}] {emoji} {message}{Colors.ENDC}")

def print_substep(step_num: str, message: str):
    """Print formatted sub-step message."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"{Colors.OKCYAN}[{timestamp}]   └─ {step_num} {message}{Colors.ENDC}")

def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{Colors.BOLD}{'='*80}")
    print(f"{title}")
    print(f"{'='*80}{Colors.ENDC}\n")

def generate_bot_handle(company_name: str) -> str:
    """Generate clean bot handle from company name."""
    clean = company_name.lower()
    clean = re.sub(r'[^a-z0-9-]', '', clean)
    return clean + '-ai-agent-demo'

async def run_playwright_tasks(
    bot_handle: str,
    company_name: str,
    company_website: Optional[str],
    ada_actions: List[Dict]
) -> tuple[Optional[str], bool, bool]:
    """
    Run all Playwright-based tasks in a single browser session.

    Args:
        bot_handle: Bot handle
        company_name: Company name
        company_website: Optional website URL
        ada_actions: List of actions to import

    Returns:
        Tuple of (api_key, website_success, actions_success)
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print_status("❌", "Playwright not installed", Colors.FAIL)
        return None, False, False

    print_header("🎭 UNIFIED PLAYWRIGHT SESSION (5-minute timeout)")
    print_substep("", "Running API key retrieval, website scraping, and action import in ONE browser session")

    async with async_playwright() as p:
        browser = None
        try:
            # Launch browser once
            print_substep("→", "Launching Chromium browser (headless)...")
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            context.set_default_timeout(300000)  # 5-minute timeout
            page = await context.new_page()

            # Task 1: Get API Key
            print_substep("→", "Task 1/3: Retrieving API key...")
            api_key = await get_api_key_playwright(bot_handle, page=page, should_close_browser=False)

            # Task 2: Add Website Knowledge Source
            print_substep("→", "Task 2/3: Adding website knowledge source...")
            website_success = False
            try:
                website_success = await add_website_knowledge_source(
                    bot_handle, company_name, company_website, page=page, should_close_browser=False
                )
            except Exception as e:
                print_status("⚠️", f"Website task failed (non-critical): {e}", Colors.WARNING)

            # Task 3: Import Actions
            print_substep("→", "Task 3/3: Importing actions into Ada...")
            actions_success = False
            if ada_actions:
                try:
                    actions_success = await import_actions_to_ada(
                        bot_handle, ada_actions, page=page, should_close_browser=False
                    )
                except Exception as e:
                    print_status("⚠️", f"Action import failed (non-critical): {e}", Colors.WARNING)

            print_status("✅", "All Playwright tasks completed", Colors.OKGREEN)
            return api_key, website_success, actions_success

        except Exception as e:
            print_status("❌", f"Playwright session error: {e}", Colors.FAIL)
            return None, False, False
        finally:
            if browser:
                print_substep("→", "Closing browser...")
                await browser.close()

async def clone_bot(bot_handle: str) -> bool:
    """Clone bot via API."""
    print_substep("2.1", "Calling Ada clone API endpoint...")
    print_substep("", f"Target bot handle: {bot_handle}")
    print_substep("", "Using scteam@ada.support credentials")

    try:
        async with httpx.AsyncClient() as client:
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

            if response.status_code in [200, 201]:
                print_status("✅", "Bot cloned successfully", Colors.OKGREEN)
                return True
            elif response.status_code == 500:
                print_status("⚠️", "Bot may already exist (HTTP 500 - this is expected)", Colors.WARNING)
                print_substep("", "Continuing workflow (HTTP 500 doesn't mean failure)")
                return True
            else:
                print_status("❌", f"Clone failed: HTTP {response.status_code}", Colors.FAIL)
                return False
    except Exception as e:
        print_status("❌", f"Clone error: {e}", Colors.FAIL)
        return False

async def get_api_key_playwright(bot_handle: str, page=None, should_close_browser: bool = True) -> Optional[str]:
    """Get API key using Playwright automation.

    Args:
        bot_handle: Bot handle to retrieve key for
        page: Optional existing Playwright page (for session reuse)
        should_close_browser: Whether to close browser when done (False if reusing session)
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        print_status("❌", "Playwright not installed. Run: pip install playwright && playwright install", Colors.FAIL)
        return None

    # If page provided, reuse it; otherwise create new browser
    if page:
        print_substep("3.1", "Reusing existing browser session...")
    else:
        print_substep("3.1", "Launching Chromium browser (headless)...")

    playwright_context = None
    browser = None

    try:
        if not page:
            playwright_context = async_playwright()
            p = await playwright_context.__aenter__()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            context.set_default_timeout(300000)  # 5-minute timeout
            page = await context.new_page()
        else:
            # Set timeout on existing page
            page.set_default_timeout(300000)

            # Login
            print_substep("3.2", f"Navigating to login page: {bot_handle}.ada.support")
            login_url = f"https://{bot_handle}.ada.support/"
            await page.goto(login_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            print_substep("3.3", "Filling login credentials and submitting form...")
            await page.fill('input[type="email"], input[name="email"]', ADA_EMAIL)
            await page.fill('input[type="password"], input[name="password"]', ADA_PASSWORD)
            await page.click('button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")')
            await page.wait_for_timeout(3000)

            # Navigate to APIs page
            print_substep("3.4", "Navigating to /platform/apis page...")
            apis_url = f"https://{bot_handle}.ada.support/platform/apis"
            await page.goto(apis_url, wait_until="domcontentloaded")
            await page.wait_for_timeout(2000)

            # Close modals
            print_substep("3.5", "Closing any modal dialogs...")
            try:
                close_button = await page.wait_for_selector('button:has-text("close")', timeout=3000)
                if close_button:
                    await close_button.click()
                    await page.wait_for_timeout(1000)
            except:
                print_substep("", "No modals to close")
                pass

            # Click to create API key
            print_substep("3.6", "Clicking 'New API Key' button...")
            try:
                await page.click('button:has-text("Get started")')
            except:
                await page.click('button:has-text("New API Key")')
            await page.wait_for_timeout(1000)

            # Fill name
            print_substep("3.7", "Filling API key name: 'automation-key'")
            await page.wait_for_selector('text="New API key"', timeout=5000)
            await page.wait_for_timeout(500)
            name_input = await page.wait_for_selector('input[type="text"]', timeout=5000)
            await name_input.fill("automation-key")

            # Generate key
            print_substep("3.8", "Clicking 'Generate key' button...")
            await page.click('button:has-text("Generate key")')

            # Wait for key to appear - try multiple strategies
            print_substep("3.9", "Waiting for API key to be generated (may take 5-15 seconds)...")

            # Strategy 1: Wait for success message
            api_key = None
            try:
                await page.wait_for_selector('text="This key will only be shown once"', timeout=15000)
                print_status("✓", "API key modal appeared successfully", Colors.OKGREEN)
                await page.wait_for_timeout(1000)  # Let it fully render
            except:
                print_status("⚠️", "Didn't see confirmation message, trying alternative selectors...", Colors.WARNING)

            # Strategy 2: Wait a bit more and take a screenshot for debugging
            await page.wait_for_timeout(2000)
            screenshot_path = f"/tmp/ada_api_key_{bot_handle}.png"
            await page.screenshot(path=screenshot_path)
            print_substep("", f"Debug screenshot saved: {screenshot_path}")

            # Strategy 3: Try multiple extraction methods
            print_substep("3.10", "Extracting API key from page using multiple strategies...")

            # Method 1: Look for the exact pattern in modal text (most reliable)
            print_substep("", "Method 1: Searching page text for hex pattern...")
            api_key = await page.evaluate("""
                () => {
                    // First try to find the modal with "API key" label
                    const modalText = document.body.innerText;

                    // Look for hex pattern that's 32-40 characters long (Ada API keys are typically 32)
                    const hexPattern = /[a-f0-9]{32,40}/gi;
                    const matches = modalText.match(hexPattern);

                    if (matches && matches.length > 0) {
                        // Return the first valid match
                        return matches[0];
                    }
                    return null;
                }
            """)

            # Method 2: Try to find it in input fields or code blocks
            if not api_key:
                print_substep("", "Method 2: Searching DOM elements (input/code/textarea)...")
                selectors_to_try = [
                    'input[value]',  # Any input with a value
                    'input[readonly]',
                    'textarea[readonly]',
                    'code',
                    'pre',
                    'span',
                    'div'
                ]

                for selector in selectors_to_try:
                    try:
                        elements = await page.query_selector_all(selector)
                        for elem in elements:
                            # Try both value attribute and text content
                            text = await elem.get_attribute('value') or await elem.text_content() or ''
                            text = text.strip()
                            # Check if it looks like an API key (32-40 hex chars)
                            if len(text) >= 32 and len(text) <= 40 and all(c in '0123456789abcdef' for c in text.lower()):
                                api_key = text
                                print_status("✓", f"Found API key using selector: {selector}", Colors.OKGREEN)
                                break
                        if api_key:
                            break
                    except Exception as e:
                        continue

            # Method 3: Last resort - look for any element containing exactly 32-40 hex characters
            if not api_key:
                print_substep("", "Method 3: Deep DOM search for hex strings...")
                try:
                    api_key = await page.evaluate("""
                        () => {
                            const allElements = document.querySelectorAll('*');
                            for (const elem of allElements) {
                                const text = (elem.value || elem.textContent || '').trim();
                                const hexPattern = /^[a-f0-9]{32,40}$/i;
                                if (hexPattern.test(text)) {
                                    return text;
                                }
                            }
                            return null;
                        }
                    """)
                    if api_key:
                        print_status("✓", "Found API key using deep DOM search", Colors.OKGREEN)
                except:
                    pass

            if api_key:
                print_status("✅", f"API key retrieved successfully: {api_key[:12]}...{api_key[-4:]}", Colors.OKGREEN)
                print_substep("", f"Full key length: {len(api_key)} characters")
                return api_key
            else:
                print_status("❌", "Could not extract API key from page", Colors.FAIL)
                print_substep("", f"Check screenshot at: {screenshot_path}")
                return None

    finally:
        if should_close_browser and browser:
            await browser.close()
        if playwright_context:
            await playwright_context.__aexit__(None, None, None)

async def generate_claude_completion(prompt: str, temperature: float = 0.7, max_tokens: int = 4000) -> str:
    """Generate completion using Claude."""
    if not ANTHROPIC_API_KEY:
        raise ValueError("ANTHROPIC_API_KEY environment variable must be set")

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text

async def create_knowledge_base(
    base_url: str,
    api_key: str,
    company_name: str,
    company_desc: Optional[str] = None,
    num_articles: int = 10
) -> tuple[str, List[Dict]]:
    """Create knowledge base with articles."""
    print_header("📚 PHASE 4: Knowledge Base Creation")

    # Create knowledge source
    print_substep("4.1", "Creating knowledge source in Ada...")
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

        if response.status_code in [200, 201]:
            print_status("✅", "Knowledge source created", Colors.OKGREEN)
        elif response.status_code == 409:
            print_status("⚠️", "Knowledge source already exists", Colors.WARNING)
        else:
            print_status("❌", f"Knowledge source creation failed: {response.status_code}", Colors.FAIL)

    # Generate company description if not provided
    if not company_desc:
        print_substep("4.2", f"Generating AI company description for {company_name}...")
        company_desc = await generate_claude_completion(
            f"""Generate a comprehensive company description for {company_name}.
Include: company overview, main products/services, target market.
Write 150-250 words in a professional tone.""",
            temperature=0.7
        )
        print_status("✅", f"Company description generated ({len(company_desc)} chars)", Colors.OKGREEN)

    # Generate KB articles
    print_substep("4.3", f"Generating {num_articles} knowledge articles using Claude AI...")
    print_substep("", f"This may take 30-60 seconds depending on the number of articles...")
    articles_prompt = f"""You are an expert content writer for a company knowledge base.

Return a single valid JSON array of {num_articles} FAQ articles for: {company_name}

Each article must have:
- A clear, question-style title in the "name" field
- A detailed body (120–200 words) in the "content" field
- The same "knowledge_source_id": "demosource"
- A string "id" from "1" to "{num_articles}"

Company description: {company_desc}

CRITICAL: Respond with **one single JSON array only**. No markdown. No text outside JSON.

[
  {{"id": "1", "name": "Question 1?", "content": "120-200 word answer...", "knowledge_source_id": "demosource"}},
  ...{num_articles} objects total...
]"""

    articles_response = await generate_claude_completion(articles_prompt, temperature=0.5, max_tokens=8000)

    # Clean Claude markdown
    cleaned = articles_response.strip()

    # Debug: Log raw response info
    print_status("DEBUG", f"Claude response length: {len(cleaned)} chars", Colors.WARNING)
    print_status("DEBUG", f"First 200 chars: {cleaned[:200]}", Colors.WARNING)
    print_status("DEBUG", f"Last 200 chars: {cleaned[-200:]}", Colors.WARNING)

    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]
    cleaned = cleaned.strip()

    # Debug: Log cleaned response info
    print_status("DEBUG", f"After cleaning, length: {len(cleaned)} chars", Colors.WARNING)
    print_status("DEBUG", f"After cleaning, first 200: {cleaned[:200]}", Colors.WARNING)
    print_status("DEBUG", f"After cleaning, last 200: {cleaned[-200:]}", Colors.WARNING)

    try:
        articles = json.loads(cleaned)
    except json.JSONDecodeError as e:
        print_status("⚠️", f"JSON parse failed at position {e.pos} - retrying with shorter content...", Colors.WARNING)

        # Save full response to file for inspection
        try:
            with open("/tmp/claude_response_error.txt", "w") as f:
                f.write(cleaned)
        except:
            pass

        # Retry with shorter article content to avoid token limit truncation
        retry_prompt = f"""You are an expert content writer for a company knowledge base.

Return a single valid JSON array of {num_articles} FAQ articles for: {company_name}

Each article must have:
- A clear, question-style title in the "name" field
- A concise body (60-80 words MAX) in the "content" field
- The same "knowledge_source_id": "demosource"
- A string "id" from "1" to "{num_articles}"

Company description: {company_desc}

CRITICAL: Respond with **one single JSON array only**. No markdown. No text outside JSON. Keep content SHORT.

[
  {{"id": "1", "name": "Question 1?", "content": "60-80 word answer.", "knowledge_source_id": "demosource"}},
  ...{num_articles} objects total...
]"""

        print_status("DEBUG", f"Retrying with shorter content prompt...", Colors.WARNING)
        retry_response = await generate_claude_completion(retry_prompt, temperature=0.5, max_tokens=8000)

        retry_cleaned = retry_response.strip()
        if retry_cleaned.startswith("```json"):
            retry_cleaned = retry_cleaned[7:]
        if retry_cleaned.startswith("```"):
            retry_cleaned = retry_cleaned[3:]
        if retry_cleaned.endswith("```"):
            retry_cleaned = retry_cleaned[:-3]
        retry_cleaned = retry_cleaned.strip()

        try:
            articles = json.loads(retry_cleaned)
            print_status("✅", f"Retry succeeded - parsed {len(articles)} articles", Colors.OKGREEN)
        except json.JSONDecodeError as e2:
            print_status("❌", f"Retry also failed at position {e2.pos}", Colors.FAIL)
            raise ValueError(f"Failed to parse knowledge articles JSON after retry. Check logs for details.")

    print_status("✅", f"Generated {len(articles)} articles", Colors.OKGREEN)

    # Upload articles
    print_substep("4.4", f"Uploading {len(articles)} articles to Ada knowledge base...")
    print_substep("", "Using bulk upload API endpoint...")
    async with httpx.AsyncClient() as client:
        try:
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
            print_status("✅", f"Uploaded {len(articles)} articles", Colors.OKGREEN)
        except httpx.HTTPStatusError as e:
            print_status("❌", f"Failed to upload articles: HTTP {e.response.status_code}", Colors.FAIL)
            raise ValueError(f"Ada API returned HTTP {e.response.status_code}. Check Ada API key and permissions.")
        except Exception as e:
            print_status("❌", f"Failed to upload articles", Colors.FAIL)
            raise ValueError(f"Error uploading articles to Ada: {type(e).__name__}")

    return company_desc, articles

async def add_website_knowledge_source(bot_handle: str, company_name: str, company_website: Optional[str] = None, page=None, should_close_browser: bool = True) -> bool:
    """Add company website as a knowledge source using Playwright.

    Args:
        bot_handle: Bot handle
        company_name: Company name
        company_website: Optional website URL (inferred if not provided)
        page: Optional existing Playwright page (for session reuse)
        should_close_browser: Whether to close browser when done
    """
    print_header("🌐 PHASE 4B: Website Knowledge Source")

    # Infer company website if not provided
    if not company_website:
        print_substep("4B.1", f"Inferring company website URL for {company_name}...")
        # Generate likely website URL
        company_slug = company_name.lower().replace(" ", "").replace("'", "")
        company_website = f"https://{company_slug}.com"
        print_substep("", f"Using inferred URL: {company_website}")
    else:
        print_substep("4B.1", f"Using provided website: {company_website}")

    print_substep("4B.2", "Adding website as knowledge source via Ada dashboard...")
    print_substep("", f"This triggers Ada's web scraper to index the site")

    from playwright.async_api import async_playwright

    playwright_context = None
    browser = None

    try:
        if not page:
            print_substep("4B.3", "Launching browser (headless)...")
            playwright_context = async_playwright()
            p = await playwright_context.__aenter__()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            context.set_default_timeout(300000)  # 5-minute timeout
            page = await context.new_page()
        else:
            print_substep("4B.3", "Reusing existing browser session...")
            page.set_default_timeout(300000)

        # Navigate to homepage first (not knowledge page) to handle login properly
        print_substep("4B.4", f"Navigating to Ada dashboard...")
        await page.goto(f"https://{bot_handle}.ada.support/", timeout=30000)
        await asyncio.sleep(2)

        # Check if we need to login
        try:
            # Try to detect if we're on login page
            await page.wait_for_selector('input[placeholder="lovelace@ada.support"]', timeout=3000)
            print_substep("4B.5", "Login required - filling credentials...")
            await page.fill('input[placeholder="lovelace@ada.support"]', ADA_EMAIL)
            await page.fill('input[name="password"]', ADA_PASSWORD)
            await page.click('button:has-text("Log in")')
            print_substep("", "Waiting for login to complete...")
            await asyncio.sleep(4)
        except:
            print_substep("4B.5", "Already logged in")

        # Now navigate to knowledge page
        print_substep("4B.6", f"Navigating to knowledge page...")
        await page.goto(f"https://{bot_handle}.ada.support/content/knowledge", timeout=30000)
        await asyncio.sleep(3)

        # Click "Add source"
        print_substep("4B.7", "Clicking 'Add source' button...")
        await page.click('button:has-text("Add source")')
        await asyncio.sleep(2)

        # Click "Website" option (use .last to avoid multiple matches)
        print_substep("4B.8", "Selecting 'Website' source type...")
        await page.locator('text=Website').last.click()
        await asyncio.sleep(2)

        # Fill source name and URL using role-based selectors
        print_substep("4B.9", f"Filling source name and URL...")
        textboxes = await page.get_by_role('textbox').all()
        print_substep("", f"Found {len(textboxes)} input fields")

        # Skip first textbox (search box), fill source name in second
        await textboxes[1].fill(f"{company_name} Website")
        await asyncio.sleep(1)

        # Fill URL in third textbox
        await textboxes[2].fill(company_website)
        await asyncio.sleep(1)

        # Click "Add" button with force to bypass modal mask
        print_substep("4B.10", "Clicking 'Add' to kick off web scraping...")
        await page.click('button:has-text("Add")', force=True)
        await asyncio.sleep(3)

        print_status("✅", f"Website source added: {company_website}", Colors.OKGREEN)
        print_substep("", "Ada's web scraper is now indexing the site in the background")

        return True

    except Exception as e:
        print_status("⚠️", f"Website source addition failed (non-critical): {e}", Colors.WARNING)
        print_substep("", "Continuing with generated articles only")
        return False
    finally:
        if should_close_browser and browser:
            await browser.close()
        if playwright_context:
            await playwright_context.__aexit__(None, None, None)

async def generate_questions(company_name: str, articles: List[Dict], num_questions: int = 70) -> List[str]:
    """Generate customer questions based on knowledge articles."""
    print_header("❓ PHASE 5: Question Generation")

    print_substep("5.1", f"Preparing context from {len(articles)} knowledge articles...")
    articles_text = "\n\n".join([f"Article {a['id']}: {a['name']}\n{a['content']}" for a in articles])
    print_substep("", f"Context length: {len(articles_text)} characters")

    print_substep("5.2", f"Calling Claude AI to generate {num_questions} questions...")
    print_substep("", "Using temperature=0.7 for creative variation")

    questions_prompt = f"""Generate exactly {num_questions} realistic customer questions for {company_name}.

Knowledge Base:
{articles_text}

Return ONLY a JSON object:
{{"question_1": "How can I...", "question_2": "What is...", ... "question_{num_questions}: "When do..."}}

No markdown. No text outside JSON."""

    questions_response = await generate_claude_completion(questions_prompt, temperature=0.7, max_tokens=4000)

    print_substep("5.3", "Parsing and cleaning Claude response...")
    cleaned = questions_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        questions_obj = json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        print_status("❌", "Failed to parse questions JSON from Claude", Colors.FAIL)
        raise ValueError("Failed to parse customer questions JSON. Check logs for details.")

    questions = [questions_obj[k] for k in sorted(questions_obj.keys(), key=lambda x: int(x.split('_')[1]))]
    questions = questions[:num_questions]

    print_status("✅", f"Generated {len(questions)} questions", Colors.OKGREEN)
    print_substep("", f"Sample: \"{questions[0][:60]}...\"")
    return questions

async def create_beeceptor_endpoints(bot_handle: str, company_name: str, num_actions: int = 2) -> tuple[bool, List[Dict]]:
    """Create Beeceptor API endpoints and return action configurations.

    Args:
        bot_handle: Bot handle for endpoint path namespacing
        company_name: Company name for industry detection
        num_actions: Number of actions/endpoints to generate (default: 2)
    """
    print_header("📡 PHASE 6: Beeceptor Endpoint Creation")

    num_actions = max(1, num_actions)  # At least 1
    print_substep("6.1", "Generating industry-specific mock API endpoint configurations using Claude AI...")
    print_substep("", f"Creating {num_actions} mock endpoints for: {bot_handle}")

    # Build dynamic JSON schema for N rules and N actions
    rules_schema = "\n".join([
        f'    "use_case_{i}_rule": {{\n'
        f'      "enabled": true,\n'
        f'      "mock": true,\n'
        f'      "delay": 0,\n'
        f'      "match": {{"method": "GET or POST", "value": "/{bot_handle}/meaningful_endpoint_name_{i}", "operator": "SW"}},\n'
        f'      "send": {{"status": 200, "body": "realistic JSON response as escaped string", "headers": {{"Content-Type": "application/json"}}, "templated": false}}\n'
        f'    }}'
        for i in range(1, num_actions + 1)
    ])
    actions_schema = "\n".join([
        f'    {{\n'
        f'      "name": "Descriptive action {i} name",\n'
        f'      "description": "What this action does for the customer",\n'
        f'      "url": "https://ada-demo.proxy.beeceptor.com/{bot_handle}/meaningful_endpoint_name_{i}",\n'
        f'      "headers": [],\n'
        f'      "inputs": [],\n'
        f'      "outputs": [{{"id": "output{i}", "name": "output", "key": "*", "is_visible_to_llm": true, "save_as_variable": false, "variable_name": ""}}],\n'
        f'      "request_body": "",\n'
        f'      "content_type": "json",\n'
        f'      "method": "GET or POST"\n'
        f'    }}'
        for i in range(1, num_actions + 1)
    ])

    endpoints_prompt = f"""You are creating mock API endpoints for {company_name}. First, identify what industry this company is in (e.g., e-commerce/retail, banking, healthcare, telecommunications, insurance, etc.).

Then create {num_actions} realistic Beeceptor rule configurations that represent common customer support use cases for that industry. Each use case should be distinct and cover a different customer need.

Examples by industry:
- E-commerce/Retail: order_tracking, product_availability, return_status, loyalty_points
- Banking: account_balance, transaction_history, card_activation, loan_status
- Healthcare: appointment_scheduling, prescription_status, test_results, referral_status
- Telecommunications: plan_details, usage_info, service_status, bill_summary
- Insurance: claim_status, policy_details, coverage_check, renewal_quote
- Cloud Hosting/VPS: server_status, restart_server, ticket_status, invoice_lookup

For {company_name}, create {num_actions} endpoints with:
1. Descriptive endpoint paths (not generic like "status_check")
2. Realistic response bodies with relevant fields for that industry
3. Appropriate HTTP methods (GET for queries, POST for actions)
4. Each endpoint should be a genuinely distinct customer support use case

Return ONLY this JSON structure with NO markdown formatting:
{{
  "industry": "detected industry name",
  "result": {{
{rules_schema}
  }},
  "ada_actions": [
{actions_schema}
  ]
}}"""

    endpoints_response = await generate_claude_completion(endpoints_prompt, temperature=0.7, max_tokens=500 * num_actions + 1000)

    print_substep("6.2", "Parsing Claude response and extracting rules...")
    cleaned = endpoints_response.strip()
    if cleaned.startswith("```json"):
        cleaned = cleaned[7:]
    if cleaned.startswith("```"):
        cleaned = cleaned[3:]
    if cleaned.endswith("```"):
        cleaned = cleaned[:-3]

    try:
        endpoints = json.loads(cleaned.strip())
    except json.JSONDecodeError as e:
        print_status("❌", "Failed to parse endpoints JSON from Claude", Colors.FAIL)
        raise ValueError("Failed to parse Beeceptor endpoints JSON. Check logs for details.")

    industry = endpoints.get("industry", "unknown")
    print_substep("", f"Detected industry: {industry}")

    # Post all rules to Beeceptor dynamically
    rules = endpoints.get("result", {})
    async with httpx.AsyncClient() as client:
        for i, (rule_key, rule_value) in enumerate(rules.items(), 1):
            rule_json = json.dumps(rule_value)
            endpoint_path = rule_value["match"]["value"]
            method = rule_value["match"]["method"]
            print_substep(f"6.{i + 2}", f"Posting rule #{i} to Beeceptor API ({method} {endpoint_path})...")
            await client.post(
                "https://api.beeceptor.com/api/v1/endpoints/ada-demo/rules",
                headers={"Authorization": BEECEPTOR_TOKEN, "Content-Type": "application/json"},
                content=rule_json,
                timeout=30.0
            )

    print_status("✅", f"Created {len(rules)} Beeceptor endpoints", Colors.OKGREEN)
    print_substep("", "View at: https://app.beeceptor.com/console/ada-demo")

    # Return the Ada action configurations for import
    ada_actions = endpoints.get("ada_actions", [])

    if ada_actions:
        print_substep("", f"Generated {len(ada_actions)} Ada action configs:")
        for action in ada_actions:
            print_substep("", f"  • {action['name']}: {action['method']} {action['url']}")

    return True, ada_actions

async def create_conversations(
    base_url: str,
    api_key: str,
    questions: List[str],
    num_conversations: Optional[int] = None
) -> tuple[str, int]:
    """Create channel and conversations."""
    print_header("💬 PHASE 7: Conversations Creation")

    # Create channel
    print_substep("7.1", "Creating messaging channel in Ada...")
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{base_url}/api/v2/channels/",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"name": "Demo_Channel", "description": "Automated demo channel", "modality": "messaging"},
            timeout=30.0
        )
        response.raise_for_status()
        channel_id = response.json()["id"]
        print_status("✅", f"Channel created: {channel_id}", Colors.OKGREEN)

    # Create conversations
    if num_conversations is None:
        num_conversations = len(questions)

    questions_to_use = questions[:num_conversations]

    print_substep("7.2", f"Creating {len(questions_to_use)} conversations (this will take ~{len(questions_to_use) * 0.5:.0f}s)...")
    print_substep("", "Each conversation = 1 new conversation + 1 end-user message")

    successful = 0
    failed = 0

    async with httpx.AsyncClient() as client:
        for i, question in enumerate(questions_to_use, 1):
            try:
                print_substep("", f"[{i}/{len(questions_to_use)}] Creating conversation: \"{question[:50]}...\"")
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
                    print_status("✓", f"{i}/{len(questions_to_use)} conversations created", Colors.OKGREEN)

                await asyncio.sleep(0.5)  # Rate limiting

            except Exception as e:
                failed += 1
                print_status("✗", f"Conversation {i} failed: {e}", Colors.FAIL)

    print_status("✅", f"Created {successful} conversations", Colors.OKGREEN)
    if failed > 0:
        print_status("⚠️", f"{failed} conversations failed", Colors.WARNING)

    return channel_id, successful

async def import_actions_to_ada(bot_handle: str, ada_actions: List[Dict], page=None, should_close_browser: bool = True) -> bool:
    """Import actions into Ada using Playwright automation.

    Args:
        bot_handle: Bot handle
        ada_actions: List of action configurations to import
        page: Optional existing Playwright page (for session reuse)
        should_close_browser: Whether to close browser when done
    """
    print_header("🔌 PHASE 8: Ada Action Import")

    if not ada_actions:
        print_status("⚠️", "No actions to import", Colors.WARNING)
        return False

    print_substep("8.1", f"Importing {len(ada_actions)} actions into Ada dashboard...")
    print_substep("", f"Target: https://{bot_handle}.ada.support/content/actions/new")

    from playwright.async_api import async_playwright

    playwright_context = None
    browser = None

    try:
        if not page:
            print_substep("8.2", "Launching Chromium browser (headless)...")
            playwright_context = async_playwright()
            p = await playwright_context.__aenter__()
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            context.set_default_timeout(300000)  # 5-minute timeout
            page = await context.new_page()
        else:
            print_substep("8.2", "Reusing existing browser session...")
            page.set_default_timeout(300000)

        # Navigate to homepage and login if needed
        print_substep("8.3", f"Navigating to Ada dashboard...")
        await page.goto(f"https://{bot_handle}.ada.support/", timeout=60000)
        await asyncio.sleep(2)

        # Check if we need to login
        try:
            await page.wait_for_selector('input[placeholder="lovelace@ada.support"]', timeout=3000)
            print_substep("8.4", "Login required - filling credentials...")
            await page.fill('input[placeholder="lovelace@ada.support"]', ADA_EMAIL)
            await page.fill('input[name="password"]', ADA_PASSWORD)
            await page.click('button:has-text("Log in")')
            print_substep("", "Waiting for login to complete...")
            await asyncio.sleep(4)
        except:
            print_substep("8.4", "Already logged in")

        # Import each action
        for i, action in enumerate(ada_actions, 1):
            print_substep("", f"[{i}/{len(ada_actions)}] Importing action: {action['name']}")

            # Navigate to new action page
            print_substep("8.5", "Navigating to /content/actions/new...")
            await page.goto(f"https://{bot_handle}.ada.support/content/actions/new")
            await asyncio.sleep(3)

            # Click "Import Action" button
            print_substep("8.6", "Clicking 'Import Action' button...")
            await page.click('button:has-text("Import Action")')
            await asyncio.sleep(2)

            # Paste action JSON in the correct format
            print_substep("8.7", "Pasting action JSON into import modal...")

            # Ensure action has the correct format with all required fields
            action_to_import = {
                "name": action.get("name", ""),
                "description": action.get("description", ""),
                "url": action.get("url", ""),
                "headers": action.get("headers", []),
                "inputs": action.get("inputs", []),
                "outputs": action.get("outputs", [{
                    "name": "output",
                    "key": "*",
                    "is_visible_to_llm": True,
                    "save_as_variable": False,
                    "variable_name": ""
                }]),
                "request_body": action.get("request_body", ""),
                "content_type": action.get("content_type", "json"),
                "method": action.get("method", "GET")
            }

            action_json = json.dumps(action_to_import)

            # Fill the textarea in the modal
            textarea = page.locator('textarea').first
            await textarea.fill(action_json)
            await asyncio.sleep(2)

            # Click "Import" button in modal
            print_substep("8.8", "Submitting action import...")
            import_button = page.locator('button:has-text("Import")').last
            await import_button.click()
            await asyncio.sleep(3)

            # Click "Save and make active" button
            print_substep("8.9", "Saving and activating action...")
            await page.click('button:has-text("Save and make active")')
            await asyncio.sleep(3)

            print_status("✓", f"Action '{action['name']}' imported and activated", Colors.OKGREEN)

        print_status("✅", f"Imported {len(ada_actions)} actions into Ada", Colors.OKGREEN)
        return True

    except Exception as e:
        print_status("❌", f"Action import failed: {e}", Colors.FAIL)
        return False
    finally:
        if should_close_browser and browser:
            await browser.close()
        if playwright_context:
            await playwright_context.__aexit__(None, None, None)

async def provision_demo(
    company_name: str,
    ada_api_key: Optional[str] = None,
    auto_retrieve_key: bool = False,
    company_description: Optional[str] = None,
    company_website: Optional[str] = None,
    num_articles: int = 10,
    num_questions: int = 70,
    num_conversations: Optional[int] = None,
    num_actions: int = 2,
    dry_run: bool = False,
    progress_callback: Optional[callable] = None
) -> Dict[str, Any]:
    """
    Main provisioning workflow.

    Args:
        company_name: Name of the company
        ada_api_key: Manual Ada API key (if provided)
        auto_retrieve_key: Automatically retrieve API key via Playwright
        company_description: Optional manual company description
        company_website: Optional company website URL to scrape for knowledge
        num_articles: Number of knowledge articles to generate
        num_questions: Number of customer questions to generate
        num_conversations: Number of conversations to create (defaults to num_questions)
        num_actions: Number of Beeceptor mock API actions to create (default: 2)
        dry_run: If True, only validate and show what would be done
        progress_callback: Optional callback function to report progress updates

    Returns:
        Dictionary with provisioning results
    """

    def update_progress(phase: int, message: str):
        """Update progress if callback is provided."""
        if progress_callback:
            progress_callback(phase, message)
    start_time = datetime.now()

    print_header("🚀 ADA AGENT PROVISIONING")
    print(f"Company: {Colors.BOLD}{company_name}{Colors.ENDC}")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    if dry_run:
        print_status("🔍", "DRY RUN MODE - No changes will be made", Colors.WARNING)

    # Validate environment
    if not ANTHROPIC_API_KEY:
        error_msg = "ANTHROPIC_API_KEY not set in environment"
        print_status("❌", error_msg, Colors.FAIL)
        return {"success": False, "error": error_msg}

    print_status("✓", f"Anthropic API key: {ANTHROPIC_API_KEY[:15]}...", Colors.OKGREEN)

    # Generate bot handle
    print_header("📝 PHASE 1: Bot Handle Generation")
    update_progress(1, "Generating bot handle...")
    bot_handle = generate_bot_handle(company_name)
    print_status("✅", f"Bot handle: {bot_handle}", Colors.OKGREEN)
    update_progress(1, f"Bot handle generated: {bot_handle}")

    if dry_run:
        print_status("🔍", "Would create bot and retrieve API key", Colors.WARNING)
        print_status("🔍", f"Would generate {num_articles} articles and {num_questions} questions", Colors.WARNING)
        print_status("🔍", f"Would create {num_conversations or num_questions} conversations", Colors.WARNING)
        print_status("🔍", f"Would create {num_actions} Beeceptor mock API actions", Colors.WARNING)
        return {
            "success": True,
            "dry_run": True,
            "bot_handle": bot_handle,
            "bot_url": f"https://{bot_handle}.ada.support"
        }

    # Clone bot
    print_header("🔄 PHASE 2: Bot Cloning")
    update_progress(2, "Cloning bot from template...")
    clone_success = await clone_bot(bot_handle)
    if not clone_success:
        print_status("❌", "Bot cloning failed", Colors.FAIL)
        return {"success": False, "error": "Bot cloning failed"}

    print_substep("2.2", "Waiting 30 seconds for Ada to provision the new bot...")
    print_substep("", "This allows Ada's infrastructure to complete the cloning process")
    update_progress(2, "Bot cloned, waiting for provisioning...")
    await asyncio.sleep(30)

    # Handle API key
    base_url = f"https://{bot_handle}.ada.support"
    api_key = None

    if ada_api_key:
        # Manual API key provided - use it directly
        print_status("✓", f"Using provided API key: {ada_api_key[:12]}...{ada_api_key[-4:]}", Colors.OKGREEN)
        api_key = ada_api_key
        update_progress(3, "Using provided API key")

        # Create knowledge base first
        update_progress(4, "Creating knowledge base...")
        company_desc, articles = await create_knowledge_base(
            base_url, api_key, company_name, company_description, num_articles
        )
        update_progress(4, f"Knowledge base created with {len(articles)} articles")

        # Generate questions
        update_progress(5, "Generating customer questions...")
        questions = await generate_questions(company_name, articles, num_questions)
        update_progress(5, f"Generated {len(questions)} questions")

        # Create Beeceptor endpoints
        update_progress(6, "Creating Beeceptor endpoints...")
        beeceptor_success, ada_actions = await create_beeceptor_endpoints(bot_handle, company_name, num_actions)
        update_progress(6, "Beeceptor endpoints created")

        # Now run Playwright tasks (website + actions only)
        try:
            _, website_success, actions_success = await run_playwright_tasks(
                bot_handle, company_name, company_website, ada_actions
            )
        except Exception as e:
            print_status("⚠️", f"Playwright tasks skipped: {e}", Colors.WARNING)
            website_success = False
            actions_success = False

    elif auto_retrieve_key:
        # Auto-retrieve mode: need to get API key first, then use unified session
        # First, just get Beeceptor actions ready
        update_progress(3, "Preparing Beeceptor endpoints for action import...")
        beeceptor_success, ada_actions = await create_beeceptor_endpoints(bot_handle, company_name, num_actions)

        # Run unified Playwright session: API key + website + actions
        update_progress(3, "Running unified Playwright session...")
        api_key, website_success, actions_success = await run_playwright_tasks(
            bot_handle, company_name, company_website, ada_actions
        )

        if not api_key:
            print_status("❌", "Failed to retrieve API key automatically", Colors.FAIL)
            return {"success": False, "error": "API key retrieval failed"}

        update_progress(3, "API key retrieved successfully")

        # Now create knowledge base
        update_progress(4, "Creating knowledge base...")
        company_desc, articles = await create_knowledge_base(
            base_url, api_key, company_name, company_description, num_articles
        )
        update_progress(4, f"Knowledge base created with {len(articles)} articles")

        # Generate questions
        update_progress(5, "Generating customer questions...")
        questions = await generate_questions(company_name, articles, num_questions)
        update_progress(5, f"Generated {len(questions)} questions")

    else:
        print_status("❌", "No API key provided and auto-retrieve not enabled", Colors.FAIL)
        return {"success": False, "error": "No API key available"}

    # Create conversations
    update_progress(7, f"Creating {num_conversations or len(questions)} conversations...")
    channel_id, conversations_created = await create_conversations(
        base_url, api_key, questions, num_conversations
    )
    update_progress(7, f"Created {conversations_created} conversations")

    # Calculate duration
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print summary
    print_header("🎉 PROVISIONING COMPLETE!")
    print(f"{Colors.OKGREEN}📋 Summary:{Colors.ENDC}")
    print(f"   • Company: {company_name}")
    print(f"   • Bot Handle: {bot_handle}")
    print(f"   • Bot URL: {Colors.OKBLUE}https://{bot_handle}.ada.support{Colors.ENDC}")
    print(f"   • API Key: {api_key[:12]}...{api_key[-4:]}")
    print(f"   • Knowledge Articles: {len(articles)}")
    print(f"   • Questions Generated: {len(questions)}")
    print(f"   • Conversations Created: {conversations_created}/{num_conversations or len(questions)}")
    print(f"   • Actions Imported: {'Yes' if 'actions_success' in locals() and actions_success else 'No'}")
    print(f"   • Website Source Added: {'Yes' if 'website_success' in locals() and website_success else 'No'}")
    print(f"   • Channel ID: {channel_id}")
    print(f"   • Duration: {duration:.1f} seconds")
    print(f"   • Beeceptor: {Colors.OKBLUE}https://app.beeceptor.com/console/ada-demo{Colors.ENDC}")
    print(f"   • MCP Server: {'Registered — restart Claude to activate' if 'mcp_registered' in locals() and mcp_registered else 'Already registered or skipped'}")
    print(f"\n{Colors.OKGREEN}{'='*80}{Colors.ENDC}\n")

    # Register as MCP server in Claude desktop
    mcp_registered = register_mcp_server(bot_handle)

    return {
        "success": True,
        "company_name": company_name,
        "bot_handle": bot_handle,
        "bot_url": f"https://{bot_handle}.ada.support",
        "api_key": api_key,
        "articles_count": len(articles),
        "article_titles": [a.get("name", "") for a in articles],
        "questions_count": len(questions),
        "conversations_created": conversations_created,
        "channel_id": channel_id,
        "duration_seconds": duration,
        "mcp_registered": mcp_registered
    }

def register_mcp_server(bot_handle: str) -> bool:
    """
    Add the provisioned bot as an MCP server in Claude desktop config.
    Edits ~/Library/Application Support/Claude/claude_desktop_config.json.
    Returns True if added, False if already present or on error.
    """
    config_path = Path.home() / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json"
    if not config_path.exists():
        print_status("⚠️", f"Claude desktop config not found at {config_path} — skipping MCP registration", Colors.WARNING)
        return False

    try:
        with open(config_path) as f:
            config = json.load(f)
    except Exception as e:
        print_status("⚠️", f"Could not read Claude desktop config: {e}", Colors.WARNING)
        return False

    servers = config.setdefault("mcpServers", {})
    if bot_handle in servers:
        print_status("ℹ️", f"MCP server '{bot_handle}' already registered in Claude desktop config", Colors.OKCYAN)
        return False

    servers[bot_handle] = {
        "command": "npx",
        "args": ["mcp-remote", f"https://{bot_handle}.ada.support/api/mcp/oauth"]
    }

    try:
        with open(config_path, "w") as f:
            json.dump(config, f, indent=4)
        print_status("✅", f"Registered '{bot_handle}' as MCP server in Claude desktop config", Colors.OKGREEN)
        print_status("🔄", "Restart Claude to load the new MCP connection", Colors.WARNING)
        return True
    except Exception as e:
        print_status("⚠️", f"Could not write Claude desktop config: {e}", Colors.WARNING)
        return False


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Ada Agent Provisioning - Automated demo setup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # With manual Ada API key
  python3 provision.py --company "Pepsi" --ada-key "abc123..."

  # With automatic key retrieval
  python3 provision.py --company "Coca-Cola" --auto

  # With custom settings
  python3 provision.py --company "Starbucks" --ada-key "xyz789..." --articles 15 --questions 100

  # Dry run (validate only)
  python3 provision.py --company "Nike" --ada-key "test123" --dry-run
        """
    )

    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--ada-key", help="Ada API key (manual)")
    parser.add_argument("--auto", action="store_true", help="Auto-retrieve API key via Playwright")
    parser.add_argument("--description", help="Company description (optional)")
    parser.add_argument("--website", help="Company website URL to scrape (e.g., https://traderjoes.com)")
    parser.add_argument("--articles", type=int, default=10, help="Number of knowledge articles (default: 10)")
    parser.add_argument("--questions", type=int, default=70, help="Number of questions (default: 70)")
    parser.add_argument("--conversations", type=int, help="Number of conversations (default: same as questions)")
    parser.add_argument("--actions", type=int, default=2, help="Number of mock API actions to create via Beeceptor (default: 2)")
    parser.add_argument("--dry-run", action="store_true", help="Validate without making changes")

    args = parser.parse_args()

    # Validation
    if not args.ada_key and not args.auto:
        print_status("❌", "Must provide either --ada-key or --auto", Colors.FAIL)
        sys.exit(1)

    # Run provisioning
    try:
        result = asyncio.run(provision_demo(
            company_name=args.company,
            ada_api_key=args.ada_key,
            auto_retrieve_key=args.auto,
            company_description=args.description,
            company_website=args.website,
            num_articles=args.articles,
            num_questions=args.questions,
            num_conversations=args.conversations,
            num_actions=args.actions,
            dry_run=args.dry_run
        ))

        if result["success"]:
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print_status("\n⚠️", "Provisioning interrupted by user", Colors.WARNING)
        sys.exit(1)
    except Exception as e:
        print_status("❌", f"Provisioning failed: {e}", Colors.FAIL)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
