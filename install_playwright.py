#!/usr/bin/env python3
import subimport
import sys

def install_playwright():
    """Install Playwright browsers"""
    try:
        # Install Playwright Python package
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        
        # Install browsers
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Playwright installed successfully")
    except Exception as e:
        print(f"❌ Playwright installation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    install_playwright()
