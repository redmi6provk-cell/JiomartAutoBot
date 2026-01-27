"""
Driver Manager for handling Chrome/Brave browser setup with profiles
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
import os

class DriverManager:
    def __init__(self, profile_name: str = "Profile 1", headless: bool = False):
        """
        Initialize driver manager
        
        Args:
            profile_name: Profile name like "Profile 1", "Profile 2", etc.
            headless: Run browser in headless mode (True/False)
        """
        self.profile_name = profile_name
        self.headless = headless
        self.driver = None
        self.wait = None
        
        # Paths - UPDATE THESE based on your setup
        self.BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
        self.BASE_PROFILE_DIR = r"C:\selenium_brave_profiles"
    
    def setup_driver(self):
        """Setup and return Chrome/Brave driver with profile"""
        try:
            # Extract profile number from name (e.g., "Profile 1" -> "1")
            profile_num = self.profile_name.split()[-1]
            profile_path = os.path.join(self.BASE_PROFILE_DIR, f"profile{profile_num}")
            
            # Chrome options
            options = Options()
            
            # Use Brave browser (comment out if using Chrome)
            options.binary_location = self.BRAVE_PATH
            
            # Profile settings
            options.add_argument(f"--user-data-dir={profile_path}")
            options.add_argument("--profile-directory=Default")
            
            # Additional settings
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Window size
            options.add_argument("--start-maximized")
            
            # Headless mode (optional)
            if self.headless:
                options.add_argument("--headless")
                options.add_argument("--disable-gpu")
            
            # Disable notifications
            prefs = {
                "profile.default_content_setting_values.notifications": 2,
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False
            }
            options.add_experimental_option("prefs", prefs)
            
            # Initialize driver
            print(f"🔧 Initializing {self.profile_name}...")
            self.driver = webdriver.Chrome(options=options)
            
            # Set implicit wait
            self.driver.implicitly_wait(10)
            
            # Create explicit wait object
            self.wait = WebDriverWait(self.driver, 20)
            
            print(f"✅ Driver ready for {self.profile_name}")
            return self.driver, self.wait
            
        except Exception as e:
            print(f"❌ Failed to setup driver: {e}")
            raise
    
    def cleanup(self):
        """Close the browser"""
        if self.driver:
            try:
                print(f"🔒 Closing {self.profile_name}...")
                self.driver.quit()
                print(f"✅ {self.profile_name} closed")
            except Exception as e:
                print(f"⚠️ Error closing driver: {e}")
    
    def get_driver(self):
        """Get the driver instance"""
        return self.driver
    
    def get_wait(self):
        """Get the wait instance"""
        return self.wait