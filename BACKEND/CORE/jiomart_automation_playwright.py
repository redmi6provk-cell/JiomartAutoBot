"""
JioMart Automation - Async Playwright Version
Replaces Selenium-based JioMartAutomation.
"""

import asyncio
import re
from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
from config import Config
from playwright_manager import PlaywrightManager
from otp_monitor_playwright import OTPMonitorPlaywright

class JioMartAutomationAsync:
    VERSION = "2.2.0-NUCLEAR"
    
    def __init__(self, profile_name: str, headless: bool = False):
        self.profile_name = profile_name
        self.headless = headless
        self.manager = PlaywrightManager(profile_name, headless)
        self.page: Page | None = None
        self.otp_monitor: OTPMonitorPlaywright | None = None

    async def start(self):
        """Start browser and initialize page"""
        self.page = await self.manager.setup_browser()
        self.otp_monitor = OTPMonitorPlaywright(self.page, self.profile_name)
        return self.page

    async def cleanup(self):
        """Cleanup resources"""
        if self.manager:
            await self.manager.cleanup()

    async def get_account_name(self) -> str:
        """Get account name via OTP monitor"""
        if not self.otp_monitor:
            return self.profile_name
        return await self.otp_monitor.get_account_name()

    async def send_telegram_notification(self, status: str, success: bool):
        """Send order status notification to Telegram"""
        if not self.otp_monitor:
            return
            
        icon = "✅" if success else "❌"
        account_name = self.otp_monitor.account_name or "Unknown"
        
        import time
        message = (
            f"{icon} <b>JioMart Order Update</b>\n\n"
            f"👤 Profile: <code>{self.profile_name}</code>\n"
            f"👤 Account: <code>{account_name}</code>\n"
            f"📝 Status: <b>{status}</b>\n\n"
            f"⏰ Time: {time.strftime('%I:%M:%S %p')}"
        )
        await self.otp_monitor.send_telegram(message)

    def log(self, message):
        print(f"[{self.profile_name}] {message}")

    async def nuke_popups(self):
        """Aggressively remove any backdrop or location popups [v5.1]"""
        try:
            self.log("💥 Nuking popups...")
            await self.page.evaluate("""
                () => {
                    const selectors = [
                        '.location-backdrop', '.backdrop', '.web_pincode_popup', 
                        '.close-icon', '#select_location_popup', '.accept_policy',
                        '.jm-modal-close', '.close-button'
                    ];
                    selectors.forEach(sel => {
                        const els = document.querySelectorAll(sel);
                        els.forEach(el => {
                            try {
                                if (el.tagName === 'BUTTON' || el.classList.contains('close-icon')) {
                                    el.click();
                                } else {
                                    el.remove();
                                }
                            } catch(e) {}
                        });
                    });
                }
            """)
            await asyncio.sleep(1)
        except: pass

    async def check_browser(self) -> bool:
        """Check if browser is alive, restart if needed"""
        if not self.page or self.page.is_closed():
             self.log("⚠️ Browser/Page is closed. Attempting restart...")
             await self.nuke_popups() # Nuke before attempting restart actions
             try:
                 await self.start()
                 await asyncio.sleep(2)
                 return True
             except Exception as e:
                 self.log(f"❌ Restart failed: {e}")
                 return False
        return True

    async def go_to_cart(self):
        """Navigate to cart page"""
        try:
            if not await self.check_browser():
                return False

            self.log("🛒 Opening cart...")
            try:
                await self.page.goto(Config.JIOMART_CART_URL, timeout=60000)
            except Exception as nav_err:
                 if "closed" in str(nav_err).lower():
                     self.log("  ⚠️ Browser closed during nav, retrying...")
                     if await self.check_browser():
                         await self.page.goto(Config.JIOMART_CART_URL, timeout=60000)
                     else:
                         raise nav_err
                 else:
                     raise nav_err

            if "cart" not in self.page.url:
                await self.page.wait_for_load_state("domcontentloaded")
            return "cart" in self.page.url # Strict check
        except Exception as e:
            self.log(f"❌ Failed to open cart: {e}")
            return False

    async def empty_cart(self) -> bool:
        """Empty cart (Removes coupons and saves products for later)"""
        try:
            if not await self.check_browser(): return False

            self.log("🗑️ Emptying cart...")
            if "cart" not in self.page.url:
                await self.go_to_cart()
            
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)

            # 1. Remove Coupon (Using Config)
            self.log("  → Checking for coupons to remove...")
            await self.nuke_popups() 
            for selector in Config.REMOVE_COUPON_SELECTORS:
                try:
                    btn = self.page.locator(selector).first
                    if await btn.is_visible():
                        await btn.click(timeout=3000)
                        self.log(f"  ✅ Removed coupon using: {selector}")
                        await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # JS Fallback for remove
            await self.page.evaluate("""
                () => {
                    const btn = Array.from(document.querySelectorAll('button')).find(b => 
                        b.innerText && b.innerText.includes('Remove') && 
                        (b.name === 'remove' || b.classList.contains('remove') || b.id.includes('remove'))
                    );
                    if (btn) btn.click();
                }
            """)
            await asyncio.sleep(1)

            # 2. Save for Later Loop
            self.log("  → Saving products for later...")
            for attempt in range(25):
                if not await self.check_browser(): return False
                
                # Check empty state via JS
                is_empty = await self.page.evaluate("""
                    () => {
                        const content = document.body.innerText.toLowerCase();
                        return content.includes('your cart is empty') || 
                               content.includes('no items in your cart');
                    }
                """)
                if is_empty:
                    self.log("  ✅ Cart is empty")
                    return True

                # Click "Save for Later" link
                saved = await self.page.evaluate("""
                    () => {
                        const links = Array.from(document.querySelectorAll('a, button, div, span'));
                        const saveLater = links.find(el => 
                            el.innerText && el.innerText.trim().toLowerCase() === 'save for later' && 
                            el.offsetParent !== null
                        );
                        if (saveLater) {
                            saveLater.scrollIntoView({block: 'center'});
                            saveLater.click();
                            return true;
                        }
                        return false;
                    }
                """)

                if not saved:
                    self.log("  ✅ No more products found to 'Save for Later'")
                    break
                
                self.log(f"  → Item {attempt+1} saved for later")
                await asyncio.sleep(2.5) # Wait for UI update

            return True

        except Exception as e:
            self.log(f"⚠️ Empty cart error: {e}")
            return False

    async def cleanup_addresses(self) -> bool:
        """Delete extra addresses (ENSURE ONLY 1 REMAINS)"""
        try:
            if not await self.check_browser(): return False

            self.log("🗑️ Cleaning addresses...")
            if "address" not in self.page.url:
                # Direct navigation to address page
                await self.page.goto("https://www.jiomart.com/customer/account/address", timeout=60000, wait_until="networkidle")
            
            await asyncio.sleep(5) # Long wait for address list to render
            
            # Persistent loop to delete addresses until only 1 remains
            for attempt in range(20):
                if not await self.check_browser(): return False

                # Count menus via JS with multiple candidate selectors
                count = await self.page.evaluate("""
                    () => {
                        // Priority 1: Vertical dots menu icon
                        let menus = document.querySelectorAll('span[aria-label*="IcMoreVertical"]');
                        if (menus.length > 0) return menus.length;
                        
                        // Priority 2: Address cards
                        let cards = document.querySelectorAll('.jm-address-card, jm-address-list-item');
                        if (cards.length > 0) return cards.length;
                        
                        // Priority 3: Any element containing Delete (excluding modal buttons)
                        let delOptions = Array.from(document.querySelectorAll('span, i')).filter(el => 
                            el.getAttribute('aria-label') && el.getAttribute('aria-label').includes('Vertical')
                        );
                        return delOptions.length;
                    }
                """)
                
                self.log(f"  → Attempt {attempt+1}: Address count = {count}")
                
                if count <= 1:
                    if count == 0:
                        self.log("  ⚠️ No addresses found. Checking if page loaded correctly...")
                        await asyncio.sleep(2)
                        # Re-check count once more with a different selector
                        count = await self.page.evaluate("() => document.querySelectorAll('div[class*=\"address-card\"]').length")
                        if count <= 1:
                            break
                    else:
                        self.log("  ✅ Address count is 1")
                        break
                
                # Delete the 2nd address (index 1)
                self.log(f"  → Deleting address #2...")
                
                # Open menu for 2nd address
                opened = await self.page.evaluate("""
                    () => {
                        const dots = Array.from(document.querySelectorAll('span[aria-label*="IcMoreVertical"], span[class*="IcMoreVertical"]'));
                        if (dots.length > 1) {
                            dots[1].scrollIntoView({block: 'center'});
                            dots[1].click();
                            return true;
                        }
                        return false;
                    }
                """)
                
                if not opened:
                    self.log("  ⚠️ Could not open menu for 2nd address. Trying fallback...")
                    await self.page.reload()
                    await asyncio.sleep(4)
                    continue

                await asyncio.sleep(2)
                
                # Click Delete in menu via JS
                clicked_delete = await self.page.evaluate("""
                    () => {
                        const items = Array.from(document.querySelectorAll('li, a, div, span'));
                        const del = items.find(i => 
                            i.innerText && i.innerText.trim().toLowerCase() === 'delete' && 
                            i.offsetParent !== null &&
                            !i.classList.contains('button') // Avoid clicking modal delete too early
                        );
                        if (del) {
                            del.click();
                            return true;
                        }
                        return false;
                    }
                """)
                
                if not clicked_delete:
                    self.log("  ⚠️ 'Delete' option in menu not found/clickable")
                    await self.page.reload()
                    await asyncio.sleep(4)
                    continue

                await asyncio.sleep(2)
                
                # Confirm in modal via JS
                confirmed = await self.page.evaluate("""
                    () => {
                        const btns = Array.from(document.querySelectorAll('button, div[role="button"]'));
                        const confirm = btns.find(b => 
                            b.innerText && b.innerText.trim().toLowerCase() === 'delete' && 
                            b.getAttribute('aria-label') !== 'IcMoreVertical' &&
                            b.offsetParent !== null
                        );
                        if (confirm) {
                            confirm.click();
                            return true;
                        }
                        return false;
                    }
                """)
                
                if not confirmed:
                   self.log("  ⚠️ Modal confirmation button not found")
                
                # TIMER: Let addresses list update and DOM settle
                await asyncio.sleep(5)
                
                # Check if count decreased, reload to be sure
                await self.page.reload()
                await asyncio.sleep(4)
                
                new_count = await self.page.evaluate("""
                     () => document.querySelectorAll('span[aria-label*="IcMoreVertical"], div[class*="address-card"]').length
                """)
                
                if new_count >= count and count > 0:
                    self.log(f"  ⚠️ Deletion verification failed. Initial: {count}, New: {new_count}")
                else:
                    self.log(f"  ✅ Deleted address. Remaining: {new_count}")

            return True



        except Exception as e:
            self.log(f"⚠️ Address cleanup failed: {e}")
            return False

    async def fill_address(self, address_data: dict) -> bool:
        """Edit first address or add new if none exist"""
        try:
            if not await self.check_browser(): return False

            self.log("📝 Handling address (Edit or Add New)...")
            
            if "address" not in self.page.url:
                await self.page.goto("https://www.jiomart.com/customer/account/address", timeout=60000)
                await self.page.wait_for_load_state("networkidle")
            
            await asyncio.sleep(3)

            # Check if any existing address (IcMoreVertical)
            menus = self.page.locator("//span[contains(@aria-label,'IcMoreVertical')]")
            if await menus.count() == 0:
                self.log("  ℹ️ No existing address found. Attempting to add new...")
                
                # Click Add New Address
                added_clicked = False
                for sel in Config.ADD_NEW_ADDRESS_BTN:
                    btn = self.page.locator(sel).first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        added_clicked = True
                        break
                
                if not added_clicked:
                    # Try JS click as fallback
                    added_clicked = await self.page.evaluate("""
                        () => {
                            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Add New Address'));
                            if(btn) { btn.click(); return true; }
                            return false;
                        }
                    """)

                if not added_clicked:
                    self.log("  ❌ Could not find 'Add New Address' button")
                    return False
                
                await asyncio.sleep(3)
                
                # Search for "aswaam"
                search_input = None
                for sel in Config.ADDRESS_SEARCH_INPUT:
                    el = self.page.locator(sel).first
                    if await el.count() > 0:
                        search_input = el
                        break
                
                if not search_input:
                    self.log("  ❌ Could not find address search input")
                    return False
                
                await search_input.fill("aswaam")
                await asyncio.sleep(2)
                
                # Select first result from Google Autocomplete / JioMart Search results
                await self.page.keyboard.press("ArrowDown")
                await asyncio.sleep(0.5)
                await self.page.keyboard.press("Enter")
                await asyncio.sleep(3)
                
                # Click Confirm Location
                confirmed = False
                for sel in Config.CONFIRM_LOCATION_BTN:
                    btn = self.page.locator(sel).first
                    if await btn.count() > 0 and await btn.is_visible():
                        await btn.click()
                        confirmed = True
                        break
                
                if not confirmed:
                    # Fallback to JS click for confirm button
                    confirmed = await self.page.evaluate("""
                        () => {
                            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('Confirm Location'));
                            if(btn) { btn.click(); return true; }
                            return false;
                        }
                    """)
                
                if not confirmed:
                    self.log("  ❌ Could not click 'Confirm Location'")
                    return False
                
                await asyncio.sleep(4)
                self.log("  ✅ Location confirmed, now filling details form...")

            else:
                self.log("  ℹ️ Existing address found. Editing first one...")
                await menus.first.click()
                await asyncio.sleep(1)
                
                # Click Edit
                edit_btn = self.page.locator("text='Edit'").first
                if await edit_btn.count() > 0:
                    await edit_btn.click()
                else:
                    # Fallback for Edit button
                    await self.page.evaluate("""
                        () => { 
                            const edit = Array.from(document.querySelectorAll('li, span, div')).find(el => el.innerText.trim() === 'Edit');
                            if(edit) edit.click();
                        }
                    """)
                
                await asyncio.sleep(3)

            # --- Form Filling Phase ---
            d_addr = {
                'pin': '421501',
                'house': '2',
                'floor': '0',
                'tower': '1',
                'building': 'Aswaam Homoeopathy',
                'road': 'A-2, B Cabin Road',
                'area': 'Bhawani Mandir Chowk'
            }
            if address_data:
                d_addr.update(address_data)

            # Helper to fill using pure JS events (like main.py)
            async def js_fill(name, value):
                await self.page.evaluate("""
                    ([name, value]) => {
                        const host = document.querySelector(`[name="${name}"]`);
                        if(!host) return;
                        
                        const input = host.shadowRoot 
                            ? host.shadowRoot.querySelector('input') 
                            : (host.querySelector('input') || host);
                            
                        if(input) {
                            input.focus();
                            input.value = value;
                            input.dispatchEvent(new Event('input', { bubbles:true }));
                            input.dispatchEvent(new Event('change', { bubbles:true }));
                            input.blur();
                        }
                    }
                """, [name, value])

            # Use selectors from main.py
            await js_fill('pin', d_addr.get('pin', ''))
            await js_fill('flat_or_house_no', d_addr.get('house', '')) 
            await js_fill('floorno', d_addr.get('floor', ''))          
            await js_fill('tower_no', d_addr.get('tower', ''))
            await js_fill('building_name', d_addr.get('building', ''))
            await js_fill('building_address', d_addr.get('road', ''))  
            await js_fill('area_name', d_addr.get('area', ''))

            # Select WORK (Refined for radio buttons)
            selected_work = await self.page.evaluate("""
                () => {
                    // Try clicking label first
                    const labels = Array.from(document.querySelectorAll('label'));
                    const workLabel = labels.find(l => l.innerText && l.innerText.trim().toLowerCase() === 'work');
                    if (workLabel) {
                        workLabel.click();
                        return true;
                    }
                    // Fallback: Click input by ID
                    const workInput = document.getElementById('mwork');
                    if (workInput) {
                        workInput.click();
                        return true;
                    }
                    return false;
                }
            """)
            if selected_work:
                self.log("  ✅ Selected address type: Work")
            else:
                self.log("  ⚠️ Could not select address type 'Work'")

            await asyncio.sleep(1)

            # Save & Proceed (Refined)
            save_clicked = False
            
            # Priority 1: Use aria-label with exact HTML match
            save_btn = self.page.locator("button[aria-label='button Save & Proceed']").first
            if await save_btn.count() > 0:
                try:
                    await save_btn.click(timeout=5000)
                    save_clicked = True
                except:
                    pass

            if not save_clicked:
                # Priority 2: Use text content with specific class
                save_btn_text = self.page.locator("button:has-text('Save & Proceed')").first
                if await save_btn_text.count() > 0:
                    try:
                        await save_btn_text.click(timeout=5000)
                        save_clicked = True
                    except:
                        pass

            if not save_clicked:
                # Priority 3: JS Click as fallback
                save_clicked = await self.page.evaluate("""
                    () => {
                        const btns = Array.from(document.querySelectorAll('button'));
                        const save = btns.find(b => b.innerText.includes('Save') && b.innerText.includes('Proceed'));
                        if (save) {
                            save.click();
                            return true;
                        }
                        return false;
                    }
                """)

            if save_clicked:
                self.log("✅ Address saved (Save & Proceed)")
                await asyncio.sleep(3)
                return True
            else:
                self.log("❌ Failed to click Save & Proceed")
                return False

        except Exception as e:
            self.log(f"❌ Address fill failed: {e}")
            return False

    async def add_product_to_cart(self, product_url: str) -> bool:
        """Only add product to cart (simplified) [v5.9-TIMER]"""
        try:
            self.log(f"📦 Opening product: {product_url}")
            await self.page.goto(product_url, timeout=60000)
            
            # Initial wait for product page
            await asyncio.sleep(2)

            self.log("→ Looking for Add to Cart...")
            # Use the exact selector requested or first visible from config
            selector = "//button[contains(@class,'addtocartbtn')]"
            btn = self.page.locator(selector).first
            
            if await btn.is_visible():
                await btn.scroll_into_view_if_needed()
                await asyncio.sleep(0.5)
                await btn.click()
                self.log("✅ Added to cart")
                return True
            else:
                self.log("❌ Add to cart button not found/visible")
                return False

        except Exception as e:
            self.log(f"❌ Add to cart failed: {e}")
            return False

    async def click_plus_for_qty(self, target_qty: int) -> bool:
        """Increase quantity using + button (simplified as requested)"""
        try:
            if target_qty <= 1:
                self.log("ℹ️ Quantity = 1, no need to click +")
                return True

            clicks = target_qty - 1
            self.log(f"→ Increasing qty by {clicks} clicks...")

            for i in range(clicks):
                clicked = False
                for selector in Config.PLUS_BUTTON_SELECTORS:
                    try:
                        btn = self.page.locator(selector).first
                        if await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(0.4)
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    self.log(f"⚠️ Plus button not found on click {i+1}")
                    return False

            self.log("✅ Quantity updated")
            return True

        except Exception as e:
            self.log(f"❌ Qty set failed: {e}")
            return True # Always return True as requested before

    async def _get_current_qty(self) -> int:
        """Shadow-piercing quantity detection with strict value filtering"""
        try:
            qty = await self.page.evaluate("""
                (selectors) => {
                    const findQtyFromPivot = (pivot) => {
                        if (!pivot) return 0;
                        let container = pivot.parentElement;
                        for (let layer = 0; layer < 4; layer++) { 
                            if (!container) break;
                            const elements = container.querySelectorAll('*');
                            for (let el of elements) {
                                let v = (el.tagName === 'INPUT' ? el.value : el.innerText) || "";
                                let m = v.trim().match(/^\\d+$/);
                                if (m) {
                                    let n = parseInt(m[0]);
                                    if (n > 0 && n < 20) return n; 
                                }
                            }
                            container = container.parentElement;
                        return null;
                    };

                    const btn = findBtn();
                    return findQtyFromPivot(btn);
                }
            """, Config.PLUS_BUTTON_SELECTORS)
            return qty or 1
        except:
            return 1



    async def apply_coupon(self, coupon_code: str) -> bool:
        """Apply coupon with robust expansion and detection using Config"""
        # CRITICAL: Initialize variables at Method scope to avoid UnboundLocalError
        expanded = False
        input_el = None
        
        if not coupon_code:
            self.log("ℹ️ No coupon code provided (skipping)")
            return True

        try:
            self.log(f"🎟️ Applying coupon: {coupon_code} [v{self.VERSION}]")
            await asyncio.sleep(2)
            
            # Aggressive Scroll to trigger all components
            await self.page.evaluate("""
                async () => {
                    const heights = [0.3, 0.6, 1.0, 0.8];
                    for (const h of heights) {
                        window.scrollTo(0, document.body.scrollHeight * h);
                        await new Promise(r => setTimeout(r, 600));
                    }
                }
            """)
            await asyncio.sleep(1)

            # 1. Expand Coupon Section (Retry Loop)
            expanded = False
            input_el = None
            
            for attempt in range(5):
                # 1a. Try to find input using Config selectors first
                for sel in Config.COUPON_INPUT_SELECTORS:
                    try:
                        el = self.page.locator(sel).first
                        if await el.count() > 0:
                            # If found but not visible, maybe expansion failed or is slow
                            if await el.is_visible():
                                input_el = el
                                expanded = True
                                break
                            else:
                                self.log(f"  ℹ️ Found input {sel} but not visible (attempting expansion...)")
                    except: continue
                if expanded: break
                
                # 1b. Reload fallback after 2 failed attempts
                if attempt == 2:
                    self.log("  🔄 Section not found, reloading page...")
                    await self.page.reload()
                    await asyncio.sleep(5)
                    await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight/2);")
                    await asyncio.sleep(2)

                self.log(f"  → Attempt {attempt+1}: Expanding coupon section...")
                
                # 1c. Try to expand via JS (Specific to user's HTML)
                res = await self.page.evaluate("""
                    () => {
                        const texts = ['apply coupon', 'have a coupon'];
                        
                        // Priority 1: Find direct text element (most likely listener target)
                        const textElements = Array.from(document.querySelectorAll('div, span, a, p, button, jds-text'))
                            .filter(el => {
                                const t = el.innerText ? el.innerText.trim().toLowerCase() : "";
                                return texts.some(target => t === target || t.includes(target));
                            });
                        
                        const targetText = textElements.find(el => el.offsetParent !== null && el.children.length === 0);
                        if (targetText) {
                            targetText.scrollIntoView({block: 'center'});
                            targetText.click();
                            return 'clicked text: ' + targetText.innerText;
                        }

                        // Priority 2: Icon/Chevron inside the coupon container
                        const container = document.querySelector('.apply-coupon');
                        if (container) {
                            const icon = container.querySelector('jds-icon, .j-icon, svg, .IcChevronRight');
                            if (icon) {
                                icon.click();
                                return 'clicked icon inside .apply-coupon';
                            }
                            container.click();
                            return 'clicked .apply-coupon container';
                        }
                        
                        // Priority 3: Fallback text (any element)
                        const targetAny = textElements.find(el => el.offsetParent !== null);
                        if (targetAny) {
                            targetAny.click();
                            return 'clicked any matching text: ' + targetAny.innerText;
                        }
                        return null;
                    }
                """)
                if res:
                    self.log(f"  ✅ Expansion triggered: {res}")
                    await asyncio.sleep(2)
                else:
                    # Fallback to Config expansion selectors
                    for sel in Config.COUPON_SECTION_SELECTORS:
                        try:
                            target = self.page.locator(sel).first
                            if await target.count() > 0:
                                await target.scroll_into_view_if_needed()
                                await target.click(timeout=2000, force=True)
                                self.log(f"  ✅ Clicked expansion selector: {sel}")
                                await asyncio.sleep(2)
                                break
                        except: continue
                
                # RE-CHECK input after expansion
                for sel in Config.COUPON_INPUT_SELECTORS:
                    try:
                        el = self.page.locator(sel).first
                        if await el.count() > 0 and await el.is_visible():
                            input_el = el
                            expanded = True
                            break
                    except: continue
                if expanded: break
                await asyncio.sleep(1.5)
            
            if not expanded or not input_el:
                self.log("  ⚠️ Coupon input not found after retries (skipping)")
                return True

            # 2. Find Input and Enter Code
            await input_el.scroll_into_view_if_needed()
            await asyncio.sleep(0.5)
            
            # Clear and Fill (More robust)
            try:
                await input_el.focus()
                await input_el.click()
                await self.page.keyboard.press("Control+A")
                await self.page.keyboard.press("Backspace")
                await asyncio.sleep(0.3)
                await input_el.fill(coupon_code)
            except:
                await input_el.type(coupon_code, delay=50)

            self.log(f"  ✅ Entered coupon code")
            await asyncio.sleep(1)
                
            # 3. Click Apply (Using Config.COUPON_APPLY_BUTTON)
            applied = False
            # Prioritize BUTTONS over ENTER
            for sel in [s for s in Config.COUPON_APPLY_BUTTON if s != "ENTER"] + ["ENTER"]:
                if sel == "ENTER":
                    await input_el.press("Enter")
                    self.log("  ✅ Pressed Enter for coupon")
                    applied = True 
                    await asyncio.sleep(2)
                else:
                    try:
                        # Try both .first and .last for reliability
                        btns = self.page.locator(sel)
                        for i in range(await btns.count()):
                            btn = btns.nth(i)
                            if await btn.is_visible():
                                await btn.click(timeout=3000)
                                applied = True
                                self.log(f"  ✅ Clicked Apply button: {sel}")
                                await asyncio.sleep(2)
                                break
                        if applied: break
                    except:
                        continue
            
            if not applied:
                await input_el.press("Enter")
                self.log("  ✅ Pressed Enter (Fallback)")

            # TIMER: Let final calculations settle
            await asyncio.sleep(4)
            
            # 4. Final Verification: Check if coupon code is still in input or success msg appears
            content = (await self.page.content()).lower()
            if "invalid" in content or "not applicable" in content:
                self.log("  ⚠️ Coupon might be invalid or not applicable")
                
            return True

        except Exception as e:
            self.log(f"❌ Coupon failed: {e}")
            return True

    async def _verify_amount(self, max_amount: float) -> bool:
        """Verify total amount with robust loading waits"""
        try:
            self.log(f"💰 Verifying amount (Limit: ₹{max_amount})...")
            
            # Initial wait for cart to settle
            await asyncio.sleep(3)

            # Multiple tries to catch slow-rendering totals
            for attempt in range(3):
                xpath = "//div[contains(@class,'list') and contains(@class,'total')]//span[contains(@class,'flt-right') and contains(normalize-space(.),'₹')]"
                
                # Check main page
                total_text = ""
                el = self.page.locator(xpath).first
                if await el.count() > 0:
                    total_text = await el.inner_text()
                else:
                    # Check frames
                    for frame in self.page.frames:
                        try:
                            el = frame.locator(xpath).first
                            if await el.count() > 0:
                                total_text = await el.inner_text()
                                break
                        except:
                            pass

                # If not found, try a broader selector
                if not total_text:
                    total_text = await self.page.evaluate("""
                        () => {
                            const candidates = Array.from(document.querySelectorAll('div, span, p')).filter(el => 
                                el.innerText && el.innerText.includes('₹') && 
                                (el.innerText.toLowerCase().includes('total') || el.classList.contains('total'))
                            );
                            return candidates.length > 0 ? candidates[0].innerText : "";
                        }
                    """)

                if total_text:
                    import re
                    m = re.search(r'[\d,]+\.?\d*', total_text)
                    if m:
                        amount = float(m.group().replace(",", ""))
                        if amount > 0:
                            self.log(f"  💰 Current Total: ₹{amount}")
                            if amount > max_amount:
                                self.log(f"❌ Limit Exceeded! ₹{amount} > ₹{max_amount}")
                                return False
                            return True
                
                self.log(f"  → Attempt {attempt+1}: Amount not found or ₹0, retrying...")
                await asyncio.sleep(2)

            self.log("⚠️ Total amount not found or ₹0 after retries, proceeding...")
            return True

        except Exception as e:
            self.log(f"⚠️ Verify amount error: {e}")
            return True

        except Exception as e:
            self.log(f"⚠️ Verify amount error: {e}")
            return True

    async def place_order(self) -> bool:
        """Click Place Order"""
        try:
            if not await self.check_browser():
                return False

            self.log("📋 Clicking Place Order...")
            await asyncio.sleep(1)
            
            for sel in Config.PLACE_ORDER_SELECTORS:
                try:
                    btn = self.page.locator(sel).first
                    if await btn.is_visible():
                        await btn.click()
                        self.log("✅ Clicked Place Order")
                        await asyncio.sleep(Config.WAIT_AFTER_PLACE_ORDER)
                        return True
                except:
                    continue
            
            self.log("❌ Place Order button not found")
            return False
            
        except Exception as e:
            self.log(f"❌ Place Order error: {e}")
            return False

    async def make_payment_click(self) -> bool:
        """Click Make Payment with robust navigation handling"""
        try:
            if not await self.check_browser():
                return False

            self.log("💳 clicking Make Payment...")
            await asyncio.sleep(2)
            
            # Try scrolling to middle to bring button into view
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight/2)")
            await asyncio.sleep(1)

            clicked = False
            for sel in Config.MAKE_PAYMENT_SELECTORS:
                try:
                    btn = self.page.locator(sel).first
                    if await btn.is_visible():
                        await btn.scroll_into_view_if_needed()
                        # Click and wait for navigation or load state
                        async with self.page.expect_navigation(timeout=10000) if "payment" not in self.page.url else asyncio.sleep(0):
                            await btn.click(timeout=5000)
                            clicked = True
                        
                        self.log("✅ Clicked Make Payment")
                        break
                except Exception as e:
                    continue

            if not clicked:
                # Fallback: search by text
                try:
                    btn = self.page.locator("button:has-text('Make Payment'), button:has-text('Proceed')").first
                    if await btn.is_visible():
                        await btn.click()
                        self.log("✅ Clicked Payment (Fallback)")
                        clicked = True
                except:
                    pass

            # If clicked, wait for the actual payment page components to render
            if clicked:
                try:
                    await self.page.wait_for_load_state("load", timeout=10000)
                    await asyncio.sleep(2)
                except:
                    self.log("  ⚠️ Navigation slow, proceeding with checks...")

            # Check if redundant: already on payment page or history
            url = self.page.url.lower()
            if "/order-history" in url or "/customer/account/order" in url:
                self.log("ℹ️ Redirected to Order History - Order might be placed already")
                return True
                
            if "payment" in url or "checkout" in url:
                self.log("ℹ️ Current URL: " + url)
                return True

            if not clicked:
                self.log("❌ Make Payment button not found")
                return False
                
            return True

        except Exception as e:
            self.log(f"❌ Make Payment error: {e}")
            return False

    async def select_cod(self) -> bool:
        """Select COD and Proceed with robust JioPay and Iframe support [v5.6]"""
        try:
            if not await self.check_browser(): return False
            await self.nuke_popups() # Clear blockers before starting
            
            url = self.page.url.lower()
            payment_domains = ['payments.jio.com', 'jiopay.in', 'razorpay', 'paytm', 'cashfree', 'payment/jio/gateway']
            on_payment = any(dom in url for dom in payment_domains)
            
            if not on_payment:
                # Wait up to 15s for redirect (JioPay can be slow)
                self.log(f"  → Redirect in progress ({url}), waiting 15s for portal...")
                for i in range(15):
                    await asyncio.sleep(1)
                    url = self.page.url.lower()
                    if any(dom in url for dom in payment_domains):
                        on_payment = True
                        self.log(f"  ✅ Portal reached after {i+1}s")
                        break
                
                if not on_payment:
                    self.log(f"⚠️ select_cod called but still not on payment page (URL: {url}). Skipping.")
                    return False

            self.log("💵 Selecting COD (v5.6)...")
            # Set flag for confirmation logic
            self.reached_payment = True
            
            # Step 1: Handle Blocker Modals
            # ... (modal logic same as v4.1)
            for step in [0.0, 0.4, 0.8, 1.0]:
                await self.page.evaluate(f"window.scrollTo(0, document.body.scrollHeight * {step})")
                await asyncio.sleep(0.5)

            frames = [self.page.main_frame] + self.page.frames
            selected = False
            
            # Step 2: Surgical COD Selection
            for frame in frames:
                try:
                    res = await frame.evaluate("""
                        () => {
                            const targets = ['cash on delivery', 'cod'];
                            const avoid = ['sodexo'];
                            
                            const elements = Array.from(document.querySelectorAll('div, span, label, p, .j-text'))
                                .filter(el => {
                                    const t = (el.innerText || "").toLowerCase().trim();
                                    return (t.includes('cash on delivery') || t === 'cod') && !t.includes('sodexo');
                                });
                            
                            if (elements.length === 0) return null;
                            elements.sort((a, b) => a.innerText.length - b.innerText.length);
                            const bestText = elements[0];
                            const container = bestText.closest('.j-listBlock') || bestText.closest('.payment-item') || bestText.closest('li');
                            
                            if (container) {
                                container.scrollIntoView({block: 'center'});
                                container.click();
                                const icons = container.querySelectorAll('jds-icon, svg, .j-icon, input, [role="radio"]');
                                icons.forEach(i => i.click());
                                return { found: bestText.innerText.trim(), clicked: container.className };
                            }
                            return null;
                        }
                    """)
                    if res:
                        selected = True
                        self.log(f"  ✅ COD Selected [v3.0]: '{res['found']}'")
                        break
                except: continue

            if not selected:
                self.log("  ⚠️ Smart JS failed, trying locator fallback...")
                for sel in Config.COD_SELECTORS:
                    try:
                        el = frame.locator(sel).first
                        if await el.count() > 0:
                            await el.click(timeout=3000, force=True)
                            selected = True
                            self.log(f"  ✅ Locator matched: {sel}")
                            break
                    except: continue

            # TIMER: Let selection UI state update (Proceed button activation)
            await asyncio.sleep(2)

            # Step 3: Progressive Proceed Clicks (Handles Popups)
            self.log("  → Attempting Proceed/Confirmation clicks [v4.0-COORDINATE-FIX]...")
            for attempt in range(8):
                for frame in frames:
                    try:
                        # Find button and return coordinates + error info
                        info = await frame.evaluate("""
                            () => {
                                // 1. Error check
                                const toasts = Array.from(document.querySelectorAll('div, span, p')).filter(el => {
                                    const t = el.innerText.toLowerCase();
                                    return t.includes('upi') || t.includes('reserve pay') || t.includes('error');
                                });
                                const errorText = toasts.find(t => t.offsetParent !== null)?.innerText || "";

                                // 2. Button search
                                const btns = Array.from(document.querySelectorAll('button, [role="button"], a, .j-button, .primary, .btn, .button, div, span'));
                                const matches = btns.filter(b => {
                                    const t = (b.innerText || b.value || b.getAttribute('aria-label') || "").trim().toLowerCase();
                                    if (t.includes('without offer')) return false;
                                    if (t.includes('verify')) return false;
                                    if (t === 'cancel' || t === 'close' || t === 'no' || t.includes('✕')) return false;
                                    return (t === 'proceed' || t === 'pay' || t === 'make payment' || 
                                            t === 'continue' || t === 'confirm' || t === 'yes' ||
                                            t.includes('place order') || t.includes('confirm order') ||
                                            (t.includes('proceed') && t.length < 15));
                                });

                                if (matches.length === 0) return { coords: null, error: errorText };

                                // Modal priority
                                const isModal = (el) => {
                                    let curr = el;
                                    while(curr && curr !== document.body) {
                                        const cls = (curr.className || "").toString().toLowerCase();
                                        if (cls.includes('modal') || cls.includes('dialog') || cls.includes('overlay')) return true;
                                        curr = curr.parentElement;
                                    }
                                    return false;
                                };
                                matches.sort((a, b) => isModal(b) - isModal(a));

                                const btn = matches.find(b => b.offsetParent !== null && b.getClientRects().length > 0);
                                if (btn) {
                                    const rect = btn.getBoundingClientRect();
                                    btn.scrollIntoView({block: 'center'});
                                    return {
                                        coords: { x: rect.left + rect.width/2, y: rect.top + rect.height/2 },
                                        text: (btn.innerText || 'btn').trim(),
                                        html: btn.outerHTML.substring(0, 100),
                                        error: errorText
                                    };
                                }
                                return { coords: null, error: errorText };
                            }
                        """)

                        if info.get('error'):
                            self.log(f"  ⚠️ SITE ERROR DETECTED: {info['error']}")

                        if info.get('coords'):
                            self.log(f"  ✅ Triggering Coordinate Click on '{info['text']}': {info['coords']}")
                            # Use page.mouse for real hardware-like click
                            await self.page.mouse.click(info['coords']['x'], info['coords']['y'])
                            await asyncio.sleep(2)
                            break # Move to next attempt/check
                    except: continue
                
                # Check for success
                url = self.page.url.lower()
                if any(x in url for x in ["success", "order-history", "customer/account/order"]):
                    return True
            
            return True # Proceed to confirmation check

        except Exception as e:
            self.log(f"❌ select_cod v3.0 Error: {e}")
            return True

    async def confirm_order(self) -> bool:
        """Verify order success [v5.6 (+OTP Awareness)]"""
        try:
            if not await self.check_browser(): return False
            self.log("🏁 Verifying Order Success (v5.6)...")
            
            # Wait for navigation to settle
            try:
                # 'load' is often more reliable than 'networkidle' for bank redirects
                await self.page.wait_for_load_state("load", timeout=15000)
            except: pass

            await asyncio.sleep(5)
            url = self.page.url.lower()
            # 1. URL-based success markers (Immediate)
            if "checkout/success" in url or "order-history" in url or "under-process" in url:
                self.log(f"🎉 SUCCESS: URL match detected! ({url})")
                return True

            # 2. Page content markers (Patient retrieval)
            content = ""
            for attempt in range(6): # Increased attempts
                try:
                    content = (await self.page.content()).lower()
                    if content and "loading" not in content: # Ensure it's not just a loader
                        break
                except Exception as ce:
                    self.log(f"  ℹ️ Content retrieval suspended (Page navigating?): {ce}. Waiting 2s (Retry {attempt+1}/6)...")
                    await asyncio.sleep(2)
            
            if not content:
                # If content is unreachable but we are not on a known payment page, assume success
                payment_domains = ['payments.jio.com', 'jiopay.in', 'razorpay', 'paytm', 'cashfree']
                on_payment = any(dom in url for dom in payment_domains)
                if not on_payment and "checkout" not in url:
                    self.log("🎉 SUCCESS: Navigated away from checkout/payment portal (Content unreachable).")
                    return True
                self.log("❌ CRITICAL: Page content unreachable after retries.")
                return False 

            # logic for domains
            payment_domains = ['payments.jio.com', 'jiopay.in', 'razorpay', 'paytm', 'cashfree']
            on_payment = any(dom in url for dom in payment_domains)
            
            # 3. Explicit success strings
            success_keywords = ['order id', 'order number', 'order confirmed', 'thank you for shopping', 'success']
            explicit_success = any(kw in content for kw in success_keywords)
            
            if explicit_success:
                self.log("🎉 SUCCESS: Order confirmation text found!")
                return True
                
            if not on_payment and "checkout" not in url and url != "about:blank":
                self.log(f"🎉 SUCCESS: Navigated to non-checkout page: {url}")
                return True

            self.log(f"❌ FAILED: Still on {url} without clear success markers.")
            return False

        except Exception as e:
            self.log(f"❌ Confirm error v3.0: {e}")
            return False

    async def monitor_otp(self, wait_time=20):
        try:
            if not await self.check_browser():
                return False, None, None
            if self.otp_monitor:
                return await self.otp_monitor.wait_for_otp(wait_time)
        except Exception as e:
            self.log(f"⚠️ OTP Monitoring failed: {e}")
        return False, None, None
