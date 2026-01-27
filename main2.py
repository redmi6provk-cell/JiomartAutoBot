from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time

BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
BASE_PROFILE_DIR = r"C:\selenium_brave_profiles"

def open_profiles(start, end):
    drivers = []

    for i in range(start, end + 1):
        options = Options()
        options.binary_location = BRAVE_PATH
        options.add_argument(f"--user-data-dir={BASE_PROFILE_DIR}\\profile{i}")
        options.add_argument("--profile-directory=Default")

        driver = webdriver.Chrome(options=options)
        driver.get("https://www.jiomart.com")
        drivers.append(driver)

        time.sleep(2)  # small delay to avoid race issues

    input(f"\nLogin manually for profiles {start} to {end}, then press ENTER to close all...")

    for driver in drivers:
        driver.quit()

# ---- RUN BATCHES ----
open_profiles(1, 5)
open_profiles(6, 10)
