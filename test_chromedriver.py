#!/usr/bin/env python3

import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_chromedriver():
    print("Testing ChromeDriver setup...")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    # Test direct path
    try:
        print("Testing direct path method...")
        service = Service("/Users/kalipour/.cache/selenium/chromedriver/mac-arm64/140.0.7339.207/chromedriver")
        driver = webdriver.Chrome(service=service, options=options)
        print("✅ Direct path method works!")
        driver.get("https://www.google.com")
        print(f"✅ Page title: {driver.title}")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ Direct path method failed: {e}")

    # Test system path
    try:
        print("Testing system path method...")
        driver = webdriver.Chrome(options=options)
        print("✅ System path method works!")
        driver.quit()
        return True
    except Exception as e:
        print(f"❌ System path method failed: {e}")

    return False

if __name__ == "__main__":
    success = test_chromedriver()
    sys.exit(0 if success else 1)