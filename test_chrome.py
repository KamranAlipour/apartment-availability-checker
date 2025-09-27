#!/usr/bin/env python3

import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

def test_chromedriver():
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")

    driver_path = "/Users/kalipour/.cache/selenium/chromedriver/mac-arm64/140.0.7339.207/chromedriver"

    try:
        print(f"Testing ChromeDriver at: {driver_path}")
        print(f"File exists: {os.path.exists(driver_path)}")
        print(f"File is executable: {os.access(driver_path, os.X_OK)}")

        service = Service(driver_path)
        driver = webdriver.Chrome(service=service, options=options)
        driver.get("https://www.google.com")
        print(f"Success! Page title: {driver.title}")
        driver.quit()
        return True

    except Exception as e:
        print(f"Error: {e}")
        return False

if __name__ == "__main__":
    test_chromedriver()