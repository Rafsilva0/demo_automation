#!/usr/bin/env python3
"""Update Trader Joe's chat branding with their brand color."""

import asyncio
from playwright.async_api import async_playwright

async def update_traderjoes_branding():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        context.set_default_timeout(60000)
        page = await context.new_page()

        bot_handle = 'traderjoes-ai-agent-demo'
        email = 'scteam@ada.support'
        password = 'Adalovelace123!'
        traderjoes_red = '#D32F2F'  # Trader Joe's brand red

        try:
            print('Step 1: Navigate and login...')
            await page.goto(f'https://{bot_handle}.ada.support/advanced/channels/web-chat')
            await asyncio.sleep(2)

            try:
                await page.wait_for_selector('input[placeholder="lovelace@ada.support"]', timeout=3000)
                await page.fill('input[placeholder="lovelace@ada.support"]', email)
                await page.fill('input[name="password"]', password)
                await page.click('button:has-text("Log in")')
                await asyncio.sleep(4)
                await page.goto(f'https://{bot_handle}.ada.support/advanced/channels/web-chat')
                await asyncio.sleep(3)
            except:
                print('   Already logged in')

            print('\nStep 2: Expanding "Chat window" section...')
            await page.click('text=Chat window')
            await asyncio.sleep(2)

            print(f'\nStep 3: Updating accent color to Trader Joe\'s red ({traderjoes_red})...')
            
            # Click on the color picker (the black square)
            await page.click('div:has-text("Accent color") >> .. >> div[style*="background"]')
            await asyncio.sleep(1)
            await page.screenshot(path='/tmp/color_picker_open.png')
            print('   Color picker opened: /tmp/color_picker_open.png')
            
            # Find and fill the hex input field
            print(f'   Entering hex color: {traderjoes_red}')
            
            # Try different selectors for the hex input
            try:
                # Look for input that might contain the hex value
                hex_input = page.locator('input[value*="#"]').first
                await hex_input.click()
                await hex_input.fill(traderjoes_red)
                await asyncio.sleep(1)
            except:
                print('   Trying alternative selector...')
                # Try finding by placeholder or type
                await page.fill('input[type="text"]', traderjoes_red)
                await asyncio.sleep(1)
            
            await page.screenshot(path='/tmp/color_updated.png')
            print('   Color updated: /tmp/color_updated.png')
            
            # Click outside or press Enter to confirm
            await page.keyboard.press('Enter')
            await asyncio.sleep(2)
            
            print('\nStep 4: Taking final screenshot...')
            await page.screenshot(path='/tmp/branding_final.png', full_page=True)
            print('   Final screenshot: /tmp/branding_final.png')
            
            print('\n✅ Branding updated! Check the preview on the right side.')
            print('   Keeping browser open for 60 seconds to verify...')
            await asyncio.sleep(60)

        except Exception as e:
            print(f'\n❌ Error: {e}')
            await page.screenshot(path='/tmp/error.png')
            raise
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(update_traderjoes_branding())
