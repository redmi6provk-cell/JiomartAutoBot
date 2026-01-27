"""
JioMart Advanced Automation - FIXED VERSION
✅ No duplicate quantity issue
✅ No unnecessary screenshots
✅ Proper browser management
✅ Better error recovery
"""

import time
import threading
from datetime import datetime
from jiomart_automation_improved import JioMartAutomation

# ==================== CONFIGURATION ====================

# 🛒 PRODUCTS - Add your products here
PRODUCTS = [
    
    {
        "url": "https://www.jiomart.com/p/groceries/pears-variety-pack-125-g-pack-of-5/611030135",
        "quantity": 1,
        "name": "Dove"
    },
   
   
    
    # Add more products here (up to 20)
]

# 🎟️ Coupon Code
COUPON_CODE = "R2A5V1E4H0T"

# 🔁 REORDER LOOP - How many times each profile orders
REORDER_COUNT = 5

# 👥 20 PROFILES
PROFILES = [
    "Profile 1", "Profile 2", "Profile 3", "Profile 4", "Profile 5",
    "Profile 6", "Profile 7", "Profile 8", "Profile 9", "Profile 10",
    "Profile 11", "Profile 12", "Profile 13", "Profile 14", "Profile 15",
    "Profile 16", "Profile 17", "Profile 18", "Profile 19", "Profile 20"
]

# Results storage
results = {}
results_lock = threading.Lock()

# ==================== HELPER FUNCTIONS ====================
def get_timestamp():
    return datetime.now().strftime("%H:%M:%S")

# ==================== SINGLE ORDER ATTEMPT ====================
def place_single_order(automation, attempt_num: int, profile_name: str):
    """
    Place ONE order with all products
    Returns: True if success, False if failed
    """
    try:
        print(f"\n{'='*70}")
        print(f"[{profile_name}] 🔄 ATTEMPT {attempt_num}/{REORDER_COUNT} - {get_timestamp()}")
        print(f"{'='*70}")
        
        # STEP 1: Add ALL products to cart
        print(f"[{profile_name}] 📦 Adding {len(PRODUCTS)} products to cart...")
        
        for idx, product in enumerate(PRODUCTS, 1):
            print(f"[{profile_name}]   → Product {idx}/{len(PRODUCTS)}: {product['name']}")
            
            success = automation.add_product_to_cart(
                product['url'], 
                quantity=product['quantity']
            )
            
            if not success:
                print(f"[{profile_name}]   ❌ Failed: {product['name']}")
                return False
            
            print(f"[{profile_name}]   ✅ Added: {product['name']} (Qty: {product['quantity']})")
            time.sleep(1)  # Small delay between products
        
        print(f"[{profile_name}] ✅ All {len(PRODUCTS)} products added!")
        
        # STEP 2: Go to Cart
        print(f"[{profile_name}] 🛒 Opening cart...")
        if not automation.go_to_cart():
            raise Exception("Go to cart failed")
        
        # STEP 3: Apply Coupon
        if COUPON_CODE:
            print(f"[{profile_name}] 🎟️ Applying coupon...")
            automation.apply_coupon(COUPON_CODE)
            time.sleep(1)
        
        # STEP 4: Place Order
        print(f"[{profile_name}] 📋 Placing order...")
        if not automation.place_order():
            raise Exception("Place order failed")
        
        # STEP 5: Make Payment
        print(f"[{profile_name}] 💳 Clicking Make Payment...")
        if not automation.make_payment_click():
            raise Exception("Make payment failed")
        
        # STEP 6: COD Selection
        print(f"[{profile_name}] 💵 Selecting COD...")
        if not automation.select_cod():
            raise Exception("COD selection failed")
        
        # STEP 7: Confirmation
        print(f"[{profile_name}] 🎉 Confirming order...")
        automation.confirm_order()
        
        print(f"\n{'='*70}")
        print(f"[{profile_name}] ✅ ORDER {attempt_num} SUCCESS at {get_timestamp()}!")
        print(f"{'='*70}\n")
        
        # Wait before next order
        if attempt_num < REORDER_COUNT:
            print(f"[{profile_name}] ⏳ Waiting 3 seconds before next order...")
            time.sleep(3)
        
        return True
        
    except Exception as e:
        print(f"\n{'='*70}")
        print(f"[{profile_name}] ❌ ORDER {attempt_num} FAILED at {get_timestamp()}")
        print(f"[{profile_name}] Error: {str(e)}")
        print(f"{'='*70}\n")
        return False

# ==================== PROFILE WITH REORDER LOOP ====================
def run_profile_with_reorders(profile_name: str):
    """
    Run one profile with multiple order attempts
    """
    automation = None
    profile_results = {
        "profile": profile_name,
        "total_attempts": REORDER_COUNT,
        "successful_orders": 0,
        "failed_orders": 0,
        "attempts": []
    }
    
    try:
        print(f"\n{'#'*80}")
        print(f"# {profile_name} - Starting with {REORDER_COUNT} order attempts")
        print(f"# Time: {get_timestamp()}")
        print(f"{'#'*80}\n")
        
        # Initialize Browser ONCE
        print(f"[{profile_name}] 🚀 Initializing browser...")
        automation = JioMartAutomation(profile_name=profile_name, headless=False)
        time.sleep(2)
        
        # REORDER LOOP - Multiple orders in same browser
        for attempt in range(1, REORDER_COUNT + 1):
            
            # Place order
            success = place_single_order(automation, attempt, profile_name)
            
            # Record result
            attempt_result = {
                "attempt": attempt,
                "status": "✅ SUCCESS" if success else "❌ FAILED",
                "timestamp": get_timestamp()
            }
            profile_results["attempts"].append(attempt_result)
            
            if success:
                profile_results["successful_orders"] += 1
            else:
                profile_results["failed_orders"] += 1
                print(f"[{profile_name}] ⚠️ Order {attempt} failed, continuing...")
                time.sleep(2)
        
        # Final Summary
        print(f"\n{'#'*80}")
        print(f"# {profile_name} - COMPLETED")
        print(f"# Success: {profile_results['successful_orders']}/{REORDER_COUNT}")
        print(f"# Failed: {profile_results['failed_orders']}/{REORDER_COUNT}")
        success_rate = (profile_results['successful_orders']/REORDER_COUNT*100)
        print(f"# Success Rate: {success_rate:.1f}%")
        print(f"{'#'*80}\n")
        
        # Store results
        with results_lock:
            results[profile_name] = profile_results
        
        # Keep browser open briefly for verification
        time.sleep(5)
        
    except Exception as e:
        print(f"\n[{profile_name}] ❌ CRITICAL ERROR: {str(e)}\n")
        
        with results_lock:
            profile_results["error"] = str(e)
            results[profile_name] = profile_results
    
    finally:
        if automation:
            print(f"[{profile_name}] 🔒 Closing browser...")
            automation.cleanup()

# ==================== PARALLEL RUNNER ====================
def run_parallel(profiles_list):
    """Run all profiles simultaneously"""
    
    print(f"\n{'#'*80}")
    print(f"# JIOMART ADVANCED AUTOMATION")
    print(f"# Time: {get_timestamp()}")
    print(f"# Profiles: {len(profiles_list)}")
    print(f"# Products per order: {len(PRODUCTS)}")
    print(f"# Reorders per profile: {REORDER_COUNT}")
    print(f"# Total orders: {len(profiles_list)} × {REORDER_COUNT} = {len(profiles_list) * REORDER_COUNT}")
    print(f"{'#'*80}\n")
    
    print("📋 Products to order:")
    for idx, prod in enumerate(PRODUCTS, 1):
        print(f"   {idx}. {prod['name']} (Qty: {prod['quantity']})")
    
    print(f"\n⚡ Starting in 5 seconds...\n")
    time.sleep(5)
    
    # Create threads
    threads = []
    for profile in profiles_list:
        thread = threading.Thread(
            target=run_profile_with_reorders, 
            args=(profile,), 
            name=profile
        )
        threads.append(thread)
    
    # Start all threads
    print(f"🚀 Launching all profiles at {get_timestamp()}...\n")
    for thread in threads:
        thread.start()
        time.sleep(0.5)
    
    # Wait for completion
    print("⏳ All profiles running...\n")
    for thread in threads:
        thread.join()
    
    # Final Summary
    print(f"\n{'#'*80}")
    print(f"# FINAL SUMMARY - {get_timestamp()}")
    print(f"{'#'*80}\n")
    
    total_success = 0
    total_failed = 0
    
    for profile in profiles_list:
        result = results.get(profile, {})
        success = result.get("successful_orders", 0)
        failed = result.get("failed_orders", 0)
        total = success + failed
        
        total_success += success
        total_failed += failed
        
        rate = (success/total*100 if total > 0 else 0)
        print(f"  {profile:15} | ✅ {success:2} | ❌ {failed:2} | Total: {total:2} | {rate:.0f}%")
    
    print(f"\n{'─'*80}")
    total_orders = total_success + total_failed
    print(f"  📊 Total Orders: {total_orders}")
    print(f"  ✅ Successful: {total_success}")
    print(f"  ❌ Failed: {total_failed}")
    overall_rate = (total_success/total_orders*100 if total_orders > 0 else 0)
    print(f"  📈 Success Rate: {overall_rate:.1f}%")
    print(f"{'#'*80}\n")

# ==================== SEQUENTIAL RUNNER ====================
def run_sequential(profiles_list):
    """Run profiles one by one"""
    
    print(f"\n{'#'*80}")
    print(f"# SEQUENTIAL MODE")
    print(f"# Profiles: {len(profiles_list)}")
    print(f"# Reorders: {REORDER_COUNT} per profile")
    print(f"{'#'*80}\n")
    
    for idx, profile in enumerate(profiles_list, 1):
        print(f"\n{'─'*80}")
        print(f"🔄 [{idx}/{len(profiles_list)}] Processing: {profile}")
        print(f"{'─'*80}\n")
        
        run_profile_with_reorders(profile)
        
        if idx < len(profiles_list):
            print(f"\n⏳ Next profile in 3 seconds...\n")
            time.sleep(3)
    
    # Summary
    print(f"\n{'#'*80}")
    print(f"# SUMMARY - {get_timestamp()}")
    print(f"{'#'*80}\n")
    
    total_success = 0
    total_failed = 0
    
    for profile in profiles_list:
        result = results.get(profile, {})
        success = result.get("successful_orders", 0)
        failed = result.get("failed_orders", 0)
        print(f"  {profile:15} | ✅ {success} | ❌ {failed}")
        total_success += success
        total_failed += failed
    
    print(f"\n📊 Total: ✅ {total_success} | ❌ {total_failed}")
    print(f"{'#'*80}\n")

# ==================== MAIN MENU ====================
if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════════╗
    ║                                                                  ║
    ║     JIOMART AUTOMATION - FIXED VERSION                           ║
    ║     ✅ No Duplicate Quantity Issue                               ║
    ║     ✅ No Unnecessary Screenshots                                ║
    ║     ✅ Better Error Handling                                     ║
    ║                                                                  ║
    ╚══════════════════════════════════════════════════════════════════╝
    """)
    
    print(f"\n📅 Time: {get_timestamp()}")
    print(f"📦 Products: {len(PRODUCTS)}")
    print(f"🔁 Reorders: {REORDER_COUNT} per profile")
    print(f"👥 Profiles: {len(PROFILES)}\n")
    
    print("─"*70)
    print("📋 MENU:")
    print("─"*70)
    print("1. 🔥 PARALLEL - All profiles together")
    print("2. 🐢 SEQUENTIAL - One by one")
    print("3. 🎯 SINGLE TEST - Test with one profile")
    print("4. ⚙️  CUSTOM - Select specific profiles")
    print("─"*70)
    
    choice = input("\nChoose (1/2/3/4): ").strip()
    
    if choice == "1":
        # Parallel
        num = input(f"\nHow many profiles? (1-{len(PROFILES)}, Enter=all): ").strip()
        
        if num and num.isdigit():
            selected = PROFILES[:int(num)]
        else:
            selected = PROFILES
        
        print(f"\n✅ Will use {len(selected)} profiles")
        print(f"📊 Total orders: {len(selected)} × {REORDER_COUNT} = {len(selected) * REORDER_COUNT}")
        
        confirm = input(f"\nContinue? (y/n): ").lower()
        if confirm == 'y':
            run_parallel(selected)
    
    elif choice == "2":
        # Sequential
        num = input(f"\nHow many profiles? (1-{len(PROFILES)}, Enter=all): ").strip()
        
        if num and num.isdigit():
            selected = PROFILES[:int(num)]
        else:
            selected = PROFILES
        
        confirm = input(f"\nContinue? (y/n): ").lower()
        if confirm == 'y':
            run_sequential(selected)
    
    elif choice == "3":
        # Single test
        test_profile = input(f"\nProfile name (Enter=Profile 1): ").strip()
        if not test_profile:
            test_profile = PROFILES[0]
        
        print(f"\n🎯 Testing: {test_profile}")
        print(f"🔁 Will place {REORDER_COUNT} orders")
        
        confirm = input(f"\nContinue? (y/n): ").lower()
        if confirm == 'y':
            run_profile_with_reorders(test_profile)
    
    elif choice == "4":
        # Custom
        print("\nAvailable profiles:")
        for i, p in enumerate(PROFILES, 1):
            print(f"   {i}. {p}")
        
        selected = input("\nEnter numbers (e.g., 1,3,5,7-10): ").strip()
        
        try:
            custom_profiles = []
            for part in selected.split(","):
                if "-" in part:
                    start, end = map(int, part.split("-"))
                    custom_profiles.extend([PROFILES[i-1] for i in range(start, end+1)])
                else:
                    custom_profiles.append(PROFILES[int(part)-1])
            
            if custom_profiles:
                mode = input("\nParallel (p) or Sequential (s)? ").lower()
                
                if mode == 'p':
                    run_parallel(custom_profiles)
                elif mode == 's':
                    run_sequential(custom_profiles)
        except:
            print("❌ Invalid input")
    
    else:
        print("❌ Invalid choice")
    
    print("\n✅ Script finished!")
    print(f"📅 End: {get_timestamp()}")
    input("\nPress ENTER to exit...")