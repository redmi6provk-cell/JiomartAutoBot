@echo off
title JioMart Automation Starter

:: --- RAINBOW INTRO ---
for %%i in (1 2 3 4 5) do (
    color 1f & timeout /t 1 >nul /nobreak
    color 4f & timeout /t 1 >nul /nobreak
)

:: Final theme (Purple bg + Aqua text)
color 5b
cls

cd /d E:\JioMartF\BACKEND\CORE

echo ==================================================
echo        🚀 JioMart Automation Starter
echo ==================================================
echo.

echo [1/2] ⚙️ Starting FastAPI Backend...
start "JioMart Backend" cmd /k ".\env\Scripts\python main_async.py"

timeout /t 3 >nul

echo [2/2] 🤖 Starting Telegram Bot...
start "JioMart Bot" cmd /k ".\env\Scripts\python interactive_bot_playwright.py"

echo.
echo ==================================================
echo ✅ Both processes started successfully!
echo 💡 You can close this window now.
echo ==================================================
echo.

pause