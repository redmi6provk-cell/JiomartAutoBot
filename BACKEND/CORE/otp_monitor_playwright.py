"""
Async OTP Monitor for JioMart using Playwright.
Replaces Selenium-based OTPMonitor.
"""

import time
import asyncio
import requests
from config import Config

class OTPMonitorPlaywright:
    def __init__(self, page, profile_name):
        self.page = page
        self.profile_name = profile_name
        self.last_otp = None
        self.account_name = None  # Cache account name

    async def send_telegram(self, message: str) -> bool:
        """Send message to Telegram (Async wrapper)"""
        if not Config.TELEGRAM_ENABLED:
            print(f"[{self.profile_name}] ⚠️ Telegram disabled in config")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            
            data = {
                "chat_id": Config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            
            print(f"[{self.profile_name}] 📤 Sending to Telegram...")
            
            # Run blocking requests in executor
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.post(url, data=data, timeout=10))
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"[{self.profile_name}] ✅ Telegram sent!")
                    return True
                else:
                    print(f"[{self.profile_name}] ❌ Telegram API error: {result}")
                    return False
            else:
                print(f"[{self.profile_name}] ❌ HTTP {response.status_code}: {response.text}")
                return False
                
        except Exception as e:
            print(f"[{self.profile_name}] ❌ Telegram connection error: {e}")
            return False

    async def get_account_name(self) -> str:
        """Get account name from /customer/account page"""
        try:
            print(f"[{self.profile_name}] 👤 Getting account name...")
            await self.page.goto(f"{Config.JIOMART_BASE_URL}/customer/account")
            await self.page.wait_for_load_state("networkidle")
            
            # Method 1: Full Name label
            try:
                # XPath: //label[normalize-space()='Full Name']/following-sibling::div
                # Playwright: locator("text=Full Name").locator("xpath=following-sibling::div") or similar
                # Using XPath directly is fine
                name_el = self.page.locator("//label[normalize-space()='Full Name']/following-sibling::div")
                if await name_el.count() > 0:
                    account_name = (await name_el.inner_text()).strip()
                    if account_name:
                        print(f"[{self.profile_name}] ✅ Name found: {account_name}")
                        self.account_name = account_name
                        return account_name
            except Exception:
                pass
            
            # Method 2: Input field
            try:
                input_el = self.page.locator("input[name='name'], input[id='name'], input[placeholder*='Name']").first
                if await input_el.count() > 0:
                    val = await input_el.get_attribute("value")
                    if val:
                        self.account_name = val
                        return val
            except Exception:
                pass

            # Method 3: Body text regex (fallback)
            try:
                body_text = await self.page.evaluate("document.body.innerText")
                import re
                match = re.search(r'(?:Full Name|Name)[:\s]+([A-Za-z\s]+)', body_text)
                if match:
                    name = match.group(1).strip()
                    if len(name) > 3:
                        self.account_name = name
                        return name
            except Exception:
                pass
            
            print(f"[{self.profile_name}] ⚠️ Could not find name, using profile name")
            self.account_name = self.profile_name
            return self.profile_name
            
        except Exception as e:
            print(f"[{self.profile_name}] ❌ Error getting name: {e}")
            self.account_name = self.profile_name
            return self.profile_name

    async def check_otp_on_page(self) -> str | None:
        """Check if OTP is visible on current page"""
        try:
            # 1. By class "delotpno"
            otp_el = self.page.locator(".delotpno").first
            if await otp_el.count() > 0:
                text = (await otp_el.inner_text()).strip()
                if text.isdigit() and len(text) >= 4:
                    return text
            
            # 2. Flexible search
            # Equivalent to //*[contains(@class, 'otp') or contains(@id, 'otp')]
            otp_candidates = self.page.locator("xpath=//*[contains(@class, 'otp') or contains(@id, 'otp')]")
            count = await otp_candidates.count()
            
            for i in range(count):
                el = otp_candidates.nth(i)
                text = (await el.inner_text()).strip()
                if text.isdigit() and 4 <= len(text) <= 6:
                    return text
            
            return None
        except Exception:
            return None

    async def navigate_to_order_details(self) -> bool:
        """Navigate to order history, filter by Under Process, and click first order"""
        try:
            print(f"[{self.profile_name}] 📋 Opening order history...")
            await self.page.goto(f"{Config.JIOMART_BASE_URL}/customer/orderhistory")
            await self.page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)

            # STEP 1: Click "Under Process" filter
            print(f"[{self.profile_name}] 🔍 Filtering by 'Under Process'...")
            try:
                # Based on user HTML: <span class="label">Under Process</span> inside a label
                under_process_radio = self.page.locator("label:has-text('Under Process')")
                if await under_process_radio.count() > 0:
                    await under_process_radio.first.click()
                    print(f"[{self.profile_name}] ✅ Filter 'Under Process' clicked")
                    await asyncio.sleep(2)

                # Click "Apply" or "OK" if it exists (for the filter)
                ok_btn = self.page.locator("button:has-text('OK'), button:has-text('Apply'), button:has-text('Submit')").first
                if await ok_btn.count() > 0 and await ok_btn.is_visible():
                    await ok_btn.click()
                    print(f"[{self.profile_name}] ✅ Filter 'OK/Apply' button clicked")
                    await self.page.wait_for_load_state("networkidle", timeout=10000)
                    await asyncio.sleep(3)

            except Exception as fe:
                print(f"[{self.profile_name}] ⚠️ Filter click failed: {fe}")

            # STEP 2: Click first order in the filtered list
            selectors = [
                 "//div[contains(@class, 'order-item')]",
                 "//div[contains(@class, 'ng-star-inserted') and .//div[contains(@class, 'status')]]",
                 "jm-order-list-item",
                 ".order-list-item"
            ]
            
            for sel in selectors:
                orders = self.page.locator(sel)
                if await orders.count() > 0:
                    first_order = orders.first
                    await first_order.scroll_into_view_if_needed()
                    await asyncio.sleep(0.5)
                    await first_order.click()
                    print(f"[{self.profile_name}] ✅ Clicked latest (under process) order")
                    await asyncio.sleep(3)
                    return True
            
            print(f"[{self.profile_name}] ℹ️ No orders found or click failed")
            return False
            
        except Exception as e:
            print(f"[{self.profile_name}] ❌ Nav error: {e}")
            return False

    async def wait_for_otp(self, max_wait_minutes=1440):
        """Monitor for OTP (Main loop) - Indefinite until browser closed"""
        try:
            print(f"\n[{self.profile_name}] 👀 Starting Async OTP Monitoring...")
            print(f"[{self.profile_name}] 💡 Monitoring will stop if you close the browser window.")
            
            # Get name if missing
            if not self.account_name:
                await self.get_account_name()
            
            # Go to order details
            await self.navigate_to_order_details()
            
            # Default to 24 hours (1440 mins) if not specified
            max_attempts = max_wait_minutes * 4  # check every 15s -> 4 times/min
            
            for attempt in range(1, max_attempts + 1):
                # CHECK IF BROWSER/PAGE IS CLOSED
                if self.page.is_closed():
                    print(f"[{self.profile_name}] 🛑 Browser closed manually. Stopping OTP monitor.")
                    return False, None, self.account_name

                try:
                    otp = await self.check_otp_on_page()
                except Exception as e:
                    if "Target page, context or browser has been closed" in str(e):
                         print(f"[{self.profile_name}] 🛑 Browser closed. Stopping OTP monitor.")
                         return False, None, self.account_name
                    raise e
                
                if otp:
                    if otp != self.last_otp:
                        self.last_otp = otp
                        print(f"\n[{self.profile_name}] 🎉 OTP Found: {otp}")
                        
                        message = (
                            f"🛒 <b>JioMart Delivery OTP</b>\n\n"
                            f"👤 Profile: <code>{self.profile_name}</code>\n"
                            f"👤 Account: <code>{self.account_name}</code>\n"
                            f"🔢 OTP: <code>{otp}</code>\n\n"
                            f"⏰ Time: {time.strftime('%I:%M:%S %p')}"
                        )
                        await self.send_telegram(message)
                        return True, otp, self.account_name
                
                # Progress update
                if attempt % 4 == 0:
                    elapsed = (attempt * 15) // 60
                    print(f"[{self.profile_name}] ⏳ Monitoring... ({elapsed} min elapsed)")
                
                # Refresh periodically (every 1 minute)
                if attempt % 4 == 0:
                    try:
                        print(f"[{self.profile_name}] 🔄 Refreshing...")
                        await self.page.reload()
                        await asyncio.sleep(2)
                    except Exception as e:
                        if "Target page, context or browser has been closed" in str(e):
                             print(f"[{self.profile_name}] 🛑 Browser closed during refresh.")
                             return False, None, self.account_name
                
                await asyncio.sleep(15)
                
            print(f"[{self.profile_name}] ⏰ Timeout waiting for OTP (Max limit reached)")
            return False, None, self.account_name
            
        except Exception as e:
            print(f"[{self.profile_name}] ❌ Monitor Loop Error: {e}")
            return False, None, self.profile_name
