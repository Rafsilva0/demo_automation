#!/usr/bin/env python3
"""Test importing an action via JSON in Ada."""

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

        # Sample action JSON to import
        test_action = {
            "name": "Check Store Hours",
            "description": "Get store hours for a Trader Joe's location",
            "url": "https://ada-demo.proxy.beeceptor.com/traderjoes-ai-agent-demo/store_hours",
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

            print('\nStep 2: Navigate to actions page and click New Action...')
            await page.goto(f'https://{bot_handle}.ada.support/content/actions')
            await asyncio.sleep(3)
            await page.click('button:has-text("New Action")')
            await asyncio.sleep(3)

            print('\nStep 3: Click "Import Action" button...')
            await page.click('button:has-text("Import Action")')
            await asyncio.sleep(2)
            await page.screenshot(path='/tmp/import_modal.png', full_page=True)
            print('   Screenshot: /tmp/import_modal.png')

            print('\nStep 4: Looking for textarea or input to paste JSON...')
            # Find the JSON input field
            textareas = await page.locator('textarea').all()
            print(f'   Found {len(textareas)} textareas')
            
            if len(textareas) > 0:
                print('\nStep 5: Pasting action JSON...')
                action_json = json.dumps(test_action, indent=2)
                await textareas[0].fill(action_json)
                await asyncio.sleep(2)
                await page.screenshot(path='/tmp/json_pasted.png', full_page=True)
                print('   Screenshot: /tmp/json_pasted.png')

            print('\nKeeping browser open for 60 seconds to explore...')
            await asyncio.sleep(60)

        except Exception as e:
            print(f'\n❌ Error: {e}')
            await page.screenshot(path='/tmp/error.png', full_page=True)
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(test_action_import())
