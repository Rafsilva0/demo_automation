"""
Playwright service for Ada dashboard automation.

Automates API key retrieval from Ada platform, replacing manual 28-day wait.
Also handles action import via UI since API doesn't support it.
"""

import asyncio
import json
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext
import structlog

logger = structlog.get_logger()


class PlaywrightService:
    """Automates Ada dashboard interactions using Playwright."""

    def __init__(
        self,
        headless: bool = True,
        timeout: int = 60000,  # Increased from 30s to 60s
        email: str = "scteam@ada.support",
        password: str = "Adalovelace123!"
    ):
        """
        Initialize Playwright service.

        Args:
            headless: Run browser in headless mode
            timeout: Default timeout in milliseconds
            email: Login email for Ada dashboard
            password: Login password for Ada dashboard
        """
        self.headless = headless
        self.timeout = timeout
        self.email = email
        self.password = password

    async def get_ada_api_key(
        self,
        bot_handle: str,
        max_retries: int = 3
    ) -> str:
        """
        Retrieve API key from Ada dashboard using browser automation.

        Flow:
        1. Navigate to https://{bot_handle}.ada.support/
        2. Login with credentials
        3. Navigate to /platform/apis
        4. Click "New API Key" button
        5. Fill name field with "automation-key"
        6. Click "Generate key" button
        7. Extract API key from plain text field
        8. Return API key

        Args:
            bot_handle: Bot handle (e.g., "pepsi-ai-agent-demo")
            max_retries: Maximum retry attempts if automation fails

        Returns:
            API key string (e.g., "ada_v1_xxx...")

        Raises:
            Exception: If automation fails after all retries
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "playwright_api_key_retrieval_attempt",
                    bot_handle=bot_handle,
                    attempt=attempt,
                    max_retries=max_retries
                )

                api_key = await self._retrieve_api_key(bot_handle)

                logger.info(
                    "playwright_api_key_retrieved",
                    bot_handle=bot_handle,
                    attempt=attempt,
                    key_preview=f"{api_key[:12]}..." if api_key else None
                )

                return api_key

            except Exception as e:
                last_error = e
                logger.warning(
                    "playwright_api_key_attempt_failed",
                    bot_handle=bot_handle,
                    attempt=attempt,
                    error=str(e)
                )

                if attempt < max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(
                        "playwright_retrying",
                        wait_seconds=wait_time
                    )
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error(
            "playwright_api_key_retrieval_failed",
            bot_handle=bot_handle,
            error=str(last_error)
        )
        raise Exception(
            f"Failed to retrieve API key after {max_retries} attempts: {last_error}"
        )

    async def _retrieve_api_key(self, bot_handle: str) -> str:
        """
        Internal method to perform single API key retrieval attempt.

        Args:
            bot_handle: Bot handle

        Returns:
            API key string
        """
        async with async_playwright() as p:
            # Launch browser
            browser: Browser = await p.chromium.launch(headless=self.headless)

            try:
                # Create context with timeout
                context: BrowserContext = await browser.new_context()
                context.set_default_timeout(self.timeout)

                page: Page = await context.new_page()

                # Step 1: Navigate to login page
                login_url = f"https://{bot_handle}.ada.support/"
                logger.info("playwright_navigating", url=login_url)
                await page.goto(login_url, wait_until="networkidle")

                # Step 2: Fill email
                logger.info("playwright_filling_email")
                email_selector = 'input[type="email"], input[name="email"]'
                await page.fill(email_selector, self.email)

                # Step 3: Fill password
                logger.info("playwright_filling_password")
                password_selector = 'input[type="password"], input[name="password"]'
                await page.fill(password_selector, self.password)

                # Step 4: Submit login form
                logger.info("playwright_submitting_login")
                submit_selector = 'button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")'
                await page.click(submit_selector)

                # Wait for navigation after login
                await page.wait_for_load_state("networkidle")

                # Step 5: Navigate to API keys page
                apis_url = f"https://{bot_handle}.ada.support/platform/apis"
                logger.info("playwright_navigating_to_apis", url=apis_url)
                await page.goto(apis_url, wait_until="networkidle")

                # Step 6: Click "New API Key" button
                logger.info("playwright_clicking_new_api_key")
                new_key_button = 'button:has-text("New API Key")'
                await page.click(new_key_button)

                # Wait for modal to appear
                await page.wait_for_timeout(1000)

                # Step 7: Fill name field
                logger.info("playwright_filling_key_name")
                name_input = 'input[name="name"], input[placeholder*="name" i]'
                await page.fill(name_input, "automation-key")

                # Step 8: Click "Generate key" button
                logger.info("playwright_clicking_generate_key")
                generate_button = 'button:has-text("Generate key")'
                await page.click(generate_button)

                # Wait for key to be generated
                await page.wait_for_timeout(2000)

                # Step 9: Extract API key from page
                logger.info("playwright_extracting_api_key")

                # Try multiple selectors for the API key
                api_key = None
                selectors = [
                    'input[readonly]',  # Plain text input field
                    'code',  # Code element
                    'pre',  # Preformatted text
                    'textarea[readonly]',  # Textarea
                    '.api-key',  # Class-based selector
                    '[data-testid="api-key"]',  # Test ID selector
                ]

                for selector in selectors:
                    try:
                        logger.info("playwright_trying_selector", selector=selector)
                        element = await page.wait_for_selector(selector, timeout=5000)
                        if element:
                            # Try getting input value first
                            api_key = await element.input_value() if await element.evaluate('el => el.tagName.toLowerCase()') in ['input', 'textarea'] else None

                            # If not input, get text content
                            if not api_key:
                                api_key = await element.text_content()

                            if api_key and api_key.strip():
                                api_key = api_key.strip()
                                logger.info(
                                    "playwright_api_key_found",
                                    selector=selector,
                                    key_preview=f"{api_key[:12]}..."
                                )
                                break
                            else:
                                logger.info("playwright_selector_matched_but_empty", selector=selector)
                    except Exception as e:
                        logger.info("playwright_selector_failed", selector=selector, error=str(e)[:100])
                        continue

                if not api_key:
                    # Take screenshot for debugging with timeout to avoid hanging
                    screenshot_path = f"/tmp/{bot_handle}_api_key_page.png"
                    try:
                        await page.screenshot(path=screenshot_path, timeout=10000)
                        logger.error(
                            "playwright_api_key_not_found",
                            screenshot=screenshot_path
                        )
                    except Exception as screenshot_error:
                        logger.error(
                            "playwright_screenshot_failed",
                            error=str(screenshot_error)
                        )
                    raise Exception(
                        f"Could not find API key on page. Check logs for details."
                    )

                return api_key

            finally:
                await browser.close()

    async def import_actions(
        self,
        bot_handle: str,
        actions: List[Dict[str, Any]],
        max_retries: int = 3
    ) -> Dict[str, Any]:
        """
        Import multiple actions into Ada dashboard using browser automation.

        Ada API doesn't support action import, so we use Playwright to automate the UI.

        Flow for each action:
        1. Navigate to https://{bot_handle}.ada.support/
        2. Login with credentials (if needed)
        3. Navigate to /content/actions/new
        4. Click "Import Action" button
        5. Paste action JSON into textarea
        6. Click "Import" button in modal
        7. Click "Save and make active" button
        8. Repeat for each action

        Args:
            bot_handle: Bot handle (e.g., "walmart-ai-agent-demo")
            actions: List of action dictionaries with correct Ada format
            max_retries: Maximum retry attempts if automation fails

        Returns:
            Dictionary with results:
            {
                "success": bool,
                "imported_count": int,
                "failed_count": int,
                "actions": [
                    {"name": "Action 1", "status": "success"},
                    {"name": "Action 2", "status": "failed", "error": "..."}
                ]
            }
        """
        last_error = None

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    "playwright_action_import_attempt",
                    bot_handle=bot_handle,
                    action_count=len(actions),
                    attempt=attempt,
                    max_retries=max_retries
                )

                result = await self._import_actions(bot_handle, actions)

                logger.info(
                    "playwright_actions_imported",
                    bot_handle=bot_handle,
                    attempt=attempt,
                    imported_count=result["imported_count"],
                    failed_count=result["failed_count"]
                )

                return result

            except Exception as e:
                last_error = e
                logger.warning(
                    "playwright_action_import_attempt_failed",
                    bot_handle=bot_handle,
                    attempt=attempt,
                    error=str(e)
                )

                if attempt < max_retries:
                    wait_time = 2 ** attempt
                    logger.info("playwright_retrying", wait_seconds=wait_time)
                    await asyncio.sleep(wait_time)

        # All retries exhausted
        logger.error(
            "playwright_action_import_failed",
            bot_handle=bot_handle,
            error=str(last_error)
        )
        raise Exception(
            f"Failed to import actions after {max_retries} attempts: {last_error}"
        )

    async def _import_actions(
        self,
        bot_handle: str,
        actions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Internal method to perform action imports.

        Args:
            bot_handle: Bot handle
            actions: List of action dictionaries

        Returns:
            Dictionary with import results
        """
        results = {
            "success": True,
            "imported_count": 0,
            "failed_count": 0,
            "actions": []
        }

        async with async_playwright() as p:
            browser: Browser = await p.chromium.launch(headless=self.headless)

            try:
                context: BrowserContext = await browser.new_context()
                context.set_default_timeout(self.timeout)
                page: Page = await context.new_page()

                # Step 1: Login
                login_url = f"https://{bot_handle}.ada.support/"
                logger.info("playwright_navigating", url=login_url)
                await page.goto(login_url, wait_until="networkidle")

                # Check if already logged in by looking for login form
                try:
                    await page.wait_for_selector('input[type="email"]', timeout=3000)
                    # Login form found, need to login
                    logger.info("playwright_logging_in")
                    await page.fill('input[type="email"]', self.email)
                    await page.fill('input[type="password"]', self.password)
                    submit_selector = 'button[type="submit"], button:has-text("Sign in"), button:has-text("Log in")'
                    await page.click(submit_selector)
                    await page.wait_for_load_state("networkidle")
                    logger.info("playwright_login_complete")
                except Exception:
                    logger.info("playwright_already_logged_in")

                # Step 2: Import each action
                for action in actions:
                    action_name = action.get("name", "Unknown Action")
                    logger.info("playwright_importing_action", action_name=action_name)

                    try:
                        # Navigate to new action page
                        action_url = f"https://{bot_handle}.ada.support/content/actions/new"
                        await page.goto(action_url, wait_until="networkidle")
                        await asyncio.sleep(2)

                        # Click "Import Action" button
                        logger.info("playwright_clicking_import_button")
                        await page.click('button:has-text("Import Action")')
                        await asyncio.sleep(2)

                        # Fill action JSON
                        logger.info("playwright_filling_action_json")
                        action_json = json.dumps(action)
                        textarea = page.locator('textarea').first
                        await textarea.fill(action_json)
                        await asyncio.sleep(1)

                        # Click "Import" button in modal
                        logger.info("playwright_clicking_modal_import")
                        import_button = page.locator('button:has-text("Import")').last
                        await import_button.click()
                        await asyncio.sleep(3)

                        # Click "Save and make active" button
                        logger.info("playwright_saving_action")
                        await page.click('button:has-text("Save and make active")')
                        await asyncio.sleep(3)

                        logger.info("playwright_action_imported", action_name=action_name)
                        results["imported_count"] += 1
                        results["actions"].append({
                            "name": action_name,
                            "status": "success"
                        })

                    except Exception as e:
                        logger.error(
                            "playwright_action_import_failed",
                            action_name=action_name,
                            error=str(e)
                        )
                        results["failed_count"] += 1
                        results["success"] = False
                        results["actions"].append({
                            "name": action_name,
                            "status": "failed",
                            "error": str(e)
                        })

                        # Take screenshot for debugging with timeout
                        try:
                            screenshot_path = f"/tmp/{bot_handle}_{action_name.replace(' ', '_')}_error.png"
                            await page.screenshot(path=screenshot_path, timeout=10000)
                            logger.info("playwright_error_screenshot", path=screenshot_path)
                        except Exception as screenshot_error:
                            logger.warning("playwright_screenshot_timeout", error=str(screenshot_error))

                return results

            finally:
                await browser.close()


# CLI for testing
if __name__ == "__main__":
    import sys

    async def test_retrieval():
        """Test API key retrieval with a bot handle."""
        if len(sys.argv) < 2:
            print("Usage: python -m app.services.playwright_service <bot_handle>")
            print("Example: python -m app.services.playwright_service pepsi-ai-agent-demo")
            sys.exit(1)

        bot_handle = sys.argv[1]
        service = PlaywrightService(headless=False)  # Visible browser for testing

        try:
            api_key = await service.get_ada_api_key(bot_handle)
            print(f"✅ API Key retrieved: {api_key[:12]}...{api_key[-4:]}")
            print(f"Full key: {api_key}")
        except Exception as e:
            print(f"❌ Failed to retrieve API key: {e}")
            sys.exit(1)

    asyncio.run(test_retrieval())
