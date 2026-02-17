#!/usr/bin/env python3
"""Complete branding update for Trader Joe's."""

import asyncio
from playwright.async_api import async_playwright

async def update_full_branding():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        context.set_default_timeout(60000)
        page = await context.new_page()

        bot_handle = 'traderjoes-ai-agent-demo'
        email = 'scteam@ada.support'
        password = 'Adalovelace123!'

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

            print('\nStep 2: Expanding "General" section...')
            await page.click('text=General')
            await asyncio.sleep(2)
            
            print('\nStep 3: Finding and filling Agent name input...')
            # Use get_by_role to find the text input under "Agent name"
            agent_name_inputs = await page.get_by_role('textbox').all()
            print(f'   Found {len(agent_name_inputs)} textbox inputs')
            
            # First textbox should be the Agent name
            await agent_name_inputs[0].fill("Trader Joe's Helper")
            await asyncio.sleep(1)
            print('   Agent name updated')
            
            print('\nStep 4: Enabling Description toggle...')
            # Click the toggle next to Description
            description_section = page.locator('text=Description')
            description_toggle = description_section.locator('..').locator('input[type="checkbox"]')
            is_checked = await description_toggle.is_checked()
            if not is_checked:
                print('   Enabling description...')
                await description_toggle.click()
                await asyncio.sleep(1)
            
            print('\nStep 5: Filling description...')
            # Now fill the textarea (should appear after enabling)
            textareas = await page.locator('textarea').all()
            if len(textareas) > 0:
                await textareas[0].fill("Your friendly Trader Joe's shopping assistant")
                await asyncio.sleep(1)
                print('   Description updated')
            
            await page.screenshot(path='/tmp/general_updated.png', full_page=True)
            print('   Screenshot: /tmp/general_updated.png')
            
            print('\nStep 6: Expanding "Chat window" section...')
            await page.click('text=Chat window')
            await asyncio.sleep(2)
            
            print('\nStep 7: Updating accent color to Trader Joe\'s red (#D32F2F)...')
            color_div = page.locator('text=Accent color').locator('..').locator('div[style*="background"]').first
            await color_div.click()
            await asyncio.sleep(1)
            
            hex_input = page.locator('input[value*="#"]').first
            await hex_input.fill('#D32F2F')
            await page.keyboard.press('Enter')
            await asyncio.sleep(2)
            print('   Accent color updated to #D32F2F')
            
            print('\nStep 8: Scrolling to find Avatar options...')
            await page.evaluate('window.scrollBy(0, 600)')
            await asyncio.sleep(2)
            await page.screenshot(path='/tmp/after_scroll.png', full_page=True)
            print('   Screenshot: /tmp/after_scroll.png')
            
            print('\nStep 9: Looking for Custom icon option...')
            try:
                custom_icon_radio = page.locator('text=Custom icon').locator('..').locator('input[type="radio"]')
                await custom_icon_radio.click()
                await asyncio.sleep(2)
                print('   Selected "Custom icon" option')
                await page.screenshot(path='/tmp/custom_icon_selected.png', full_page=True)
            except Exception as e:
                print(f'   Could not select custom icon: {e}')
            
            print('\nStep 10: SAVING CHANGES...')
            save_button = page.locator('button:has-text("Save changes")')
            await save_button.click()
            await asyncio.sleep(3)
            
            await page.screenshot(path='/tmp/branding_saved.png', full_page=True)
            print('   Screenshot: /tmp/branding_saved.png')
            
            print('\n✅ BRANDING UPDATED AND SAVED!')
            print('   - Agent name: "Trader Joe\'s Helper"')
            print('   - Description: "Your friendly Trader Joe\'s shopping assistant"')
            print('   - Accent color: #D32F2F (Trader Joe\'s red)')
            print('\nKeeping browser open for 30 seconds...')
            await asyncio.sleep(30)

        except Exception as e:
            print(f'\n❌ Error: {e}')
            await page.screenshot(path='/tmp/error.png', full_page=True)
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(update_full_branding())
