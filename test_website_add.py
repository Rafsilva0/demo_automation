#!/usr/bin/env python3
"""Test script to add website knowledge source for Trader Joe's."""

import asyncio
from playwright.async_api import async_playwright

async def test_add_website():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        context.set_default_timeout(60000)
        page = await context.new_page()

        bot_handle = 'traderjoes-ai-agent-demo'
        website = 'https://www.traderjoes.com'
        email = 'scteam@ada.support'
        password = 'Adalovelace123!'

        try:
            print('Step 1: Navigate to homepage and login')
            await page.goto(f'https://{bot_handle}.ada.support/')
            await asyncio.sleep(2)

            print('Step 2: Fill login form')
            await page.fill('input[placeholder="lovelace@ada.support"]', email)
            await page.fill('input[name="password"]', password)
            await page.click('button:has-text("Log in")')
            print('   Waiting for login to complete...')
            await asyncio.sleep(4)

            print('Step 3: Navigate to knowledge page')
            await page.goto(f'https://{bot_handle}.ada.support/content/knowledge')
            await asyncio.sleep(3)

            print('Step 4: Click Add source')
            await page.click('button:has-text("Add source")')
            await asyncio.sleep(2)

            print('Step 5: Select Website')
            await page.locator('text=Website').last.click()
            await asyncio.sleep(2)

            print('Step 6: Fill source name and URL')
            textboxes = await page.get_by_role('textbox').all()
            print(f'   Found {len(textboxes)} textboxes')
            
            # Fill source name (skip first textbox which is search)
            await textboxes[1].fill("Trader Joe's Website")
            await asyncio.sleep(1)
            
            # Fill URL
            await textboxes[2].fill(website)
            await asyncio.sleep(1)

            print('Step 7: Click Add button (with force)')
            await page.screenshot(path='/tmp/before_add_click.png')
            
            # Try force click to bypass modal mask
            await page.click('button:has-text("Add")', force=True)
            print('   Add button clicked!')
            await asyncio.sleep(3)

            print('Step 8: Take final screenshot')
            await page.screenshot(path='/tmp/after_add_click.png')
            print('   Screenshot saved: /tmp/after_add_click.png')

            print(f'\n✅ Success! Website source added for {bot_handle}')
            print('   Check screenshot to verify')
            
            # Wait so we can inspect
            await asyncio.sleep(30)

        except Exception as e:
            print(f'\n❌ Error: {e}')
            await page.screenshot(path='/tmp/error_screenshot.png')
            print('   Error screenshot saved: /tmp/error_screenshot.png')
            raise
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_add_website())
