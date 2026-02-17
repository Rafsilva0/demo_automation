#!/usr/bin/env python3
"""Test importing an action with correct JSON format."""

import asyncio
import json
from playwright.async_api import async_playwright

async def test_action_import():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        context.set_default_timeout(60000)
        page = await context.new_page()

        bot_handle = 'traderjoes-ai-agent-demo'
        email = 'scteam@ada.support'
        password = 'Adalovelace123!'

        # Correct action format based on your example
        test_action = {
            "name": "Check Product Availability",
            "description": "Check if a specific Trader Joe's product is in stock",
            "url": "https://ada-demo.proxy.beeceptor.com/traderjoes-ai-agent-demo/product_availability",
            "headers": [],
            "inputs": [],
            "outputs": [{
                "name": "output",
                "key": "*",
                "is_visible_to_llm": True,
                "save_as_variable": False,
                "variable_name": ""
            }],
            "request_body": "",
            "content_type": "json",
            "method": "GET"
        }

        try:
            print('Step 1: Navigate and login...')
            await page.goto(f'https://{bot_handle}.ada.support/')
            await asyncio.sleep(2)

            try:
                await page.wait_for_selector('input[placeholder="lovelace@ada.support"]', timeout=3000)
                await page.fill('input[placeholder="lovelace@ada.support"]', email)
                await page.fill('input[name="password"]', password)
                await page.click('button:has-text("Log in")')
                await asyncio.sleep(4)
            except:
                print('   Already logged in')

            print('\nStep 2: Navigate to New Action page...')
            await page.goto(f'https://{bot_handle}.ada.support/content/actions/new')
            await asyncio.sleep(3)

            print('\nStep 3: Click "Import Action" button...')
            await page.click('button:has-text("Import Action")')
            await asyncio.sleep(2)

            print('\nStep 4: Paste action JSON with correct format...')
            action_json = json.dumps(test_action)
            textarea = page.locator('textarea').first
            await textarea.fill(action_json)
            await asyncio.sleep(2)
            await page.screenshot(path='/tmp/json_filled.png')
            print('   Screenshot: /tmp/json_filled.png')

            print('\nStep 5: Click "Import" button in modal...')
            import_button = page.locator('button:has-text("Import")').last
            await import_button.click()
            await asyncio.sleep(3)
            await page.screenshot(path='/tmp/after_import.png', full_page=True)
            print('   Screenshot: /tmp/after_import.png')

            print('\nStep 6: Click "Save and make active" button...')
            await page.click('button:has-text("Save and make active")')
            await asyncio.sleep(3)
            await page.screenshot(path='/tmp/action_saved.png')
            print('   Screenshot: /tmp/action_saved.png')

            print('\n✅ Action imported and saved!')
            await asyncio.sleep(10)

        except Exception as e:
            print(f'\n❌ Error: {e}')
            await page.screenshot(path='/tmp/error.png', full_page=True)
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_action_import())
