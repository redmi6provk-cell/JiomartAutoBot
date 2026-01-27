"""
Configuration file for JioMart Automation
✅ FIXED - Coupon input selectors
✅ FIXED - Better wait strategy
✅ FIXED - More robust payment selectors
"""
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

class Config:
    # ==================== URLS ====================
    JIOMART_BASE_URL = "https://www.jiomart.com"
    JIOMART_CART_URL = "https://www.jiomart.com/checkout/cart"
    
    # ==================== TIMEOUTS ====================
    DEFAULT_TIMEOUT = 20
    IMPLICIT_WAIT = 10
    
    # ==================== PRODUCT PAGE SELECTORS ====================
    ADD_TO_CART_SELECTORS = [
        "//button[contains(@class, 'qty_plus')]",
        "//button[@data-vertical='GROCERIES']",
        "//img[@alt='add button']/parent::button",
        "//button[contains(@class, 'jm-btn') and contains(@class, 'primary')]",
        "//button[@class='jm-btn primary medium jm-icon center jm-mr-base qty_plus ']"
    ]
    
    # Quantity selectors
    QUANTITY_INPUT_SELECTORS = [
        "//input[@type='number']",
        "//input[@placeholder='Qty']",
        "//input[contains(@class, 'quantity')]"
    ]
    
    PLUS_BUTTON_SELECTORS = [
        "//button[contains(@class, 'qty_plus')]",
        "//button[@aria-label='Increase quantity']",
        "//img[@alt='add button']/parent::button"
    ]
    
    MINUS_BUTTON_SELECTORS = [
        "//button[contains(@class, 'qty_minus')]",
        "//button[@aria-label='Decrease quantity']",
        "//img[@alt='remove button']/parent::button"
    ]
    
    # ==================== CART PAGE SELECTORS ====================
    # FIXED: Better coupon selectors with more options
    COUPON_SECTION_SELECTORS = [
        "//div[contains(@class, 'apply-coupon')]",
        "//div[contains(@class, 'coupon-section')]",
        "//div[contains(text(), 'Apply Coupon')]",
        "//span[contains(text(), 'Apply Coupon')]"
    ]
    
    COUPON_INPUT_SELECTORS = [
        "//input[@id='couponcode']",
        "//input[@name='couponcode']",
        "//input[@placeholder='Enter coupon code']",
        "//input[contains(@class, 'coupon')]",
        "//input[@type='text'][contains(@id, 'coupon')]",
        "//div[contains(@class, 'coupon')]//input[@type='text']"
    ]
    
    COUPON_APPLY_BUTTON = [
        "ENTER" 
        "//button[contains(text(), 'Apply')]",
        "//button[@type='submit' and contains(., 'Apply')]",
        "//button[contains(@class, 'apply') and contains(@class, 'coupon')]",
         # Fallback: press Enter key
    ]
    
    # ==================== PLACE ORDER BUTTON ====================
    PLACE_ORDER_SELECTORS = [
        "//button[@name='placeorder']",
        "//button[contains(text(), 'Place Order')]",
        "//button[@type='submit' and contains(@class, 'primary')]",
        "//div[contains(text(), 'Place Order')]/ancestor::button",
        "//button[contains(@class, 'place') and contains(@class, 'order')]"
    ]
    
    # ==================== MAKE PAYMENT BUTTON - ENHANCED ====================
    MAKE_PAYMENT_SELECTORS = [
        # Direct text matches
        "//button[contains(text(), 'Make Payment')]",
        "//button[normalize-space(text())='Make Payment']",
        
        # Attribute-based
        "//button[@name='placeorder']",
        "//button[@title='Make Payment']",
        "//button[@aria-label='button Make Payment']",
        
        # Class-based
        "//button[contains(@class, 'j-button') and contains(@class, 'primary')]",
        "//button[contains(@class, 'payment')]",
        
        # Structure-based
        "//div[contains(text(), 'Make Payment')]/ancestor::button",
        "//div[contains(@class, 'payment')]//button",
        
        # Flexible - any button with "payment" in visible text
        "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'payment')]"
    ]
    
    # ==================== COD SELECTION ====================
    COD_SELECTORS = [
        "//div[contains(text(), 'Cash on Delivery')]",
        "//input[@type='radio'][@value='COD']",
        "//input[@type='radio'][contains(@id, 'cod')]",
        "//div[contains(@class, 'j-listblock_block-title')][contains(text(), 'Cash on Delivery')]",
        "//label[contains(., 'Cash on Delivery')]",
        "//span[contains(text(), 'Cash on Delivery')]"
    ]
    
    COD_PROCEED_SELECTORS = [
        "//button[contains(text(), 'Proceed')]",
        "//button[@aria-label='Proceed']",
        "//button[contains(@class, 'j-button') and contains(., 'Proceed')]",
        "//button[@type='submit'][contains(@class, 'primary')]",
        "//button[normalize-space(text())='Proceed']"
    ]
    
    # ==================== SUCCESS INDICATORS ====================
    SUCCESS_MESSAGES = [
        "order placed",
        "thank you",
        "confirmed",
        "success",
        "order confirmed",
        "order successful"
    ]
    
    # ==================== WAIT TIMES - OPTIMIZED ====================
    WAIT_AFTER_ADD_TO_CART = 0.8  # Reduced for speed
    WAIT_AFTER_COUPON = 1.5  # Reduced for speed
    WAIT_AFTER_PLACE_ORDER = 2  # Reduced for speed
    WAIT_AFTER_PAYMENT = 1  # Reduced for speed
    WAIT_AFTER_COD = 0.1  # Reduced for speed
    SCROLL_PAUSE_TIME = 0.5  # Reduced for speed