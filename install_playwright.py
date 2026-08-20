#!/usr/bin/env python3
"""
Playwright browser installation utility for optional JavaScript rendering crawler.
"""
import subprocess
import sys

def install_playwright():
    """Install Playwright package and chromium browser binary"""
    try:
        print("📦 Installing Playwright Python package...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        
        print("🌐 Installing Chromium browser binaries...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright and Chromium installed successfully!")
    except Exception as e:
        print(f"❌ Playwright installation failed: {e}")
        print("Note: ScrapAI will continue working in standard and lightweight crawler mode without Playwright.")
        sys.exit(1)

if __name__ == "__main__":
    install_playwright()
