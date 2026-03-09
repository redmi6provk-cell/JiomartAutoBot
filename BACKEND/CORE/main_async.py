from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import traceback

# ==================== IMPORTS ====================
from jiomart_automation_playwright import JioMartAutomationAsync
from config import Config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== MODELS ====================

class Product(BaseModel):
    url: str
    name: str
    qty: int

class AutomationRequest(BaseModel):
    mode: str
    products: List[Product]
    coupon_code: str = ""
    max_amount: float = 100
    reorder_count: int
    profiles: Optional[List[str]] = None
    profile: Optional[str] = None
    parallel_browsers: int = 3
    headless: bool = False
    monitor_otp: bool = True
    otp_wait_minutes: int = 20
class RemovalRequest(BaseModel):
    profiles_start: int
    profiles_end: int
    parallel_browsers: int = 3
    headless: bool = False

async def run_removal_single(profile_name: str, headless: bool):
    automation = None
    try:
        print(f"[{profile_name}] 🧹 Starting manual cleanup...")
        automation = JioMartAutomationAsync(profile_name, headless)
        await automation.start()
        await automation.empty_cart()
        print(f"[{profile_name}] ✅ Cleanup complete")
    except Exception as e:
        print(f"[{profile_name}] ❌ Cleanup failed: {e}")
    finally:
        if automation:
            await automation.cleanup()

async def run_removal_task(start_idx, end_idx, headless):
    profiles = [f"Profile {i}" for i in range(start_idx, end_idx + 1)]
    # Simple parallel execution
    tasks = [run_removal_single(p, headless) for p in profiles]
    await asyncio.gather(*tasks)

@app.post("/api/remove-products")
async def remove_products(request: RemovalRequest):
    try:
        print(f"🚀 Starting cleanup for profiles {request.profiles_start} to {request.profiles_end}")
        asyncio.create_task(
            run_removal_task(request.profiles_start, request.profiles_end, request.headless)
        )
        return {"status": "success", "message": "Cleanup started in background"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ==================== ASYNC AUTOMATION LOGIC ====================

async def run_single_profile(profile_name: str, products: List[dict], coupon: str, 
                             reorder_count: int, headless: bool, monitor_otp: bool, 
                             otp_wait: int, max_amount: float, auto_clean: bool,
                             custom_address: dict, results_list: list = None, semaphore: asyncio.Semaphore = None):
    automation = None
    released = False
    success_in_task = False
    account_info = "Unknown"
    try:
        print(f"\n{'#'*70}")
        print(f"# {profile_name} | STARTING ASYNC")
        if custom_address:
            print(f"# Custom Address: {custom_address.get('pin')}")
        print(f"{'#'*70}\n")

        # Start Playwright FIRST
        automation = JioMartAutomationAsync(profile_name, headless)
        await automation.start()
        
        # Get account name early for notifications
        account_info = await automation.get_account_name()

        # CLEANUP PHASE (Playwright Version - Uses DB Cookies)
        if auto_clean:
            print(f"[{profile_name}] 🧹 Running cleanup (Playwright)...")
            
            # 1. Clean Cart (Remove Coupon Only)
            await automation.empty_cart()
            
            # 2. Clean Addresses (Delete Extra)
            await automation.cleanup_addresses()
            
            # 3. Fill/Edit Address (1st Address)
            if custom_address:
                await automation.fill_address(custom_address)
            else:
                 # Use default hardcoded if no custom provided
                  await automation.fill_address({
                     'pin': '421501',
                     'house': '2', 
                     'floor': '0',  
                     'tower': '1',
                     'building': 'Aswaam Homoeopathy',
                     'road': 'A-2, B Cabin Road',
                     'area': 'Bhawani Mandir Chowk'
                 })
                
            print(f"[{profile_name}] ✅ Cleanup complete")

        success_count = 0
        
        for attempt in range(1, reorder_count + 1):
            print(f"\n[{profile_name}] 🔄 Order {attempt}/{reorder_count}")
            
            # Add products
            for product in products:
                qty = product.get('qty', 1)
                
                if not await automation.add_product_to_cart(product['url']):
                    print(f"[{profile_name}] ❌ Failed to add product. Stopping.")
                    return
                
                if qty > 1:
                    if not await automation.click_plus_for_qty(qty):
                        print(f"[{profile_name}] ❌ Failed to update quantity. Stopping.")
                        return
                
                print(f"[{profile_name}] ✅ {product['name']} (Qty: {qty})")
                await asyncio.sleep(0.5)
            
            # Checkout flow
            await automation.go_to_cart()
            if not await automation.apply_coupon(coupon):
                # Optionally stop on coupon failure, but user might want to proceed without coupon
                # However, for nuclear mode, usually coupon is critical
                pass
            
            if max_amount is not None:
                if not await automation._verify_amount(max_amount):
                    print(f"[{profile_name}] 🛑 Amount exceeded, stopping.")
                    return

            if not await automation.place_order():
                print(f"[{profile_name}] ❌ Place Order failed. Stopping.")
                return
                
            if not await automation.make_payment_click():
                print(f"[{profile_name}] ❌ Make Payment click failed. Stopping.")
                return
                
            if not await automation.select_cod():
                print(f"[{profile_name}] ❌ COD selection failed. Stopping.")
                return
                
            if not await automation.confirm_order():
                print(f"[{profile_name}] ❌ Order confirmation failed (Definitive failure).")
                await automation.send_telegram_notification("Order placement FAILED ❌", False)
                return
            
            # If we reached here, order is successful
            await automation.send_telegram_notification("Order placed successfully! Waiting for OTP... 🕒", True)
            success_in_task = True
            
            # Optimization: Release semaphore slot early so next profile can start shopping
            if semaphore and not released:
                semaphore.release()
                released = True
                print(f"[{profile_name}] 🔓 Slot released! Next profile can start shopping.")
            
            success_count += 1
            print(f"[{profile_name}] ✅ Order {attempt} placed!")
            
            # OTP Monitoring
            if monitor_otp:
                print(f"[{profile_name}] 🔎 Success confirmed. Starting OTP monitoring...")
                success, otp, _ = await automation.monitor_otp(otp_wait)
                if success:
                    print(f"[{profile_name}] 🔢 OTP: {otp}")
            
            if attempt < reorder_count:
                await asyncio.sleep(5)
                
        print(f"\n[{profile_name}] 🏁 Done! {success_count}/{reorder_count}")

    except Exception as e:
        print(f"[{profile_name}] ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
        
async def run_otp_check_profile(profile_name: str, headless: bool, otp_wait: int = 5):
    """Stand-alone OTP check for a single profile"""
    automation = None
    account_info = "Unknown"
    try:
        print(f"\n{'='*70}")
        print(f"🔍 OTP CHECK | {profile_name}")
        print(f"{'='*70}\n")

        automation = JioMartAutomationAsync(profile_name, headless)
        await automation.start()
        
        # Get account name
        account_info = await automation.get_account_name()
        
        print(f"[{profile_name}] 🔎 Success confirmed. Starting OTP monitoring...")
        success, otp, _ = await automation.monitor_otp(otp_wait)
        
        if success:
            print(f"[{profile_name}] 🎉 OTP Found: {otp}")
            # The monitor_otp already sends the "JioMart Delivery OTP" message
        else:
            print(f"[{profile_name}] ❌ No OTP found in {otp_wait} minutes")
            # Send specific "No OTP Found" message
            import time
            message = (
                f"⚠️ <b>JioMart OTP Status</b>\n\n"
                f"👤 Profile: <code>{profile_name}</code>\n"
                f"👤 Account: <code>{account_info}</code>\n"
                f"❌ Status: <b>No OTP found</b> (Checked for {otp_wait} min)\n\n"
                f"⏰ Time: {time.strftime('%I:%M:%S %p')}"
            )
            await automation.otp_monitor.send_telegram(message)

    except Exception as e:
        print(f"[{profile_name}] ❌ OTP Check Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if automation:
            await automation.cleanup()

async def run_otp_check_task(profiles, headless, otp_wait=5):
    """Orchestrator for standalone OTP checks"""
    try:
        max_concurrent = 2
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def sem_run(p, delay):
            if delay > 0:
                await asyncio.sleep(delay)
            async with semaphore:
                await run_otp_check_profile(p, headless, otp_wait)

        tasks = [sem_run(p, i * 2) for i, p in enumerate(profiles)]
        await asyncio.gather(*tasks)
        print(f"\n✅ All OTP checks complete for {profiles}")
                
    except Exception as e:
        print(f"⚠️ OTP Task Error: {e}")
        if semaphore and not released:
            semaphore.release()
            released = True
            
        # Record results for summary
        if results_list is not None:
            results_list.append({
                "profile": profile_name,
                "account": account_info,
                "success": success_in_task
            })
            
        if automation:
            await automation.cleanup()

async def run_automation_task(profiles, products, coupon, reorder_count, mode, headless, 
                               monitor_otp, otp_wait, max_amount, auto_clean=True, custom_address=None):
    """Orchestrator for async tasks with throttling"""
    try:
        # Limit concurrent browsers to 2 (User requested to reduce load)
        max_concurrent = 2
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def sem_run(p, delay):
            if delay > 0:
                await asyncio.sleep(delay)
            # Manual acquire to allow early release inside run_single_profile
            await semaphore.acquire()
            await run_single_profile(
                p, products, coupon, reorder_count, headless, monitor_otp, otp_wait, max_amount,
                auto_clean, custom_address, results_list=results, semaphore=semaphore
            )

        results = []
        if mode == 'parallel':
            # Create tasks for all profiles but throttled by semaphore
            # Add 2s jitter between each profile start to reduce load
            tasks = [sem_run(p, i * 2) for i, p in enumerate(profiles)]
            await asyncio.gather(*tasks)
            
        else: # sequential or single
            for profile in profiles:
                await run_single_profile(
                    profile, products, coupon, reorder_count, headless, monitor_otp, otp_wait, max_amount,
                    auto_clean, custom_address, results_list=results
                )
                await asyncio.sleep(2)
        
        # PRINT TERMINAL SUMMARY
        print(f"\n" + "="*50)
        print(f"🚀 AUTOMATION SUMMARY 🚀")
        print("="*50)
        
        success_count = sum(1 for r in results if r['success'])
        fail_count = len(results) - success_count
        
        for res in results:
            status = "✅ SUCCESS" if res['success'] else "❌ FAILED"
            print(f"- {res['profile']} ({res['account']}): {status}")
            
        print("="*50)
        print(f"📊 TOTALS: {success_count} Success | {fail_count} Failed")
        print("="*50 + "\n")
                
    except Exception as e:
        print(f"⚠️ Task Error: {e}")


# ==================== API ENDPOINTS ====================

@app.get("/")
def read_root():
    return {"message": "JioMart Automation API - ASYNC PLAYWRIGHT 🚀"}

@app.post("/api/start-automation")
async def start_automation(request: AutomationRequest):
    try:
        # Prepare products list
        products = [
            {"url": p.url, "name": p.name, "qty": p.qty}
            for p in request.products
        ]
        
        # Determine profiles
        if request.mode == 'single_test':
            profiles = [request.profile or "Profile 1"]
            mode = 'single'
        elif request.mode == 'parallel':
            profiles = request.profiles or ["Profile 1"]
            mode = 'parallel'
        else:
            profiles = request.profiles or ["Profile 1"]
            mode = 'sequential'
            
        print(f"🚀 Starting automation for {len(profiles)} profiles in {mode} mode")
        
        # Start background task WITHOUT await
        # asyncio.create_task schedules it on the event loop
        asyncio.create_task(
            run_automation_task(
                profiles, 
                products, 
                request.coupon_code, 
                request.reorder_count,
                mode,
                request.headless,
                request.monitor_otp,
                request.otp_wait_minutes,
                request.max_amount,
                request.auto_clean,
                request.custom_address
            )
        )
        
        return {
            "status": "success",
            "message": f"✅ Started {len(profiles)} profile(s) (Async)!",
            "data": {
                "mode": mode,
                "profiles": profiles
            }
        }
        
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/check-telegram")
def check_telegram():
    try:
        import requests
        
        if not Config.TELEGRAM_ENABLED:
            return {"status": "error", "message": "Telegram is disabled in config"}
        
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/getMe"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            bot_info = response.json()
            return {
                "status": "success",
                "message": "✅ Telegram connected!",
                "bot_info": bot_info.get('result', {})
            }
        else:
            return {"status": "error", "message": f"Telegram API error: {response.text}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)
