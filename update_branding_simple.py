#!/usr/bin/env python3
"""Simple branding update - name and color."""

import asyncio
from playwright.async_api import async_playwright

async def update_branding_simple(bot_handle: str, company_name: str, brand_color: str = '#D32F2F'):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        context.set_default_timeout(60000)
        page = await context.new_page()

        email = 'scteam@ada.support'
        password = 'Adalovelace123!'

        try:
            print(f'Step 1: Navigate to {bot_handle} branding page...')
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
            
            print('\nStep 3: Updating Agent name to "AI Agent"...')
            textboxes = await page.get_by_role('textbox').all()
            await textboxes[0].fill("AI Agent")
            await asyncio.sleep(1)
            print('   ✓ Agent name set to "AI Agent"')
            
            print('\nStep 4: Expanding "Chat window" section...')
            await page.click('text=Chat window')
            await asyncio.sleep(2)
            
            print(f'\nStep 5: Updating accent color to {brand_color}...')
            # Click the actual color input directly
            color_input = page.locator('input[type="color"]').first
            await color_input.click()
            await asyncio.sleep(1)
            
            # Fill the color value directly
            await color_input.fill(brand_color)
            await asyncio.sleep(2)
            print(f'   ✓ Accent color set to {brand_color}')
            
            await page.screenshot(path='/tmp/branding_ready.png', full_page=True)
            
            print('\nStep 6: SAVING CHANGES...')
            save_button = page.locator('button:has-text("Save changes")')
            await save_button.click()
            await asyncio.sleep(3)
            
            await page.screenshot(path='/tmp/branding_saved_final.png', full_page=True)
            print('   Screenshot: /tmp/branding_saved_final.png')
            
            print(f'\n✅ BRANDING SAVED FOR {company_name}!')
            print(f'   - Agent name: "AI Agent"')
            print(f'   - Accent color: {brand_color}')
            
            await asyncio.sleep(5)
            return True

        except Exception as e:
            print(f'\n❌ Error: {e}')
            await page.screenshot(path='/tmp/error.png', full_page=True)
            import traceback
            traceback.print_exc()
            return False
        finally:
            await browser.close()

if __name__ == '__main__':
    asyncio.run(update_branding_simple(
        bot_handle='traderjoes-ai-agent-demo',
        company_name="Trader Joe's",
        brand_color='#D32F2F'
    ))
