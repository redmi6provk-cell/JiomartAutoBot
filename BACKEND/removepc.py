import threading
from concurrent.futures import ThreadPoolExecutor
import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Local imports
from config import Config
from driver_manager import DriverManager

class JioMartAutoBot:
    def __init__(self, profile_name, config):
        self.profile_name = profile_name
        self.config = config
        self.dm = DriverManager(profile_name=self.profile_name)

    def run_task(self):
        """Single profile logic: Remove Coupon & Save for Later."""
        driver = None
        try:
            print(f"🚀 [{self.profile_name}] Starting...")
            driver, wait = self.dm.setup_driver()
            driver.get("https://www.jiomart.com/checkout/cart")
            time.sleep(3)

            # 1. Coupon Remove (Based on your provided image)
            try:
                coupon_xpath = "//button[@name='remove' and .//div[contains(text(), 'Remove')]]"
                coupon_btn = WebDriverWait(driver, 5).until(EC.element_to_be_clickable((By.XPATH, coupon_xpath)))
                coupon_btn.click()
                print(f"[{self.profile_name}] 🎫 Coupon removed.")
                time.sleep(2)
            except:
                print(f"[{self.profile_name}] 🎫 No coupon found.")

            # 2. Save for Later (Based on your provided image)
            save_later_xpath = "//a[@title='Save for Later']"
            while True:
                links = driver.find_elements(By.XPATH, save_later_xpath)
                if not links:
                    break
                try:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", links[0])
                    links[0].click()
                    time.sleep(1.5)
                except:
                    break

            print(f"[{self.profile_name}] ✅ Task Complete!")

        except Exception as e:
            print(f"[{self.profile_name}] ❌ Error: {e}")
        finally:
            if driver:
                self.dm.cleanup()

def start_cleaning(profile_list, max_parallel):
    """ThreadPoolExecutor to run multiple browsers in parallel."""
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        executor.map(lambda p: JioMartAutoBot(p, Config).run_task(), profile_list)

if __name__ == "__main__":
    print("--- JioMart Multi-Profile Manager ---")
    
    try:
        # User input for range
        start_num = int(input("Kahan se shuru karein? (Profile Number): "))
        end_num = int(input("Kahan tak khatam karein? (Profile Number): "))
        
        # Parallel browsers count
        parallel_count = int(input("Ek sath kitne browser chalayein? (e.g. 3 or 5): ") or "3")

        # Range ke basis pe list banai (e.g. 1 to 5 -> Profile 1, Profile 2...)
        selected_profiles = [f"Profile {i}" for i in range(start_num, end_num + 1)]
        
        if not selected_profiles:
            print("❌ Invalid Range!")
        else:
            print(f"\n🔄 Running for: {selected_profiles[0]} to {selected_profiles[-1]}")
            print(f"⚡ Parallel Browsers: {parallel_count}\n")
            
            start_cleaning(selected_profiles, parallel_count)
            
            print("\n🎉 Mission Accomplished! Sab profiles saaf hain.")

    except ValueError:
        print("❌ Please enter valid numbers for Profile Range.")