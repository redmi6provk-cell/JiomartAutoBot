"""
Playwright Browser Manager for JioMart Automation.
Replaces driver_manager.py with Playwright-based browser automation.
"""
import asyncio
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from database import SessionLocal
from models import Profile, Cookie
import json
from typing import Optional, Dict, Any


class PlaywrightManager:
    """
    Manages Playwright browser instances with profile support.
    Loads cookies and local storage from PostgreSQL database.
    """
    
    def __init__(self, profile_name: str, headless: bool = False):
        """
        Initialize Playwright manager.
        
        Args:
            profile_name: Profile name (e.g., "Profile 1")
            headless: Run browser in headless mode
        """
        self.profile_name = profile_name
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.profile_id = None
        
        # Browser settings
        self.BRAVE_PATH = r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
    
    async def setup_browser(self):
        """Setup and launch Playwright browser with profile."""
        try:
            # Extract profile number from name (e.g., "Profile 1" -> 1)
            profile_num = int(self.profile_name.split()[-1])
            
            # Load profile from database
            db = SessionLocal()
            try:
                profile = db.query(Profile).filter(Profile.profile_number == profile_num).first()
                if not profile:
                    raise ValueError(f"Profile {profile_num} not found in database")
                
                self.profile_id = profile.id
                print(f"✅ Loaded profile #{profile_num} from database")
                
                # Get cookies data
                cookie_record = db.query(Cookie).filter(Cookie.profile_id == profile.id).first()
                cookies_data = cookie_record.cookies if cookie_record else {}
                
            finally:
                db.close()
            
            # Launch Playwright
            self.playwright = await async_playwright().start()
            
            # Launch browser (Chromium/Brave)
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                # Try to use standard chrome if available, otherwise bundled chromium
                channel='chrome', 
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--start-maximized'
                ]
            )
            
            # Create browser context
            self.context = await self.browser.new_context(
                viewport=None,  # Use full window size
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Inject cookies and local storage
            await self._inject_session_data(cookies_data)
            
            # Create page
            self.page = await self.context.new_page()
            
            print(f"✅ Playwright browser launched successfully")
            return self.page
            
        except Exception as e:
            print(f"❌ Error setting up browser: {e}")
            await self.cleanup()
            raise
    
    async def _inject_session_data(self, cookies_data: Dict[str, Any]):
        """
        Inject cookies and local storage into browser context.
        
        Args:
            cookies_data: Dictionary containing targets with cookies and local_storage
        """
        for url, target_data in cookies_data.items():
            # Add cookies
            cookies_list = target_data.get('cookies', [])
            if cookies_list:
                await self.context.add_cookies(cookies_list)
                print(f"   🍪 Injected {len(cookies_list)} cookies for {url}")
            
            # Add local storage (need to navigate to the page first)
            local_storage = target_data.get('local_storage', {})
            if local_storage:
                # Create a temporary page to inject local storage
                temp_page = await self.context.new_page()
                await temp_page.goto(url)
                
                # Inject local storage items
                for key, value in local_storage.items():
                    await temp_page.evaluate(
                        f"localStorage.setItem({json.dumps(key)}, {json.dumps(value)})"
                    )
                
                await temp_page.close()
                print(f"   💾 Injected {len(local_storage)} local storage items for {url}")
    
    async def save_session(self):
        """
        Save current cookies and local storage back to database.
        """
        if not self.context or not self.profile_id:
            print("⚠️  No active context or profile to save")
            return
        
        try:
            # Get current cookies
            cookies = await self.context.cookies()
            
            # Get local storage from current page
            local_storage = {}
            if self.page:
                local_storage = await self.page.evaluate("() => Object.assign({}, localStorage)")
            
            # Organize by domain
            targets = {}
            current_url = await self.page.url() if self.page else "https://www.jiomart.com/"
            
            targets[current_url] = {
                "cookies": cookies,
                "local_storage": local_storage
            }
            
            # Update database
            db = SessionLocal()
            try:
                cookie_record = db.query(Cookie).filter(Cookie.profile_id == self.profile_id).first()
                if cookie_record:
                    cookie_record.cookies = targets
                else:
                    cookie_record = Cookie(profile_id=self.profile_id, cookies=targets)
                    db.add(cookie_record)
                
                db.commit()
                print(f"✅ Session saved to database ({len(cookies)} cookies, {len(local_storage)} storage items)")
            finally:
                db.close()
                
        except Exception as e:
            print(f"❌ Error saving session: {e}")
    
    async def cleanup(self):
        """Close browser and cleanup resources."""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            print("✅ Browser cleaned up")
        except Exception as e:
            print(f"⚠️  Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Context manager entry."""
        await self.setup_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        await self.save_session()
        await self.cleanup()


# Synchronous wrapper for compatibility
class PlaywrightManagerSync:
    """
    Synchronous wrapper for PlaywrightManager.
    Use this for compatibility with existing synchronous code.
    """
    
    def __init__(self, profile_name: str, headless: bool = False):
        self.profile_name = profile_name
        self.headless = headless
        self.manager = None
        self.page = None
    
    def setup_driver(self):
        """Setup browser and return page (sync version)."""
        self.manager = PlaywrightManager(self.profile_name, self.headless)
        self.page = asyncio.run(self.manager.setup_browser())
        return self.page
    
    def cleanup(self):
        """Cleanup browser (sync version)."""
        if self.manager:
            asyncio.run(self.manager.cleanup())
    
    def save_session(self):
        """Save session (sync version)."""
        if self.manager:
            asyncio.run(self.manager.save_session())


# Example usage
if __name__ == "__main__":
    async def test():
        async with PlaywrightManager("Profile 1", headless=False) as manager:
            page = manager.page
            await page.goto("https://www.jiomart.com/")
            await page.wait_for_timeout(3000)
            print(f"Page title: {await page.title()}")
    
    asyncio.run(test())
