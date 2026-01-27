"""
JioMart Automation - FIXED VERSION
✅ Fixed coupon input interaction
✅ Fixed Make Payment button detection
✅ Better wait strategies
✅ More robust element interaction
"""

import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementClickInterceptedException
from config import Config
from driver_manager import DriverManager

class JioMartAutomation:
    def __init__(self, profile_name: str = "Profile 1", headless: bool = False):
        """Initialize the automation with specific profile"""
        self.driver_manager = DriverManager(profile_name, headless)
        self.driver, self.wait = self.driver_manager.setup_driver()
        self.profile_name = profile_name
    
    def log(self, message):
        """Print log with profile name"""
        print(f"[{self.profile_name}] {message}")
    
    def add_product_to_cart(self, product_url: str, quantity: int = 1):
        """Add product to cart"""
        try:
            self.log(f"📦 Opening product: {product_url}")
            self.driver.get(product_url)
            time.sleep(0.5)
            
            # Check if already in cart
            try:
                self.driver.find_element(By.XPATH, "//button[contains(text(), 'Go to Cart')]")
                self.log("  ℹ️ Product already in cart")
                return True
            except:
                pass
            
            # Scroll to button area
            self.driver.execute_script("window.scrollTo(0, 400);")
            time.sleep(0.1)
            
            current_qty = self._get_current_quantity()
            
            if current_qty > 0:
                self.log(f"  ℹ️ Product already has quantity {current_qty}")
                if current_qty >= quantity:
                    self.log(f"  ✅ Quantity already set to {current_qty}")
                    return True
            
            self.log("  → Looking for Add to Cart button...")
            add_btn_found = False
            
            for selector in Config.ADD_TO_CART_SELECTORS:
                try:
                    add_btn = self.driver.find_element(By.XPATH, selector)
                    
                    if add_btn.is_displayed() and add_btn.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", add_btn)
                        time.sleep(0.1)
                        
                        try:
                            add_btn.click()
                        except ElementClickInterceptedException:
                            self.driver.execute_script("arguments[0].click();", add_btn)
                        
                        self.log(f"  ✅ Clicked Add to Cart")
                        add_btn_found = True
                        time.sleep(Config.WAIT_AFTER_ADD_TO_CART)
                        break
                        
                except:
                    continue
            
            if not add_btn_found:
                raise Exception("Add to Cart button not found")
            
            if quantity > 1:
                time.sleep(0.5)
                current = self._get_current_quantity()
                if current < quantity:
                    self._set_quantity(quantity, current)
            
            self.log(f"✅ Product added to cart (Qty: {quantity})")
            return True
        
        except Exception as e:
            self.log(f"❌ Failed to add product: {e}")
            return False
    
    def _get_current_quantity(self):
        """Get current quantity in product page"""
        try:
            for selector in Config.QUANTITY_INPUT_SELECTORS:
                try:
                    qty_input = self.driver.find_element(By.XPATH, selector)
                    if qty_input.is_displayed():
                        return int(qty_input.get_attribute('value') or 0)
                except:
                    continue
            return 0
        except:
            return 0
    
    def _set_quantity(self, target_qty: int, current_qty: int = 0):
        """Set quantity by clicking plus button"""
        try:
            clicks_needed = target_qty - current_qty
            self.log(f"  → Setting quantity: {current_qty} → {target_qty} ({clicks_needed} clicks)")
            
            for i in range(clicks_needed):
                clicked = False
                for selector in Config.PLUS_BUTTON_SELECTORS:
                    try:
                        plus_btn = self.driver.find_element(By.XPATH, selector)
                        if plus_btn.is_displayed():
                            plus_btn.click()
                            time.sleep(0.4)
                            clicked = True
                            break
                    except:
                        continue
                
                if not clicked:
                    self.log(f"  ⚠️ Could not click plus button")
                    break
            
            return True
        except Exception as e:
            self.log(f"  ⚠️ Quantity setting error: {e}")
            return False
    
    def go_to_cart(self):
        """Navigate to cart page"""
        try:
            self.log("🛒 Opening cart...")
            self.driver.get(Config.JIOMART_CART_URL)
            time.sleep(3)
            
            self.log("✅ Cart opened")
            return True
        
        except Exception as e:
            self.log(f"❌ Failed to open cart: {e}")
            return False
    
    def apply_coupon(self, coupon_code: str):
        """Apply coupon code - FIXED with better interaction"""
        try:
            self.log(f"🎟️ Applying coupon: {coupon_code}")
            time.sleep(2)
            
            # Scroll to bottom where coupon section is
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            
            # Try to click on "Apply Coupon" section first to expand it
            self.log("  → Looking for coupon section...")
            for selector in Config.COUPON_SECTION_SELECTORS:
                try:
                    coupon_section = self.driver.find_element(By.XPATH, selector)
                    if coupon_section.is_displayed():
                        self.log("  → Found coupon section, clicking to expand...")
                        try:
                            coupon_section.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", coupon_section)
                        time.sleep(1.5)
                        break
                except:
                    continue
            
            # Now find and interact with input
            self.log("  → Looking for coupon input...")
            coupon_input = None
            
            for selector in Config.COUPON_INPUT_SELECTORS:
                try:
                    element = self.driver.find_element(By.XPATH, selector)
                    if element.is_displayed() and element.is_enabled():
                        coupon_input = element
                        self.log(f"  ✅ Found input with selector: {selector}")
                        break
                except:
                    continue
            
            if not coupon_input:
                self.log("  ⚠️ Coupon input not found - skipping")
                return True
            
            # Scroll to input and focus
            self.log("  → Scrolling to input...")
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", coupon_input)
            time.sleep(1)
            
            # Try multiple methods to interact with input
            self.log("  → Attempting to enter coupon code...")
            
            # Method 1: Direct click and send_keys
            try:
                coupon_input.click()
                time.sleep(0.5)
                coupon_input.clear()
                time.sleep(0.3)
                coupon_input.send_keys(coupon_code)
                self.log(f"  ✅ Entered code: {coupon_code}")
            except Exception as e:
                self.log(f"  → Method 1 failed: {e}")
                
                # Method 2: JavaScript setValue
                try:
                    self.log("  → Trying JavaScript method...")
                    self.driver.execute_script(f"arguments[0].value = '{coupon_code}';", coupon_input)
                    # Trigger input event
                    self.driver.execute_script("arguments[0].dispatchEvent(new Event('input', { bubbles: true }));", coupon_input)
                    self.log(f"  ✅ Set code via JavaScript: {coupon_code}")
                except Exception as e2:
                    self.log(f"  → Method 2 failed: {e2}")
                    
                    # Method 3: ActionChains
                    try:
                        self.log("  → Trying ActionChains...")
                        actions = ActionChains(self.driver)
                        actions.move_to_element(coupon_input).click().perform()
                        time.sleep(0.5)
                        actions.send_keys(coupon_code).perform()
                        self.log(f"  ✅ Entered via ActionChains: {coupon_code}")
                    except Exception as e3:
                        self.log(f"  ⚠️ All methods failed: {e3}")
                        return True  # Don't fail entire order for coupon
            
            time.sleep(1.5)
            
            # Apply coupon
            self.log("  → Clicking Apply button...")
            apply_success = False
            
            for option in Config.COUPON_APPLY_BUTTON:
                if option == "ENTER":
                    try:
                        coupon_input.send_keys(Keys.ENTER)
                        self.log("  → Pressed Enter")
                        apply_success = True
                        break
                    except:
                        continue
                else:
                    try:
                        apply_btn = self.driver.find_element(By.XPATH, option)
                        if apply_btn.is_displayed() and apply_btn.is_enabled():
                            try:
                                apply_btn.click()
                            except:
                                self.driver.execute_script("arguments[0].click();", apply_btn)
                            self.log("  ✅ Clicked Apply button")
                            apply_success = True
                            break
                    except:
                        continue
            
            if not apply_success:
                # Fallback: press Enter on input
                try:
                    coupon_input.send_keys(Keys.ENTER)
                    self.log("  → Pressed Enter (fallback)")
                except:
                    pass
            
            time.sleep(Config.WAIT_AFTER_COUPON)
            self.log("✅ Coupon process completed")
            return True
                
        except Exception as e:
            self.log(f"❌ Coupon error: {e}")
            return True  # Don't fail order for coupon issues
    
    def place_order(self):
        """Click Place Order button"""
        try:
            self.log("📋 Clicking Place Order...")
            time.sleep(2)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            
            for selector in Config.PLACE_ORDER_SELECTORS:
                try:
                    place_order = self.driver.find_element(By.XPATH, selector)
                    
                    if place_order.is_displayed() and place_order.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", place_order)
                        time.sleep(1)
                        
                        try:
                            place_order.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", place_order)
                        
                        self.log("✅ Place Order clicked")
                        time.sleep(Config.WAIT_AFTER_PLACE_ORDER)
                        return True
                        
                except:
                    continue
            
            raise Exception("Place Order button not found")
        
        except Exception as e:
            self.log(f"❌ Place Order failed: {e}")
            return False
    
    def make_payment_click(self):
        """Click Make Payment button - ENHANCED with better detection"""
        try:
            self.log("💳 Looking for Make Payment button...")
            
            # Wait for page to load after Place Order
            time.sleep(Config.WAIT_AFTER_PLACE_ORDER)
            
            # Try scrolling to different positions
            scroll_positions = [
                "window.scrollTo(0, document.body.scrollHeight);",  # Bottom
                "window.scrollTo(0, document.body.scrollHeight / 2);",  # Middle
                "window.scrollTo(0, 0);"  # Top
            ]
            
            for scroll_cmd in scroll_positions:
                self.driver.execute_script(scroll_cmd)
                time.sleep(1.5)
                
                # Try all selectors at this scroll position
                for idx, selector in enumerate(Config.MAKE_PAYMENT_SELECTORS):
                    try:
                        make_payment = self.driver.find_element(By.XPATH, selector)
                        
                        if make_payment.is_displayed() and make_payment.is_enabled():
                            self.log(f"  ✅ Found button with selector {idx+1}")
                            
                            # Scroll to element
                            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", make_payment)
                            time.sleep(1)
                            
                            # Try clicking
                            try:
                                make_payment.click()
                                self.log("  ✅ Clicked via normal click")
                            except:
                                self.driver.execute_script("arguments[0].click();", make_payment)
                                self.log("  ✅ Clicked via JavaScript")
                            
                            time.sleep(Config.WAIT_AFTER_PAYMENT)
                            return True
                            
                    except:
                        continue
            
            # Last resort: Find ANY button with "payment" or "proceed" text
            self.log("  → Searching for any payment-related button...")
            try:
                all_buttons = self.driver.find_elements(By.TAG_NAME, "button")
                
                for btn in all_buttons:
                    try:
                        if btn.is_displayed() and btn.is_enabled():
                            btn_text = btn.text.strip().lower()
                            
                            # Check if button text contains payment-related words
                            if any(word in btn_text for word in ['payment', 'proceed', 'continue', 'next']):
                                self.log(f"  → Found button: '{btn.text}'")
                                
                                # Scroll and click
                                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
                                time.sleep(1)
                                
                                try:
                                    btn.click()
                                except:
                                    self.driver.execute_script("arguments[0].click();", btn)
                                
                                self.log(f"  ✅ Clicked: {btn.text}")
                                time.sleep(Config.WAIT_AFTER_PAYMENT)
                                return True
                    except:
                        continue
            except:
                pass
            
            # If still not found, check current URL
            current_url = self.driver.current_url
            self.log(f"  ℹ️ Current URL: {current_url}")
            
            # If already on payment page, return success
            if 'payment' in current_url.lower() or 'checkout' in current_url.lower():
                self.log("  ✅ Already on payment page")
                return True
            
            raise Exception("Make Payment button not found")
        
        except Exception as e:
            self.log(f"❌ Make Payment failed: {e}")
            return False
    
    def select_cod(self):
        """Select COD and proceed"""
        try:
            self.log("💵 Selecting COD...")
            time.sleep(2)
            
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1.5)
            
            # Select COD
            cod_selected = False
            
            for selector in Config.COD_SELECTORS:
                try:
                    cod_elem = self.driver.find_element(By.XPATH, selector)
                    
                    if cod_elem.is_displayed():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", cod_elem)
                        time.sleep(0.8)
                        
                        try:
                            cod_elem.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", cod_elem)
                        
                        self.log("  ✅ COD selected")
                        cod_selected = True
                        time.sleep(1.5)
                        break
                except:
                    continue
            
            if not cod_selected:
                raise Exception("COD selection failed")
            
            # Click Proceed
            self.log("  → Looking for Proceed...")
            time.sleep(2)
            
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            
            for selector in Config.COD_PROCEED_SELECTORS:
                try:
                    proceed_btn = self.driver.find_element(By.XPATH, selector)
                    
                    if proceed_btn.is_displayed() and proceed_btn.is_enabled():
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", proceed_btn)
                        time.sleep(0.8)
                        
                        try:
                            proceed_btn.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", proceed_btn)
                        
                        self.log("  ✅ Proceed clicked")
                        time.sleep(Config.WAIT_AFTER_COD)
                        return True
                except:
                    continue
            
            self.log("  ⚠️ Proceed not found - may be auto-confirmed")
            return True
        
        except Exception as e:
            self.log(f"❌ COD selection failed: {e}")
            return False
    
    def confirm_order(self):
        """Check final confirmation"""
        try:
            self.log("🎉 Checking confirmation...")
            time.sleep(2)
            
            page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
            
            for indicator in Config.SUCCESS_MESSAGES:
                if indicator in page_text:
                    self.log(f"✅ ORDER CONFIRMED! ({indicator})")
                    return True
            
            self.log("ℹ️ Process completed")
            return True
        
        except:
            return True
    
    def cleanup(self):
        """Close browser"""
        self.driver_manager.cleanup()
    
    def refresh_page(self):
        """Refresh current page"""
        try:
            self.driver.refresh()
            time.sleep(2)
            return True
        except:
            return False