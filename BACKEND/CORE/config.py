"""
Configuration file for JioMart Automation
✅ FIXED - Coupon input selectors
✅ FIXED - Better wait strategy
✅ FIXED - More robust payment selectors
"""
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

class Config:
   
    # TELEGRAM_BOT_TOKEN = "8563837428:AAF8ClpR5pofm0ymICIbaIs-d3zQ2a6-ewg" 
    # TELEGRAM_CHAT_ID = "1339449111" 


    # # my bot
    TELEGRAM_BOT_TOKEN = "8592538979:AAHI4yN9LR8PA4OHopgDXZTOLIYFowm1rU4" 
    TELEGRAM_CHAT_ID = "1369318513" 
    
    # Enable/disable Telegram notifications
    TELEGRAM_ENABLED = True
    
    # OTP Configuration
    OTP_WAIT_TIMEOUT = 600  
    
    # ==================== URLS ====================
    JIOMART_BASE_URL = "https://www.jiomart.com"
    JIOMART_CART_URL = "https://www.jiomart.com/checkout/cart"
    
    # ==================== TIMEOUTS ====================
    DEFAULT_TIMEOUT = 20
    IMPLICIT_WAIT = 10
    FORCE_RELOAD = True
    
    # ==================== PRODUCT PAGE SELECTORS ====================
    ADD_TO_CART_SELECTORS = [
        "//button[contains(@class,'addtocartbtn')]",
        "//button[contains(@class, 'qty_plus')]",
        "//button[contains(@class, 'add-to-cart')]",
        "//button[contains(., 'Add to Cart')]",
        "//button[contains(., 'ADD TO CART')]",
        "//button[normalize-space()='Add']",
        "button.addtocartbtn",
        ".qty_plus",
        "//button[@id='add_to_cart']",
        "//div[contains(@class, 'add-to-cart')]",
        "//span[contains(text(), 'Add')]"
    ]
    
    # Quantity selectors
    QUANTITY_INPUT_SELECTORS = [
        "input[type='number']",
        "input[placeholder='Qty']",
        "input[class*='quantity']",
        "jds-input-number input",
        "input#qty-count",
        ".qty-count",
        ".quantity-count"
    ]
    
    PLUS_BUTTON_SELECTORS = [
        "//button[contains(@class, 'qty_plus')]",
        "//button[contains(@class,'plus')]",
        "//button[@aria-label='Increase quantity']",
        "//img[@alt='add button']/parent::button",
        "jds-icon[ic='IcPlus']",
        "button:has(jds-icon[ic='IcPlus'])",
        ".IcPlus",
        "//button[contains(@class, 'add') and contains(@class, 'qty')]"
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
        "//div[contains(@class, 'j-text') and contains(text(), 'Apply Coupon')]",
        "//div[normalize-space()='Apply Coupon']",
        "//span[contains(text(), 'Apply Coupon')]",
        ".apply-coupon",
        ".IcCoupon",
        "jds-icon[ic='IcCoupon']",
        ".j-listBlock__block-captionBlock",
        "//span[contains(@aria-label, 'IcCoupon')]",
        ".apply-coupon-toggle",
        "#apply_coupon_link"
    ]
    
    COUPON_INPUT_SELECTORS = [
        "#couponcode",
        "input[name='couponcode']",
        "input[placeholder*='Coupon']",
        "//input[@id='couponcode']",
        "//input[@name='couponcode']",
        "//input[@placeholder='Enter coupon code']",
        "//input[contains(@class, 'coupon')]",
        "//input[@type='text'][contains(@id, 'coupon')]",
        "//div[contains(@class, 'coupon')]//input[@type='text']"
    ]
    
    COUPON_APPLY_BUTTON = [
        "ENTER",
        "//button[contains(text(), 'Apply')]",
        "//button[@type='submit' and contains(., 'Apply')]",
        "//button[contains(@class, 'apply') and contains(@class, 'coupon')]"
    ]

    REMOVE_COUPON_SELECTORS = [
         "//button[@name='remove']",
         "//button[contains(@class, 'remove-coupon')]",
         "//div[contains(@class, 'coupon')]//button[contains(., 'Remove')]",
         "//span[contains(@class, 'remove-coupon-icon')]"
    ]

    REMOVE_FROM_CART_SELECTORS = [
        "//div[contains(@class, 'cart-product')]//button[contains(text(), 'Remove')]",
        "//div[contains(@class, 'cart-product')]//span[contains(text(), 'Remove')]",
        "//div[contains(@class, 'cart-product')]//div[contains(text(), 'Remove')]",
        "//button[@aria-label='Remove']"
    ]

    # ==================== ADDRESS MANAGEMENT ====================
    ADD_NEW_ADDRESS_BTN = [
        "button[aria-label='button Add New Address']",
        "//button[contains(., 'Add New Address')]",
        "//div[contains(text(), 'Add New Address')]/ancestor::button"
    ]
    
    ADDRESS_SEARCH_INPUT = [
        "input#searchin",
        "input[placeholder*='Search for area']",
        "//input[@aria-label='Search for area, landmark']"
    ]
    
    CONFIRM_LOCATION_BTN = [
        "button[aria-label='button Confirm Location']",
        "//button[contains(., 'Confirm Location')]",
        "//div[contains(text(), 'Confirm Location')]/ancestor::button"
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
        "//label[contains(., 'Cash on Delivery')]",
        "//span[contains(text(), 'Cash on Delivery')]",
        "div.j-listBlock:has-text('Cash on Delivery')"
    ]
    
    COD_PROCEED_SELECTORS = [
        # Exact button from user HTML
        "//button[@aria-label='Proceed' and contains(@class,'primary')]",
        "//button[contains(@class, 'j-button') and contains(@class, 'primary') and contains(., 'Proceed')]",
        "//button[@aria-label='Proceed']",
        "//button[contains(@class, 'payment-button')]",
        "//button[contains(., 'Proceed')]",
        
        # Variations seen in logs/HTML
        "//button[contains(text(), 'Pay')]",
        "//button[contains(text(), 'PAY')]",
        "//button[contains(text(), 'Proceed')]",
        "//button[normalize-space()='Proceed']",
        "//button[contains(., 'Pay')]",
        "//button[contains(., 'PAY')]",
        "//button[contains(., 'Confirm')]",
        "//button[@type='submit'][contains(@class, 'primary')]",
        
        # Frame/Modal specific (from previous iterations)
        "//footer[@class='j-modal-footer']//button[@aria-label='Proceed']",
        "//div[@class='j-modal-buttons']//button[@aria-label='Proceed']"
    ]
    
    # ==================== SUCCESS INDICATORS ====================
    SUCCESS_MESSAGES = [
        "order placed successfully",
        "order id:",
        "transaction successful",
        "thank you for shopping",
        "order confirmed successfully",
        "under process",
        "order confirmed"
    ]
    
    # ==================== WAIT TIMES - OPTIMIZED ====================
    WAIT_AFTER_ADD_TO_CART = 0  
    WAIT_AFTER_COUPON = 1.5  
    WAIT_AFTER_PLACE_ORDER = 2  
    WAIT_AFTER_PAYMENT = 1  
    WAIT_AFTER_COD = 0.5  
    SCROLL_PAUSE_TIME = 0.5  