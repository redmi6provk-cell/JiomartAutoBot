from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import threading
import time
import traceback

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== IMPORTS ====================
from jiomart_automation_improved import JioMartAutomation
from config import Config
from driver_manager import DriverManager

# For product removal
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor

# ==================== MODELS ====================

class Product(BaseModel):
    url: str
    name: str
    qty: int

class ProfileRange(BaseModel):
    start: int
    end: int

class AutomationRequest(BaseModel):
    mode: str
    products: List[Product]
    coupon_code: str = ""
    reorder_count: int
    profiles: Optional[List[str]] = None  # For custom mode
    profile: Optional[str] = None  # For single test
    parallel_browsers: int = 3
    headless: bool = False

class RemovalRequest(BaseModel):
    profiles: ProfileRange
    parallel_browsers: int = 3

# ==================== PRODUCT REMOVAL LOGIC ====================

class JioMartCleaner:
    def __init__(self, profile_name):
        self.profile_name = profile_name
        self.dm = DriverManager(profile_name=profile_name)

    def run_task(self):
        """Remove coupon & save for later"""
        driver = None
        try:
            print(f"🚀 [{self.profile_name}] Starting cleanup...")
            driver, wait = self.dm.setup_driver()
            driver.get("https://www.jiomart.com/checkout/cart")
            time.sleep(3)

            # Remove Coupon
            try:
                coupon_xpath = "//button[@name='remove' and .//div[contains(text(), 'Remove')]]"
                coupon_btn = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, coupon_xpath))
                )
                coupon_btn.click()
                print(f"[{self.profile_name}] 🎫 Coupon removed")
                time.sleep(2)
            except:
                print(f"[{self.profile_name}] 🎫 No coupon found")

            # Save for Later
            save_later_xpath = "//a[@title='Save for Later']"
            saved_count = 0
            while True:
                links = driver.find_elements(By.XPATH, save_later_xpath)
                if not links:
                    break
                try:
                    driver.execute_script(
                        "arguments[0].scrollIntoView({block: 'center'});", 
                        links[0]
                    )
                    links[0].click()
                    saved_count += 1
                    print(f"[{self.profile_name}] 💾 Saved product {saved_count}")
                    time.sleep(1.5)
                except:
                    break

            print(f"[{self.profile_name}] ✅ Cleanup complete! ({saved_count} items saved)")
            time.sleep(3)

        except Exception as e:
            print(f"[{self.profile_name}] ❌ Error: {e}")
        finally:
            if driver:
                self.dm.cleanup()

def run_removal(profile_list, max_parallel):
    """Run cleanup with parallel browsers"""
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        executor.map(
            lambda p: JioMartCleaner(p).run_task(), 
            profile_list
        )

# ==================== AUTOMATION LOGIC ====================

def place_single_order(automation, products, coupon, profile_name, attempt):
    """Place one order"""
    try:
        print(f"\n[{profile_name}] 🔄 Attempt {attempt}")
        
        # Add products
        for idx, product in enumerate(products, 1):
            print(f"[{profile_name}] Adding {product['name']}...")
            
            quantity = product.get('quantity') or product.get('qty', 1)
            
            success = automation.add_product_to_cart(
                product['url'], 
                quantity=quantity
            )
            
            if not success:
                print(f"[{profile_name}] ❌ Failed: {product['name']}")
                return False
            
            print(f"[{profile_name}] ✅ Added: {product['name']} (Qty: {quantity})")
            time.sleep(1)
        
        # Cart
        print(f"[{profile_name}] 🛒 Going to cart...")
        if not automation.go_to_cart():
            return False
        
        # Coupon
        if coupon:
            print(f"[{profile_name}] 🎟️ Applying coupon...")
            automation.apply_coupon(coupon)
            time.sleep(1)
        
        # Place order
        print(f"[{profile_name}] 📋 Placing order...")
        if not automation.place_order():
            return False
        
        # Payment
        print(f"[{profile_name}] 💳 Making payment...")
        if not automation.make_payment_click():
            return False
        
        # COD
        print(f"[{profile_name}] 💵 Selecting COD...")
        if not automation.select_cod():
            return False
        
        # Confirm
        print(f"[{profile_name}] 🎉 Confirming...")
        automation.confirm_order()
        
        print(f"[{profile_name}] ✅ Order {attempt} SUCCESS!")
        return True
        
    except Exception as e:
        print(f"[{profile_name}] ❌ Error: {e}")
        print(traceback.format_exc())
        return False

def run_profile_with_reorders(profile_name, products, coupon, reorder_count, headless):
    """Run multiple orders for one profile"""
    automation = None
    try:
        print(f"\n{'#'*60}")
        print(f"# Starting {profile_name}")
        print(f"{'#'*60}\n")
        
        automation = JioMartAutomation(profile_name=profile_name, headless=headless)
        time.sleep(2)
        
        success_count = 0
        
        for attempt in range(1, reorder_count + 1):
            success = place_single_order(
                automation, 
                products, 
                coupon, 
                profile_name, 
                attempt
            )
            
            if success:
                success_count += 1
            
            if attempt < reorder_count:
                time.sleep(3)
        
        print(f"\n[{profile_name}] ✅ Done! {success_count}/{reorder_count} successful")
        time.sleep(5)
        
    except Exception as e:
        print(f"[{profile_name}] ❌ Critical: {e}")
        print(traceback.format_exc())
    finally:
        if automation:
            automation.cleanup()

def run_parallel(profiles, products, coupon, reorder, headless):
    """Parallel execution"""
    threads = []
    for profile in profiles:
        thread = threading.Thread(
            target=run_profile_with_reorders,
            args=(profile, products, coupon, reorder, headless),
            daemon=True
        )
        threads.append(thread)
    
    for thread in threads:
        thread.start()
        time.sleep(0.5)
    
    for thread in threads:
        thread.join()

def run_sequential(profiles, products, coupon, reorder, headless):
    """Sequential execution"""
    for profile in profiles:
        run_profile_with_reorders(profile, products, coupon, reorder, headless)
        time.sleep(3)

# ==================== API ENDPOINTS ====================

@app.get("/")
def read_root():
    return {"message": "JioMart Automation API ✅"}

@app.post("/api/start-automation")
async def start_automation(request: AutomationRequest):
    try:
        print(f"\n{'='*60}")
        print(f"📦 Mode: {request.mode}")
        print(f"{'='*60}\n")
        
        # Convert products
        products_list = [
            {
                "url": p.url,
                "name": p.name,
                "quantity": p.qty,
                "qty": p.qty
            }
            for p in request.products
        ]
        
        # Determine profiles based on mode
        if request.mode == 'single_test':
            # Single test mode
            profile = request.profile or "Profile 1"
            profiles = [profile]
            
        elif request.mode in ['parallel', 'sequential']:
            # Range-based modes - NOT IMPLEMENTED IN FRONTEND YET
            # For now, use custom if profiles provided
            if request.profiles:
                profiles = request.profiles
            else:
                # Default fallback
                profiles = ["Profile 1"]
                
        elif request.mode == 'custom':
            # Custom mode with selected profiles
            profiles = request.profiles or ["Profile 1"]
        
        else:
            return {"status": "error", "message": "Invalid mode"}
        
        print(f"👥 Profiles: {profiles}")
        print(f"📦 Products: {len(products_list)}\n")
        
        # Start automation
        if request.mode in ['parallel', 'custom']:
            thread = threading.Thread(
                target=run_parallel,
                args=(
                    profiles,
                    products_list,
                    request.coupon_code,
                    request.reorder_count,
                    request.headless
                ),
                daemon=True
            )
            thread.start()
            
        elif request.mode == 'sequential':
            thread = threading.Thread(
                target=run_sequential,
                args=(
                    profiles,
                    products_list,
                    request.coupon_code,
                    request.reorder_count,
                    request.headless
                ),
                daemon=True
            )
            thread.start()
            
        elif request.mode == 'single_test':
            thread = threading.Thread(
                target=run_profile_with_reorders,
                args=(
                    profiles[0],
                    products_list,
                    request.coupon_code,
                    request.reorder_count,
                    request.headless
                ),
                daemon=True
            )
            thread.start()
        
        return {
            "status": "success",
            "message": f"✅ Started {len(profiles)} profile(s)!",
            "data": {
                "mode": request.mode,
                "profiles": profiles,
                "products": len(products_list)
            }
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

@app.post("/api/remove-products")
async def remove_products(request: RemovalRequest):
    try:
        print(f"\n{'='*60}")
        print(f"🗑️ Product Removal")
        print(f"{'='*60}\n")
        
        # Generate profile list
        profiles = [
            f"Profile {i}" 
            for i in range(request.profiles.start, request.profiles.end + 1)
        ]
        
        print(f"👥 Profiles: {profiles}")
        print(f"⚡ Parallel: {request.parallel_browsers}\n")
        
        # Start removal in background
        thread = threading.Thread(
            target=run_removal,
            args=(profiles, request.parallel_browsers),
            daemon=True
        )
        thread.start()
        
        return {
            "status": "success",
            "message": f"✅ Cleanup started for {len(profiles)} profiles!",
            "data": {
                "profiles": profiles,
                "parallel": request.parallel_browsers
            }
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(traceback.format_exc())
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)