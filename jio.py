"""
JioMart Parallel Automation - ENHANCED VERSION
5 Browsers with detailed logging and error recovery
"""

import time
import threading
from datetime import datetime
from jiomart_automation_improved import JioMartAutomation

# ==================== CONFIGURATION ====================
PRODUCT_URL = "https://www.jiomart.com/p/groceries/medimix-ayurvedic-18-herbs-classic-soap-150-g-buy-4-get-1-free/590802948"
QUANTITY = 1
COUPON_CODE = "R2A5Y1E4H0T"  # Your coupon code

# 5 Profiles - All will open simultaneously
PROFILES = [
    "Profile 1",
    "Profile 2", 
    "Profile 3",
    "Profile 4",
    "Profile 5"
]

# Results storage
results = {}
results_lock = threading.Lock()
step_progress = {}
progress_lock = threading.Lock()

# ==================== HELPER FUNCTIONS ====================
def update_progress(profile_name: str, step: str, status: str):
    """Update step progress for a profile"""
    with progress_lock:
        if profile_name not in step_progress:
            step_progress[profile_name] = {}
        step_progress[profile_name][step] = status

def get_timestamp():
    """Get current timestamp"""
    return datetime.now().strftime("%H:%M:%S")

# ==================== SINGLE PROFILE AUTOMATION ====================
def run_single_profile(profile_name: str):
    """
    Complete automation for one profile
    Runs in separate thread
    """
    automation = None
    
    try:
        print(f"\n[{profile_name}] 🚀 Starting at {get_timestamp()}...")
        
        # STEP 1: Initialize Browser
        update_progress(profile_name, "init", "⏳")
        automation = JioMartAutomation(profile_name=profile_name, headless=False)
        time.sleep(2)
        update_progress(profile_name, "init", "✅")
        
        # STEP 2: Add to Cart
        update_progress(profile_name, "add_to_cart", "⏳")
        print(f"[{profile_name}] 📦 Adding to cart...")
        success = automation.add_product_to_cart(PRODUCT_URL, quantity=QUANTITY)
        if not success:
            update_progress(profile_name, "add_to_cart", "❌")
            raise Exception("Add to cart failed")
        update_progress(profile_name, "add_to_cart", "✅")
        
        # STEP 3: Go to Cart
        update_progress(profile_name, "go_to_cart", "⏳")
        print(f"[{profile_name}] 🛒 Opening cart...")
        success = automation.go_to_cart()
        if not success:
            update_progress(profile_name, "go_to_cart", "❌")
            raise Exception("Go to cart failed")
        update_progress(profile_name, "go_to_cart", "✅")
        
        # STEP 4: Apply Coupon (optional - won't fail if it doesn't work)
        if COUPON_CODE:
            update_progress(profile_name, "coupon", "⏳")
            print(f"[{profile_name}] 🎟️ Applying coupon...")
            automation.apply_coupon(COUPON_CODE)
            time.sleep(2)
            update_progress(profile_name, "coupon", "✅")
        
        # STEP 5: Place Order
        update_progress(profile_name, "place_order", "⏳")
        print(f"[{profile_name}] 📋 Placing order...")
        success = automation.place_order()
        if not success:
            update_progress(profile_name, "place_order", "❌")
            raise Exception("Place order failed - check screenshot")
        update_progress(profile_name, "place_order", "✅")
        
        # STEP 6: Make Payment
        update_progress(profile_name, "make_payment", "⏳")
        print(f"[{profile_name}] 💳 Clicking Make Payment...")
        success = automation.make_payment_click()
        if not success:
            update_progress(profile_name, "make_payment", "❌")
            raise Exception("Make payment failed - check screenshot")
        update_progress(profile_name, "make_payment", "✅")
        
        # STEP 7: COD Selection
        update_progress(profile_name, "cod", "⏳")
        print(f"[{profile_name}] 💵 Selecting COD...")
        success = automation.select_cod()
        if not success:
            update_progress(profile_name, "cod", "❌")
            raise Exception("COD selection failed - check screenshot")
        update_progress(profile_name, "cod", "✅")
        
        # STEP 8: Confirmation
        update_progress(profile_name, "confirm", "⏳")
        print(f"[{profile_name}] 🎉 Confirming order...")
        automation.confirm_order()
        update_progress(profile_name, "confirm", "✅")
        
        # SUCCESS!
        with results_lock:
            results[profile_name] = {
                "status": "✅ SUCCESS",
                "timestamp": get_timestamp()
            }
        
        print(f"\n{'='*60}")
        print(f"[{profile_name}] ✅ ORDER PLACED SUCCESSFULLY at {get_timestamp()}!")
        print(f"{'='*60}\n")
        
        # Keep browser open for verification
        time.sleep(10)
        return True
        
    except Exception as e:
        with results_lock:
            results[profile_name] = {
                "status": f"❌ FAILED",
                "error": str(e),
                "timestamp": get_timestamp()
            }
        
        print(f"\n{'='*60}")
        print(f"[{profile_name}] ❌ ERROR at {get_timestamp()}")
        print(f"[{profile_name}] Error: {str(e)}")
        print(f"{'='*60}\n")
        
        if automation:
            automation.save_screenshot(f"{profile_name.replace(' ', '_')}_error.png")
        
        return False
        
    finally:
        if automation:
            automation.cleanup()


# ==================== PROGRESS DISPLAY ====================
def display_progress():
    """Display live progress of all profiles"""
    steps = ["init", "add_to_cart", "go_to_cart", "coupon", "place_order", "make_payment", "cod", "confirm"]
    step_names = {
        "init": "Initialize",
        "add_to_cart": "Add to Cart",
        "go_to_cart": "Go to Cart",
        "coupon": "Apply Coupon",
        "place_order": "Place Order",
        "make_payment": "Make Payment",
        "cod": "Select COD",
        "confirm": "Confirm"
    }
    
    print("\n" + "="*80)
    print("LIVE PROGRESS TRACKER")
    print("="*80)
    
    for profile in PROFILES:
        progress = step_progress.get(profile, {})
        status_line = f"{profile:12} | "
        
        for step in steps:
            status = progress.get(step, "⬜")
            status_line += f"{status} "
        
        print(status_line)
    
    print("\nLegend: ⬜ Pending | ⏳ In Progress | ✅ Done | ❌ Failed")
    print("="*80 + "\n")


# ==================== PARALLEL RUNNER ====================
def run_parallel(profiles_list):
    """Run all profiles simultaneously"""
    
    print(f"\n{'#'*80}")
    print(f"# JIOMART PARALLEL AUTOMATION - ENHANCED")
    print(f"# Time: {get_timestamp()}")
    print(f"# Profiles: {len(profiles_list)} (All together)")
    print(f"# Product: {PRODUCT_URL}")
    print(f"# Coupon: {COUPON_CODE if COUPON_CODE else 'None'}")
    print(f"{'#'*80}\n")
    
    print("⚡ Starting all browsers in 3 seconds...\n")
    time.sleep(3)
    
    # Create threads
    threads = []
    
    for profile in profiles_list:
        thread = threading.Thread(target=run_single_profile, args=(profile,), name=profile)
        threads.append(thread)
    
    # Start all threads
    print(f"🚀 Launching all {len(profiles_list)} profiles NOW at {get_timestamp()}...\n")
    
    for thread in threads:
        thread.start()
        time.sleep(0.5)  # Slight delay to prevent simultaneous requests
    
    # Monitor progress
    print("⏳ Profiles are running...\n")
    
    # Wait for all to complete with periodic progress updates
    all_finished = False
    last_display = time.time()
    
    while not all_finished:
        time.sleep(2)
        
        # Display progress every 10 seconds
        if time.time() - last_display > 10:
            display_progress()
            last_display = time.time()
        
        # Check if all threads finished
        all_finished = all(not t.is_alive() for t in threads)
    
    # Final wait
    for thread in threads:
        thread.join()
    
    # Final Progress Display
    display_progress()
    
    # Final Summary
    print(f"\n{'#'*80}")
    print(f"# FINAL SUMMARY - Completed at {get_timestamp()}")
    print(f"{'#'*80}\n")
    
    success_count = 0
    failed_count = 0
    
    for profile in profiles_list:
        result = results.get(profile, {"status": "❓ Unknown", "timestamp": "N/A"})
        status = result["status"]
        timestamp = result.get("timestamp", "N/A")
        
        print(f"  {status:25} | {profile:12} | Time: {timestamp}")
        
        if "SUCCESS" in status:
            success_count += 1
        elif "FAILED" in status:
            failed_count += 1
            error = result.get("error", "Unknown error")
            print(f"    └─ Error: {error}")
    
    print(f"\n{'─'*80}")
    print(f"  📊 Success: {success_count}/{len(profiles_list)}")
    print(f"  ❌ Failed: {failed_count}/{len(profiles_list)}")
    print(f"  📈 Success Rate: {(success_count/len(profiles_list)*100):.1f}%")
    print(f"{'#'*80}\n")


# ==================== SEQUENTIAL RUNNER ====================
def run_sequential(profiles_list):
    """Run profiles one by one"""
    
    print(f"\n{'#'*80}")
    print(f"# SEQUENTIAL MODE (One at a time)")
    print(f"# Time: {get_timestamp()}")
    print(f"{'#'*80}\n")
    
    for idx, profile in enumerate(profiles_list, 1):
        print(f"\n{'─'*80}")
        print(f"🔄 [{idx}/{len(profiles_list)}] Processing: {profile}")
        print(f"{'─'*80}\n")
        
        run_single_profile(profile)
        
        if idx < len(profiles_list):
            print(f"\n⏳ Next profile in 3 seconds...\n")
            time.sleep(3)
    
    # Summary
    print(f"\n{'#'*80}")
    print(f"# SUMMARY - Completed at {get_timestamp()}")
    print(f"{'#'*80}\n")
    
    success_count = 0
    
    for profile in profiles_list:
        result = results.get(profile, {"status": "❓ Unknown"})
        status = result["status"]
        print(f"  {status:25} | {profile}")
        
        if "SUCCESS" in status:
            success_count += 1
        elif "FAILED" in status:
            error = result.get("error", "Unknown")
            print(f"    └─ Error: {error}")
    
    print(f"\n📊 Success: {success_count}/{len(profiles_list)}")
    print(f"{'#'*80}\n")


# ==================== MAIN MENU ====================
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║        JIOMART PARALLEL AUTOMATION - ENHANCED                    ║
    ║        Multiple Browsers with Live Progress Tracking             ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n📅 Current Time: {get_timestamp()}")
    print(f"📦 Product: Maggi Noodles")
    print(f"🎟️ Coupon: {COUPON_CODE if COUPON_CODE else 'None'}\n")
    
    print("\n" + "─"*70)
    print("📋 MENU:")
    print("─"*70)
    print("1. 🔥 PARALLEL MODE - All 5 profiles together (RECOMMENDED)")
    print("2. 🐢 SEQUENTIAL MODE - One by one")
    print("3. 🎯 SINGLE PROFILE TEST")
    print("4. ⚙️  CUSTOM - Select profiles to run")
    print("─"*70)
    
    choice = input("\nChoose (1/2/3/4): ").strip()
    
    if choice == "1":
        # Parallel execution
        print(f"\n⚡ PARALLEL MODE SELECTED")
        print(f"\n📋 Will open {len(PROFILES)} browsers simultaneously:")
        for p in PROFILES:
            print(f"   • {p}")
        
        print(f"\n⚠️  WARNING:")
        print(f"   • Make sure your PC can handle {len(PROFILES)} Chrome browsers")
        print(f"   • Recommended: 8GB+ RAM, Quad-core processor")
        print(f"   • Each browser needs ~500MB RAM")
        
        confirm = input(f"\nContinue? (y/n): ").lower()
        
        if confirm == 'y':
            run_parallel(PROFILES)
        else:
            print("❌ Cancelled")
            
    elif choice == "2":
        # Sequential
        print(f"\n🐢 SEQUENTIAL MODE SELECTED")
        print(f"📋 Will run {len(PROFILES)} profiles one by one")
        
        confirm = input(f"\nContinue? (y/n): ").lower()
        
        if confirm == 'y':
            run_sequential(PROFILES)
        else:
            print("❌ Cancelled")
            
    elif choice == "3":
        # Single test
        print(f"\n🎯 SINGLE PROFILE TEST")
        print("\nAvailable profiles:")
        for i, p in enumerate(PROFILES, 1):
            print(f"   {i}. {p}")
        
        test_profile = input("\nProfile name (or press Enter for Profile 1): ").strip()
        if not test_profile:
            test_profile = "Profile 1"
        
        print(f"\n🎯 Testing: {test_profile}")
        run_single_profile(test_profile)
        
    elif choice == "4":
        # Custom selection
        print(f"\n⚙️  CUSTOM PROFILE SELECTION")
        print("\nAvailable profiles:")
        for i, p in enumerate(PROFILES, 1):
            print(f"   {i}. {p}")
        
        selected = input("\nEnter profile numbers (e.g., 1,3,5): ").strip()
        
        try:
            indices = [int(x.strip()) - 1 for x in selected.split(",")]
            custom_profiles = [PROFILES[i] for i in indices if 0 <= i < len(PROFILES)]
            
            if custom_profiles:
                print(f"\n✅ Selected profiles: {', '.join(custom_profiles)}")
                mode = input("Run in parallel (p) or sequential (s)? ").lower()
                
                if mode == 'p':
                    run_parallel(custom_profiles)
                elif mode == 's':
                    run_sequential(custom_profiles)
                else:
                    print("❌ Invalid mode")
            else:
                print("❌ No valid profiles selected")
        except:
            print("❌ Invalid input")
    else:
        print("❌ Invalid choice")
    
    print("\n✅ Script finished!")
    print(f"📅 End Time: {get_timestamp()}")
    input("\nPress ENTER to exit...")