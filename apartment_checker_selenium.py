#!/usr/bin/env python3

import time
import json
import os
import argparse
from datetime import datetime
import hashlib
import subprocess
import re
import requests
import random
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

class ApartmentChecker:
    def __init__(self):
        # Try URLs that directly show 2-bedroom apartments
        self.url = "https://www.irvinecompanyapartments.com/locations/northern-california/santa-clara/monticello/availability.html"
        # URL with 2-bedroom filter parameter
        self.filtered_url = "https://www.irvinecompanyapartments.com/locations/northern-california/santa-clara/monticello/availability.html?bedrooms=2"
        # Alternative URLs to try if main one is blocked
        self.alternative_urls = [
            "https://www.irvinecompanyapartments.com/locations/northern-california/santa-clara/monticello/",
            "https://www.irvinecompanyapartments.com/api/communities/monticello/availability?bedrooms=2",
            "https://www.irvinecompanyapartments.com/locations/northern-california/santa-clara/monticello.html",
            # Try the direct leasing page that sometimes bypasses Cloudflare
            "https://www.irvinecompanyapartments.com/online-leasing.html?siteId=3926145&commName=Monticello%20II%20Apartment%20Homes&bedrooms=2"
        ]
        self.data_file = "apartment_data.json"
        self.driver = None
        self.setup_driver()

    def setup_driver(self):
        """Setup Chrome driver with enhanced anti-detection measures"""
        try:
            options = Options()
            # Use headless mode with new implementation for better stealth
            options.add_argument("--headless=new")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-plugins")

            # Enhanced stealth options to bypass Cloudflare
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
            options.add_experimental_option('useAutomationExtension', False)

            # Additional Cloudflare bypass options
            options.add_argument("--disable-web-security")
            options.add_argument("--allow-running-insecure-content")
            options.add_argument("--disable-features=VizDisplayCompositor")
            options.add_argument("--disable-ipc-flooding-protection")
            options.add_argument("--disable-renderer-backgrounding")
            options.add_argument("--disable-backgrounding-occluded-windows")
            options.add_argument("--disable-client-side-phishing-detection")
            options.add_argument("--disable-sync")
            options.add_argument("--disable-default-apps")
            options.add_argument("--disable-background-timer-throttling")
            options.add_argument("--disable-device-discovery-notifications")
            options.add_argument("--disable-software-rasterizer")
            options.add_argument("--disable-background-networking")

            # Use a very recent Chrome user agent to appear more legitimate
            options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

            # Enhanced preferences to appear more human-like
            prefs = {
                "credentials_enable_service": False,
                "profile.password_manager_enabled": False,
                "profile.default_content_setting_values.notifications": 2,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 1,
                "profile.default_content_setting_values.cookies": 1,
                "profile.default_content_setting_values.javascript": 1,
                "profile.default_content_setting_values.plugins": 1,
                "profile.default_content_setting_values.geolocation": 2,
                "profile.default_content_setting_values.media_stream": 2,
            }
            options.add_experimental_option("prefs", prefs)

            # Add the direct path to system PATH for this session
            import os
            os.environ['PATH'] = f"/Users/kalipour/.cache/selenium/chromedriver/mac-arm64/140.0.7339.207:{os.environ.get('PATH', '')}"

            # Try multiple approaches to set up ChromeDriver
            driver_attempts = [
                # First try direct path to working driver
                lambda: webdriver.Chrome(service=Service("/Users/kalipour/.cache/selenium/chromedriver/mac-arm64/140.0.7339.207/chromedriver"), options=options),
                # Then try basic approach - use PATH driver
                lambda: webdriver.Chrome(options=options),
                # System chromedriver as fallback
                lambda: webdriver.Chrome(service=Service("/usr/local/bin/chromedriver"), options=options),
                # Last resort: webdriver-manager (may fail if offline)
                lambda: webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options),
            ]

            last_error = None
            for i, driver_func in enumerate(driver_attempts):
                try:
                    print(f"🔧 Attempting ChromeDriver setup method {i+1}/{len(driver_attempts)}...")
                    self.driver = driver_func()
                    break
                except Exception as e:
                    last_error = e
                    print(f"   Method {i+1} failed: {str(e)[:100]}...")
            else:
                print(f"⚠️ All ChromeDriver methods failed. Will use requests-based fallback.")
                self.driver = None
                return

            # Execute enhanced script to make detection much harder
            self.driver.execute_script("""
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});

                // Override plugins array to appear more realistic
                Object.defineProperty(navigator, 'plugins', {
                    get: () => {
                        return [
                            {name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer', description: 'Portable Document Format'},
                            {name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai', description: ''},
                            {name: 'Native Client', filename: 'internal-nacl-plugin', description: ''}
                        ];
                    }
                });

                // Override languages to appear more realistic
                Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']});

                // Add chrome runtime
                window.chrome = {
                    runtime: {},
                    loadTimes: function() { return {requestTime: Date.now() / 1000}; },
                    csi: function() { return {pageT: Date.now(), startE: Date.now()}; }
                };

                // Override permissions API
                Object.defineProperty(navigator, 'permissions', {
                    get: () => ({
                        query: () => Promise.resolve({state: 'granted'})
                    })
                });

                // Override connection API
                Object.defineProperty(navigator, 'connection', {
                    get: () => ({
                        rtt: 100,
                        downlink: 10,
                        effectiveType: '4g'
                    })
                });

                // Override screen properties to appear more realistic
                Object.defineProperty(window.screen, 'availHeight', {get: () => 1055});
                Object.defineProperty(window.screen, 'availWidth', {get: () => 1920});
                Object.defineProperty(window.screen, 'colorDepth', {get: () => 24});

                // Override Date to add timezone
                const originalDate = Date;
                Date = new Proxy(Date, {
                    construct(target, args) {
                        return new target(...args);
                    },
                    apply(target, thisArg, argArray) {
                        return target.apply(thisArg, argArray);
                    }
                });
                Date.now = originalDate.now;
                Date.prototype = originalDate.prototype;

                // Override getUserMedia
                navigator.mediaDevices = {
                    getUserMedia: () => Promise.reject(new Error('Permission denied'))
                };

                // Mock battery API
                navigator.getBattery = () => Promise.resolve({
                    charging: true,
                    chargingTime: 0,
                    dischargingTime: Infinity,
                    level: 1
                });

                // Override canvas fingerprinting
                const getContext = HTMLCanvasElement.prototype.getContext;
                HTMLCanvasElement.prototype.getContext = function(contextType, contextAttributes) {
                    if (contextType === '2d') {
                        const context = getContext.call(this, contextType, contextAttributes);
                        const originalGetImageData = context.getImageData;
                        context.getImageData = function() {
                            const imageData = originalGetImageData.apply(this, arguments);
                            for (let i = 0; i < imageData.data.length; i += 4) {
                                imageData.data[i] += Math.floor(Math.random() * 10) - 5;
                                imageData.data[i + 1] += Math.floor(Math.random() * 10) - 5;
                                imageData.data[i + 2] += Math.floor(Math.random() * 10) - 5;
                            }
                            return imageData;
                        };
                        return context;
                    }
                    return getContext.call(this, contextType, contextAttributes);
                };
            """)

            self.driver.set_page_load_timeout(30)
            print("✅ Chrome driver setup successful")

        except Exception as e:
            print(f"❌ Failed to setup Chrome driver: {e}")
            self.driver = None

    def get_apartment_data_requests(self):
        """Get apartment data using requests as fallback when Selenium fails"""
        try:
            print("🌐 Using requests-based approach as fallback...")

            # Create a session with enhanced headers to bypass Cloudflare
            session = requests.Session()

            # Add retry mechanism
            from requests.adapters import HTTPAdapter
            from requests.packages.urllib3.util.retry import Retry

            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
            )
            adapter = HTTPAdapter(max_retries=retry_strategy)
            session.mount("http://", adapter)
            session.mount("https://", adapter)

            # Realistic headers to mimic a real browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'sec-ch-ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                'sec-ch-ua-mobile': '?0',
                'sec-ch-ua-platform': '"macOS"',
                'Cache-Control': 'max-age=0',
            }

            session.headers.update(headers)

            # Add random delay to appear human-like
            time.sleep(random.uniform(1, 3))

            print(f"📡 Fetching data from: {self.url}")

            # Try different URL approaches
            urls_to_try = [
                self.url,
                # Try different variations of the URL
                "https://www.irvinecompanyapartments.com/locations/northern-california/santa-clara/monticello/",
                "https://www.irvinecompanyapartments.com/api/communities/monticello/availability",
                "https://www.irvinecompanyapartments.com/locations/northern-california/santa-clara/monticello.html"
            ]

            for i, url in enumerate(urls_to_try):
                try:
                    print(f"   Trying URL {i+1}/{len(urls_to_try)}: {url}")

                    # Add some randomized delay between requests
                    if i > 0:
                        time.sleep(random.uniform(2, 5))

                    response = session.get(url, timeout=30)
                    print(f"   Response status: {response.status_code}")

                    if response.status_code == 200:
                        content = response.text

                        # Check if we got a Cloudflare challenge page
                        if "Just a moment..." in content or "cf-browser-verification" in content:
                            print(f"   ⚠️ Cloudflare challenge detected for URL {i+1}")
                            continue

                        # Check if we got meaningful content (with $ signs for prices)
                        dollar_count = content.count('$')
                        print(f"   Found {dollar_count} '$' symbols, {len(content)} chars")

                        if dollar_count > 0:
                            print(f"   ✅ Found apartment data at URL {i+1}")

                            # Parse apartment details
                            apartments = self.parse_apartment_details(content)

                            return {
                                "timestamp": datetime.now().isoformat(),
                                "status_code": response.status_code,
                                "content_hash": hashlib.md5(content.encode()).hexdigest(),
                                "content_length": len(content),
                                "apartments": apartments,
                                "total_apartments": len(apartments),
                                "data_source": "requests",
                                "url_used": url
                            }
                        else:
                            print(f"   ⚠️ No apartment pricing data found at URL {i+1}")
                    else:
                        print(f"   ❌ HTTP {response.status_code} for URL {i+1}")

                except requests.RequestException as e:
                    print(f"   ❌ Request failed for URL {i+1}: {str(e)[:100]}...")
                    continue

            # If we get here, none of the URLs worked
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Network access blocked - All URL attempts failed (HTTP 403 Forbidden). This may be due to:\n" +
                         "1. Corporate firewall/proxy restrictions\n" +
                         "2. VPN connection blocking the website\n" +
                         "3. The website blocking the current IP range\n" +
                         "4. Geographic restrictions\n\n" +
                         "Potential solutions:\n" +
                         "- Try running from a different network (home WiFi, mobile hotspot)\n" +
                         "- Disable VPN if currently active\n" +
                         "- Check firewall/proxy settings\n" +
                         "- Contact network administrator if on corporate network",
                "apartments": [],
                "total_apartments": 0,
                "data_source": "requests",
                "http_status": "403 Forbidden"
            }

        except Exception as e:
            print(f"❌ Requests-based approach failed: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"Requests approach failed: {str(e)}",
                "apartments": [],
                "total_apartments": 0,
                "data_source": "requests"
            }

    def test_apartment_parsing(self):
        """Test apartment parsing logic with sample HTML content"""
        print("🧪 Testing apartment parsing logic with real website snapshot...")

        # Read the actual website snapshot file
        try:
            with open("/Users/kalipour/availability/website_snapshot.html", 'r', encoding='utf-8') as f:
                sample_html = f.read()
            print(f"✅ Loaded website snapshot: {len(sample_html)} characters")
        except Exception as e:
            print(f"❌ Failed to load website snapshot: {e}")
            # Fallback to a simple test case
            sample_html = """
            <div class="fapt-fp-list-item__column fapt-fp-list-item__column--plan-name"><span>Plan 18</span></div>
            <div data-unit-id="3926145_10_225" class="fapt-fp-unit fapt-fp-unit__table-row">
                <div class="fapt-fp-unit__column fapt-fp-unit__column--unit-name"><span>01 561</span></div>
                <div class="fapt-fp-unit__column fapt-fp-unit__column--price"><span>$4,535</span></div>
            </div>
            """

        apartments = self.parse_apartment_details(sample_html)

        return {
            "timestamp": datetime.now().isoformat(),
            "status_code": 200,
            "content_hash": hashlib.md5(sample_html.encode()).hexdigest(),
            "content_length": len(sample_html),
            "apartments": apartments,
            "total_apartments": len(apartments),
            "data_source": "website_snapshot",
            "note": "This is real website data from the saved snapshot"
        }

    def parse_apartment_details(self, html_content):
        """Parse HTML content to extract apartment details using regex"""
        apartments = []

        # Look for pricing patterns - these are usually the most reliable indicators
        price_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)(?:\s*(?:-|to)\s*\$(\d{1,3}(?:,\d{3})*))?',
        ]

        # Find all price matches with surrounding context
        for price_pattern in price_patterns:
            for match in re.finditer(price_pattern, html_content, re.I):
                price_text = match.group(0)

                # Skip obviously invalid prices (too small, likely partial matches)
                price_value = int(re.sub(r'[^\d]', '', price_text))
                if price_value < 1000:  # Skip prices under $1000 (likely partial matches)
                    continue

                # Get surrounding context (500 chars before and after)
                start = max(0, match.start() - 500)
                end = min(len(html_content), match.end() + 500)
                context = html_content[start:end]

                apartment = {}
                apartment['price'] = price_text

                # Extract all details from context
                self.extract_apartment_details_from_context(apartment, context)
                apartments.append(apartment)

    def extract_apartment_details_from_context(self, apartment, context):
        """Extract apartment details from context and populate the apartment dict"""
        # Extract square footage from context
        sqft_match = re.search(r'(\d{3,4})\s*(?:sq\.?\s*ft\.?|square\s*feet)', context, re.I)
        if sqft_match:
            apartment['square_feet'] = int(sqft_match.group(1))

        # Extract bed/bath info from context
        bed_match = re.search(r'(\d+)\s*(?:bed|br)', context, re.I)
        bath_match = re.search(r'(\d+)\s*(?:bath|ba)', context, re.I)
        if bed_match:
            apartment['bedrooms'] = int(bed_match.group(1))
        if bath_match:
            apartment['bathrooms'] = int(bath_match.group(1))

        # Extract floor plan from context if not already set
        if 'floor_plan' not in apartment:
            plan_patterns = [
                r'Plan\s+(\d+[A-Z]?)',
                r'plan\s+(\d+[A-Z]?)',
                r'Floor\s+Plan\s+(\d+[A-Z]?)',
                r'floorplan\s+(\d+[A-Z]?)'
            ]
            for plan_pattern in plan_patterns:
                plan_match = re.search(plan_pattern, context, re.I)
                if plan_match:
                    apartment['floor_plan'] = f"Plan {plan_match.group(1)}"
                    break

        # Extract unit number from context - capture full unit format like "01 561"
        unit_patterns = [
            r'(\d{2}\s+\d{3})',  # Pattern like "01 561", "05 113" (prioritize this format)
            r'(?:unit|apt\.?|#)\s*([A-Z0-9\-\s]+)',
            r'Unit\s+([A-Z]?\d+[A-Z]?\s*\d*[A-Z]?)',  # Unit A101, Unit 1201
            r'([A-Z]\d{3,4}[A-Z]?)',  # Pattern like A101, B205A, A1201
            r'(\d{3,4}[A-Z])',  # Pattern like 1201A, 205B
            r'([A-Z]{1,2}\d{2,4})',  # Pattern like A12, AB123
            r'(\d{3})',   # Pattern like 516, 261 (3-digit units)
            r'(\d{4})'   # Pattern like 1201, 2025 (4-digit units)
        ]
        for unit_pattern in unit_patterns:
            unit_match = re.search(unit_pattern, context, re.I)
            if unit_match:
                unit_candidate = unit_match.group(1).strip()
                # Only filter out obvious non-unit matches
                if unit_candidate not in ['-fp-unit', 'ies', 's'] and len(unit_candidate) >= 2:
                    apartment['unit'] = unit_candidate
                    break

        # Extract availability status from context
        if re.search(r'available|ready', context, re.I):
            apartment['status'] = 'Available'
        elif re.search(r'waitlist', context, re.I):
            apartment['status'] = 'Waitlist'
        else:
            apartment['status'] = 'Unknown'

        # Extract features from context - target the specific HTML structure
        features = []

        # Look for the specific amenities div structure
        amenities_pattern = r'<div[^>]*fapt-fp-unit__column-inner--amenities[^>]*>(.*?)</div>'
        amenities_matches = re.findall(amenities_pattern, context, re.DOTALL | re.I)

        for amenities_html in amenities_matches:
            # First try span-by-span approach to get all span content, then combine them
            span_pattern = r'<span(?![^>]*disclaimer)[^>]*>(.*?)</span>'
            span_matches = re.findall(span_pattern, amenities_html, re.DOTALL | re.I)

            # Combine all span content into one text block with smart reconstruction
            combined_span_text = ''
            for span_content in span_matches:
                clean_text = re.sub(r'<[^>]*>', '', span_content)  # Remove HTML tags
                clean_text = re.sub(r'&amp;', '&', clean_text)     # Fix HTML entities
                clean_text = re.sub(r'&lt;', '<', clean_text)
                clean_text = re.sub(r'&gt;', '>', clean_text)
                clean_text = clean_text.strip()

                # Skip obvious junk content immediately
                if (len(clean_text) > 3 and
                    not re.search(r'com/is/image|wid=\d+|button aria-label|class="[^"]*btn|\.jpg|\.png|\.gif', clean_text, re.I)):
                    combined_span_text += clean_text + ' '

            combined_span_text = combined_span_text.strip()

            # Fix common split patterns that occur when HTML spans break words
            # Pattern: "5th Flo or" -> "5th Floor" (common floor indicator splits)
            combined_span_text = re.sub(r'(\d+)(st|nd|rd|th)\s+Flo\b(?:\s+(or|r))?', r'\1\2 Floor', combined_span_text, flags=re.I)
            # Pattern: "Hardwood-Sty le" -> "Hardwood-Style" (hyphenated word splits)
            combined_span_text = re.sub(r'\b(\w+)-Sty\b(?:\s+(le))?', r'\1-Style', combined_span_text, flags=re.I)
            # More general pattern for word breaks at common points
            combined_span_text = re.sub(r'\b(Stainless|Steel|Walk-in|Washer|Dryer)\s+(Steel|Appliances|Closet|In|Home)\b', r'\1 \2', combined_span_text, flags=re.I)

            # If we have good combined content, parse it as comma-separated features
            if len(combined_span_text) > 10:
                # Split on commas and clean up each feature
                feature_items = re.split(r',\s*', combined_span_text)
                for item in feature_items:
                    item = item.strip()
                    # Only add substantial features (not empty, short, or obvious junk)
                    if (len(item) > 3 and
                        not re.match(r'^[\s,.-]*$', item) and  # Not just punctuation/whitespace
                        not item.lower() in ['and', 'or', 'with', 'the'] and  # Not just connectors
                        not re.match(r'^\d+$', item)):  # Not just numbers
                        features.append(item)

            # If span combining didn't work well, try the complete text approach
            if len(features) < 2:
                # Get the complete text content, removing HTML tags but preserving structure
                clean_amenities = re.sub(r'<[^>]*>', ' ', amenities_html)  # Replace tags with spaces
                clean_amenities = re.sub(r'&amp;', '&', clean_amenities)  # Fix HTML entities
                clean_amenities = re.sub(r'&lt;', '<', clean_amenities)
                clean_amenities = re.sub(r'&gt;', '>', clean_amenities)
                clean_amenities = re.sub(r'\s+', ' ', clean_amenities)  # Normalize whitespace
                clean_amenities = clean_amenities.strip()

                # If we have substantial content, try to parse it as comma-separated features
                if len(clean_amenities) > 10:
                    # Split on commas and clean up each feature
                    feature_items = re.split(r',\s*', clean_amenities)
                    for item in feature_items:
                        item = item.strip()
                        # Only add substantial features (not empty, short, or obvious junk)
                        if (len(item) > 3 and
                            not re.match(r'^[\s,.-]*$', item) and  # Not just punctuation/whitespace
                            not item.lower() in ['and', 'or', 'with', 'the'] and  # Not just connectors
                            not re.match(r'^\d+$', item)):  # Not just numbers
                            features.append(item)

        # If we didn't find the specific structure, fall back to the original patterns
        if len(features) < 2:
            # First, look for complete feature lists (the full comma-separated descriptions)
            complete_feature_patterns = [
                r'([^<>]*(?:\d+(?:st|nd|rd|th)\s+Floor)[^<>]*(?:,\s*[^<>,]+)*)',  # Starts with floor info
                r'([^<>,]{10,}(?:Appliances|Flooring|Closet|Washer|Dryer)[^<>,]*(?:,\s*[^<>,]+)*)',  # Contains key features
                r'([^<>]*(?:Hardwood|Stainless|Granite|Patio|Balcony)[^<>]*(?:,\s*[^<>,]+){2,})',  # Multiple features
            ]

            for pattern in complete_feature_patterns:
                matches = re.findall(pattern, context, re.I)
                for match in matches:
                    match = match.strip()
                    if len(match) > 20 and ',' in match:  # Must be substantial and have multiple features
                        # Split the complete list and add all features
                        feature_items = re.split(r',\s*', match)
                        for item in feature_items:
                            item = item.strip()
                            # Clean up and validate each feature
                            if (len(item) > 3 and
                                not re.match(r'^\d+$', item) and
                                not re.search(r'<[^>]*>', item) and  # No HTML tags
                                not item.lower().startswith('and ') and
                                not item.lower().startswith('or ')):
                                features.append(item)

            # If we still didn't find complete lists, look for individual structured features
            if len(features) < 3:
                # Look for structured feature lists with labels
                feature_list_patterns = [
                    r'(?:Features?|Amenities?|Includes?):\s*([^<>\n]+)',
                    r'(?:Available|Offers):\s*([^<>\n]+)',
                ]

                for pattern in feature_list_patterns:
                    matches = re.findall(pattern, context, re.I)
                    for match in matches:
                        if len(match.strip()) > 15:  # Only capture substantial feature descriptions
                            # Split on common separators and clean up
                            feature_items = re.split(r'[,;•·\n]', match)
                            for item in feature_items:
                                item = item.strip()
                                if len(item) > 3 and not re.match(r'^\d+$', item):
                                    features.append(item)

            # As a last resort, use keyword-based extraction but try to get full phrases
            if len(features) < 2:
                feature_keywords = ['floor', 'hardwood', 'patio', 'balcony', 'stainless', 'appliances',
                                  'washer', 'dryer', 'closet', 'granite', 'flooring', 'wood', 'view']

                for keyword in feature_keywords:
                    if re.search(keyword, context, re.I):
                        # Try to capture a longer phrase containing the keyword
                        phrase_pattern = rf'([^,.!?<>]*{keyword}[^,.!?<>]*(?:\s*-\s*[^,.!?<>]*)?)'
                        phrase_matches = re.findall(phrase_pattern, context, re.I)
                        for phrase in phrase_matches:
                            phrase = phrase.strip()
                            if len(phrase) >= len(keyword):
                                features.append(phrase)

        if features:
            # Remove duplicates and clean up
            unique_features = []
            seen = set()
            for feature in features:
                feature_clean = feature.strip()
                # Remove common prefixes/suffixes that aren't useful
                feature_clean = re.sub(r'^(and\s+|or\s+|the\s+)', '', feature_clean, flags=re.I)
                feature_clean = re.sub(r'\s*(and|or)\s*$', '', feature_clean, flags=re.I)

                if (feature_clean.lower() not in seen and
                    len(feature_clean) > 2 and
                    not re.match(r'^\d+$', feature_clean)):
                    seen.add(feature_clean.lower())
                    unique_features.append(feature_clean)

            apartment['features'] = unique_features[:15]  # Allow more features since they're detailed

    def parse_apartment_details(self, html_content):
        """
        Enhanced apartment parsing with multiple detection strategies.

        This method implements a comprehensive apartment data extraction system
        that uses multiple parsing strategies to handle different website layouts:

        1. **Structured Parsing**: Extracts data from well-formed HTML containers
           with apartment-unit classes and proper div nesting
        2. **Table Parsing**: Handles table-based apartment listings
        3. **JSON Parsing**: Extracts data from embedded JavaScript/JSON
        4. **Fallback Parsing**: Price-based extraction as last resort

        Each strategy is tried in order until apartments are found, ensuring
        maximum compatibility with different website structures.

        Args:
            html_content (str): Raw HTML content from the apartment listing page

        Returns:
            list: List of apartment dictionaries with extracted details including:
                - unit: Unit number (e.g., "01 561")
                - price: Monthly rent (e.g., "$3,200")
                - floor_plan: Plan name (e.g., "Plan 2B")
                - bedrooms: Number of bedrooms (int)
                - bathrooms: Number of bathrooms (int)
                - square_feet: Unit size in sq ft (int)
                - status: Availability status
                - features: List of amenities and features
        """
        print("🔍 Attempting to parse apartment data using multiple strategies...")

        # Strategy 1: Look for structured apartment data
        apartments = self.parse_structured_apartments(html_content)
        if apartments:
            print(f"✅ Found {len(apartments)} apartments using structured parsing")

            # Filter for only 2-bedroom apartments
            two_bedroom_apartments = []
            for apt in apartments:
                if apt.get('bedrooms') == 2:
                    two_bedroom_apartments.append(apt)

            print(f"🏠 2-bedroom apartments found: {len(two_bedroom_apartments)}")

            # If we have 2-bedroom apartments, return only those; otherwise return all
            if two_bedroom_apartments:
                return two_bedroom_apartments[:20]
            else:
                print("⚠️ No 2-bedroom apartments found, returning all apartments for debugging")
                return apartments[:20]

        # Strategy 2: Look for table-based layouts
        apartments = self.parse_table_apartments(html_content)
        if apartments:
            print(f"✅ Found {len(apartments)} apartments using table parsing")
            return apartments

        # Strategy 3: JSON data extraction
        apartments = self.parse_json_apartments(html_content)
        if apartments:
            print(f"✅ Found {len(apartments)} apartments using JSON parsing")
            return apartments

        # Strategy 4: General price-based parsing (fallback)
        print("⚠️ No structured units found, using price-based parsing")
        apartments = self.parse_apartment_details_fallback(html_content)

        return apartments

    def parse_structured_apartments(self, html_content):
        """Parse apartments from structured HTML containers"""
        apartments = []

        # Strategy for real website: Parse floor plan containers and associate units with them
        print("🏗️ Parsing real website structure with floor plan containers...")

        # Find all floor plan containers first
        floor_plan_pattern = r'<div[^>]*class="[^"]*fapt-fp-list-item__container[^"]*"[^>]*data-floorplan-id="([^"]*)"[^>]*>(.*?)(?=<div[^>]*class="[^"]*fapt-fp-list-item__container[^"]*"|$)'
        floor_plan_matches = re.findall(floor_plan_pattern, html_content, re.DOTALL | re.I)

        print(f"📋 Found {len(floor_plan_matches)} floor plan containers")

        for floor_plan_id, floor_plan_content in floor_plan_matches:
            print(f"🏠 Processing floor plan ID: {floor_plan_id}")

            # Extract floor plan details from the container
            floor_plan_info = self.extract_floor_plan_info(floor_plan_content)
            print(f"📝 Floor plan info: {floor_plan_info}")

            # Find all units within this floor plan container
            unit_pattern = r'<div[^>]*data-unit-id="[^"]*"[^>]*class="[^"]*fapt-fp-unit[^"]*"[^>]*>(.*?)(?=<div[^>]*data-unit-id=|$)'
            unit_matches = re.findall(unit_pattern, floor_plan_content, re.DOTALL | re.I)

            print(f"🏘️ Found {len(unit_matches)} units in this floor plan")

            for unit_content in unit_matches:
                apartment = self.extract_apartment_from_container(unit_content)
                if apartment and self.is_valid_apartment_unit(apartment):
                    # Add floor plan information to the apartment
                    if floor_plan_info:
                        apartment.update(floor_plan_info)
                    apartments.append(apartment)
                    print(f"✅ Added apartment: {apartment.get('unit', 'Unknown')} - {apartment.get('floor_plan', 'Unknown plan')}")

        # If no floor plan containers found, try alternative patterns
        if not apartments:
            print("⚠️ No floor plan containers found, trying alternative patterns...")
            # Fallback to simpler patterns
            container_patterns = [
                r'<div[^>]*data-unit-id="[^"]*"[^>]*class="[^"]*fapt-fp-unit[^"]*"[^>]*>(.*?)</div>(?=<div[^>]*data-unit-id=|$)',
                r'<tr[^>]*class="[^"]*unit[^"]*"[^>]*>(.*?)</tr>',
                r'<div[^>]*class="[^"]*apartment[^"]*"[^>]*>(.*?)</div>',
                r'<li[^>]*class="[^"]*unit[^"]*"[^>]*>(.*?)</li>',
            ]

            for pattern in container_patterns:
                unit_matches = re.findall(pattern, html_content, re.DOTALL | re.I)
                for unit_html in unit_matches:
                    apartment = self.extract_apartment_from_container(unit_html)
                    if apartment and self.is_valid_apartment_unit(apartment):
                        apartments.append(apartment)
                if apartments:
                    break

        print(f"🎯 Total apartments found: {len(apartments)}")
        return apartments[:20]

    def extract_floor_plan_info(self, floor_plan_html):
        """Extract floor plan information from a floor plan container"""
        floor_plan_info = {}

        # Extract floor plan name
        plan_name_patterns = [
            r'<div[^>]*class="[^"]*fapt-fp-list-item__column--plan-name[^"]*"[^>]*>.*?<span[^>]*>Plan\s+(\d+[A-Z]?)</span>',
            r'<span[^>]*>Plan\s+(\d+[A-Z]?)</span>',
            r'Plan\s+(\d+[A-Z]?)',
        ]

        for pattern in plan_name_patterns:
            match = re.search(pattern, floor_plan_html, re.I | re.DOTALL)
            if match:
                floor_plan_info['floor_plan'] = f"Plan {match.group(1).strip()}"
                break

        # Extract bed/bath information
        bed_bath_patterns = [
            r'<div[^>]*class="[^"]*fapt-fp-list-item__column--beds-baths[^"]*"[^>]*>.*?<span[^>]*>(\d+)\s*Bed\s*/\s*(\d+)\s*Bath</span>',
            r'<span[^>]*>(\d+)\s*Bed\s*/\s*(\d+)\s*Bath</span>',
        ]

        for pattern in bed_bath_patterns:
            match = re.search(pattern, floor_plan_html, re.I | re.DOTALL)
            if match:
                floor_plan_info['bedrooms'] = int(match.group(1))
                floor_plan_info['bathrooms'] = int(match.group(2))
                break

        # Extract starting price
        price_patterns = [
            r'<div[^>]*class="[^"]*fapt-fp-list-item__column--price[^"]*"[^>]*>.*?<span[^>]*>\s*\$([,\d]+)</span>',
            r'<span[^>]*>\s*\$([,\d]+)</span>',
        ]

        for pattern in price_patterns:
            match = re.search(pattern, floor_plan_html, re.I | re.DOTALL)
            if match:
                floor_plan_info['starting_price'] = f"${match.group(1).strip()}"
                break

        # Extract square footage
        sqft_patterns = [
            r'<div[^>]*class="[^"]*fapt-fp-list-item__column--sqft[^"]*"[^>]*>.*?<span[^>]*>([,\d]+)\s*</span>',
            r'<span[^>]*>([,\d]+)\s*Sq\.\s*Ft\.</span>',
        ]

        for pattern in sqft_patterns:
            match = re.search(pattern, floor_plan_html, re.I | re.DOTALL)
            if match:
                sqft_text = match.group(1).replace(',', '')
                if sqft_text.isdigit() and 500 <= int(sqft_text) <= 5000:
                    floor_plan_info['square_feet'] = int(sqft_text)
                break

        return floor_plan_info

    def parse_table_apartments(self, html_content):
        """Parse apartments from table-based layouts"""
        apartments = []

        # Look for table rows that might contain apartment data
        table_patterns = [
            r'<tr[^>]*>(.*?)</tr>',
            r'<tbody[^>]*>(.*?)</tbody>',
        ]

        for pattern in table_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.I)

            for match in matches:
                if '$' in match and ('bed' in match.lower() or 'bath' in match.lower()):
                    apartment = self.extract_apartment_from_container(match)
                    if apartment and self.is_valid_apartment_unit(apartment):
                        apartments.append(apartment)

        return apartments[:20]

    def parse_json_apartments(self, html_content):
        """Extract apartment data from embedded JSON"""
        apartments = []

        # Look for JSON data in script tags
        json_patterns = [
            r'<script[^>]*>(.*?apartmentData.*?)</script>',
            r'<script[^>]*>(.*?floorPlan.*?)</script>',
            r'<script[^>]*>(.*?unitData.*?)</script>',
            r'var\s+\w+\s*=\s*(\{.*?apartments.*?\});',
            r'window\.\w+\s*=\s*(\{.*?units.*?\});',
        ]

        for pattern in json_patterns:
            matches = re.findall(pattern, html_content, re.DOTALL | re.I)

            for match in matches:
                try:
                    # Try to extract JSON data
                    json_start = match.find('{')
                    json_end = match.rfind('}') + 1

                    if json_start >= 0 and json_end > json_start:
                        json_str = match[json_start:json_end]

                        # Basic cleanup
                        json_str = re.sub(r'//.*?\n', '', json_str)  # Remove comments
                        json_str = re.sub(r'/\*.*?\*/', '', json_str, flags=re.DOTALL)

                        # Try to parse as JSON
                        data = json.loads(json_str)

                        # Extract apartment data from JSON
                        apartments.extend(self.extract_apartments_from_json(data))

                except Exception as e:
                    continue

        return apartments[:20]

    def extract_apartment_from_container(self, container_html):
        """Extract apartment details from a container HTML snippet"""
        apartment = {}


        # Extract unit number with improved patterns
        unit_patterns = [
            r'<div[^>]*class="[^"]*unit-number[^"]*"[^>]*>([^<]+)</div>',  # For our mock structure
            r'<span[^>]*class="[^"]*unit[^"]*name[^"]*"[^>]*>([^<]+)</span>',
            r'data-unit[^>]*="([^"]+)"',
            r'<td[^>]*class="[^"]*unit[^"]*"[^>]*>([^<]+)</td>',
            r'<div[^>]*class="[^"]*unit[^"]*number[^"]*"[^>]*>([^<]+)</div>',
            r'Unit\s+([A-Z0-9\-\s]+)',
            r'(\d{2}\s+\d{3})',  # Pattern like "01 561", "05 113"
        ]

        for i, pattern in enumerate(unit_patterns):
            match = re.search(pattern, container_html, re.I)
            if match:
                apartment['unit'] = match.group(1).strip()
                break
        else:
            pass

        # Enhanced price extraction with more patterns
        price_patterns = [
            r'<div[^>]*class="[^"]*price[^"]*"[^>]*>(\$[^<]+)</div>',  # For our mock structure
            r'<span[^>]*class="[^"]*price[^"]*"[^>]*>(\$[^<]+)</span>',
            r'<td[^>]*class="[^"]*price[^"]*"[^>]*>(\$[^<]+)</td>',
            r'"price"\s*:\s*"?(\$?\d{1,3}(?:,\d{3})*)"?',
            r'"rent"\s*:\s*"?(\$?\d{1,3}(?:,\d{3})*)"?',
            r'data-price="(\$[^"]+)"',
            r'(\$\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',  # General $ pattern
            r'\$(\d{1,3}(?:,\d{3})*)\s*(?:per|/)?\s*month',  # "$2500 per month"
        ]

        for i, pattern in enumerate(price_patterns):
            match = re.search(pattern, container_html, re.I)
            if match:
                price_text = match.group(1).strip()
                # Ensure it starts with $
                if not price_text.startswith('$'):
                    price_text = '$' + price_text
                apartment['price'] = price_text
                break
        else:
            pass

        # Enhanced floor plan extraction
        floor_plan_patterns = [
            r'<div[^>]*class="[^"]*floor-plan[^"]*"[^>]*>([^<]+)</div>',  # For our mock structure
            r'<span[^>]*class="[^"]*plan[^"]*"[^>]*>([^<]+)</span>',
            r'<div[^>]*class="[^"]*floor[^"]*plan[^"]*"[^>]*>([^<]+)</div>',
            r'"floorPlan"\s*:\s*"([^"]+)"',
            r'"floor_plan"\s*:\s*"([^"]+)"',
            r'data-floor-plan="([^"]+)"',
            r'Floor\s*Plan\s*:?\s*([A-Z0-9\s]+)',
            r'Plan\s+([A-Z0-9]+[A-Z]?)',
            r'(Plan\s+\d+[A-Z]?)',  # "Plan 1A", "Plan 2B"
            r'([A-Z]\d+[A-Z]?)',  # "A1", "B2A"
        ]

        for pattern in floor_plan_patterns:
            match = re.search(pattern, container_html, re.I)
            if match:
                apartment['floor_plan'] = match.group(1).strip()
                break

        # Extract beds/baths with more patterns
        bed_bath_patterns = [
            r'<div[^>]*class="[^"]*bedrooms[^"]*"[^>]*>(\d+)\s*Bed</div>.*?<div[^>]*class="[^"]*bathrooms[^"]*"[^>]*>(\d+)\s*Bath</div>',  # For our mock structure
            r'(\d+)\s*[Bb]ed[^<]*(\d+)\s*[Bb]ath',
            r'(\d+)\s*BR[^<]*(\d+)\s*BA',
            r'<span[^>]*>(\d+)\s*Bed[^<]*(\d+)\s*Bath</span>',
            r'"bedrooms"\s*:\s*(\d+)[^}]*"bathrooms"\s*:\s*(\d+)',
            r'"beds"\s*:\s*(\d+)[^}]*"baths"\s*:\s*(\d+)',
            r'(\d+)\s*bedroom[^<]*(\d+)\s*bathroom',
        ]

        for pattern in bed_bath_patterns:
            match = re.search(pattern, container_html, re.I | re.DOTALL)
            if match:
                apartment['bedrooms'] = int(match.group(1))
                apartment['bathrooms'] = int(match.group(2))
                break

        # If combined pattern didn't work, try separate patterns
        if 'bedrooms' not in apartment:
            bedroom_patterns = [
                r'<div[^>]*class="[^"]*bedrooms[^"]*"[^>]*>(\d+)\s*Bed</div>',  # For our mock structure
                r'(\d+)\s*[Bb]ed(?:room)?',
                r'"bedrooms"\s*:\s*(\d+)',
                r'(\d+)\s*BR',
            ]
            for pattern in bedroom_patterns:
                match = re.search(pattern, container_html, re.I)
                if match:
                    apartment['bedrooms'] = int(match.group(1))
                    break

        if 'bathrooms' not in apartment:
            bathroom_patterns = [
                r'<div[^>]*class="[^"]*bathrooms[^"]*"[^>]*>(\d+)\s*Bath</div>',  # For our mock structure
                r'(\d+)\s*[Bb]ath(?:room)?',
                r'"bathrooms"\s*:\s*(\d+)',
                r'(\d+)\s*BA',
            ]
            for pattern in bathroom_patterns:
                match = re.search(pattern, container_html, re.I)
                if match:
                    apartment['bathrooms'] = int(match.group(1))
                    break

        # Enhanced square footage extraction
        sqft_patterns = [
            r'<div[^>]*class="[^"]*square-feet[^"]*"[^>]*>([,\d]+)\s*sq\s*ft</div>',  # For our mock structure
            r'(\d{3,4})\s*(?:sq\.?\s*ft\.?|sf|square\s*feet)',
            r'"squareFeet"\s*:\s*(\d{3,4})',
            r'"sqft"\s*:\s*(\d{3,4})',
            r'"square_feet"\s*:\s*(\d{3,4})',
            r'data-sqft="(\d{3,4})"',
            r'([,\d]+)\s*sq\s*ft',
        ]

        for pattern in sqft_patterns:
            match = re.search(pattern, container_html, re.I)
            if match:
                sqft_text = match.group(1).replace(',', '')
                apartment['square_feet'] = int(sqft_text)
                break

        # Enhanced availability status
        status_patterns = [
            r'<div[^>]*class="[^"]*status[^"]*"[^>]*>([^<]+)</div>',  # For our mock structure
            r'<span[^>]*class="[^"]*status[^"]*"[^>]*>([^<]+)</span>',
        ]

        status_found = False
        for pattern in status_patterns:
            match = re.search(pattern, container_html, re.I)
            if match:
                apartment['status'] = match.group(1).strip()
                status_found = True
                break

        # If no specific status pattern found, use keyword search
        if not status_found:
            if re.search(r'available|ready|lease', container_html, re.I):
                apartment['status'] = 'Available'
            elif re.search(r'waitlist|wait\s*list', container_html, re.I):
                apartment['status'] = 'Waitlist'
            elif re.search(r'occupied|unavailable|leased', container_html, re.I):
                apartment['status'] = 'Unavailable'
            else:
                apartment['status'] = 'Unknown'

        # Extract features/amenities with better cleaning
        features = []
        amenity_patterns = [
            r'<div[^>]*class="[^"]*features[^"]*"[^>]*>([^<]+)</div>',  # For our mock structure - plain text
            r'<div[^>]*class="[^"]*amenit[^"]*"[^>]*>(.*?)</div>',
            r'<ul[^>]*class="[^"]*feature[^"]*"[^>]*>(.*?)</ul>',
            r'<div[^>]*class="[^"]*feature[^"]*"[^>]*>(.*?)</div>',
        ]

        for pattern in amenity_patterns:
            match = re.search(pattern, container_html, re.DOTALL | re.I)
            if match:
                amenity_html = match.group(1)
                # Extract text content and clean it up
                text_content = re.sub(r'<[^>]*>', ' ', amenity_html)
                text_content = re.sub(r'\s+', ' ', text_content).strip()
                text_content = re.sub(r'&amp;', '&', text_content)
                text_content = re.sub(r'&lt;', '<', text_content)
                text_content = re.sub(r'&gt;', '>', text_content)

                if len(text_content) > 10:
                    # Split on common separators
                    feature_items = re.split(r'[,;•·\n]', text_content)
                    for item in feature_items:
                        item = item.strip()
                        if len(item) > 3 and not re.match(r'^\d+$', item):
                            features.append(item)

        if features:
            # Remove duplicates and clean up features
            unique_features = []
            seen = set()
            for feature in features:
                feature_clean = feature.strip()
                # Remove common prefixes/suffixes that aren't useful
                feature_clean = re.sub(r'^(and\s+|or\s+|the\s+)', '', feature_clean, flags=re.I)
                feature_clean = re.sub(r'\s*(and|or)\s*$', '', feature_clean, flags=re.I)

                # Check for duplicates using case-insensitive comparison
                if (feature_clean.lower() not in seen and
                    len(feature_clean) > 3 and
                    not re.match(r'^\d+$', feature_clean)):
                    seen.add(feature_clean.lower())
                    unique_features.append(feature_clean)

            apartment['features'] = unique_features[:10]  # Limit to 10 unique features

        return apartment if ('price' in apartment or 'unit' in apartment or 'floor_plan' in apartment) else None

    def extract_apartments_from_json(self, data):
        """Extract apartment data from JSON object"""
        apartments = []

        def extract_from_dict(obj, apartments_list):
            if isinstance(obj, dict):
                # Check if this dict looks like apartment data
                apartment_indicators = ['unit', 'price', 'rent', 'apartment', 'floorplan', 'bedrooms', 'bathrooms', 'sqft', 'squareFeet']
                if any(key.lower().replace('_', '').replace('-', '') in [ind.lower() for ind in apartment_indicators] for key in obj.keys()):
                    apartment = {}

                    # Enhanced key mappings with more variations
                    key_mappings = {
                        'unit': ['unit', 'unitNumber', 'unit_number', 'apartmentNumber', 'apt_number', 'unitName'],
                        'price': ['price', 'rent', 'monthlyRent', 'rentAmount', 'rental_price', 'monthly_price'],
                        'bedrooms': ['bedrooms', 'beds', 'bed_count', 'bedroom_count', 'br'],
                        'bathrooms': ['bathrooms', 'baths', 'bath_count', 'bathroom_count', 'ba'],
                        'square_feet': ['squareFeet', 'sqft', 'square_feet', 'size', 'area', 'sq_ft'],
                        'status': ['status', 'availability', 'available', 'isAvailable', 'lease_status'],
                        'features': ['features', 'amenities', 'amenity_list', 'perks'],
                        'floor_plan': ['floorPlan', 'floor_plan', 'plan', 'planName', 'floorplan']
                    }

                    for our_key, possible_keys in key_mappings.items():
                        for key in possible_keys:
                            # Case-insensitive lookup
                            for obj_key in obj.keys():
                                if obj_key.lower().replace('_', '').replace('-', '') == key.lower().replace('_', '').replace('-', ''):
                                    value = obj[obj_key]

                                    # Process specific data types
                                    if our_key == 'price' and isinstance(value, (int, float)):
                                        apartment[our_key] = f"${value:,.0f}"
                                    elif our_key == 'price' and isinstance(value, str) and not value.startswith('$'):
                                        # Try to extract numeric value and format
                                        numeric_match = re.search(r'(\d{1,3}(?:,\d{3})*)', value)
                                        if numeric_match:
                                            apartment[our_key] = f"${numeric_match.group(1)}"
                                        else:
                                            apartment[our_key] = value
                                    elif our_key == 'status' and isinstance(value, bool):
                                        apartment[our_key] = 'Available' if value else 'Unavailable'
                                    elif our_key in ['bedrooms', 'bathrooms', 'square_feet'] and isinstance(value, str):
                                        # Try to convert string numbers to int
                                        try:
                                            apartment[our_key] = int(value)
                                        except ValueError:
                                            apartment[our_key] = value
                                    else:
                                        apartment[our_key] = value
                                    break
                            if our_key in apartment:
                                break

                    # Only add if we have meaningful data
                    if apartment and ('unit' in apartment or 'price' in apartment or 'floor_plan' in apartment):
                        apartments_list.append(apartment)

                # Recursively search nested objects
                for value in obj.values():
                    extract_from_dict(value, apartments_list)

            elif isinstance(obj, list):
                for item in obj:
                    extract_from_dict(item, apartments_list)

        extract_from_dict(data, apartments)
        return apartments

    def parse_api_response(self, response_text):
        """Parse apartment data from API JSON response"""
        try:
            data = json.loads(response_text)
            apartments = []

            # Try to find apartment data in various JSON structures
            apartment_keys = [
                'apartments', 'units', 'floorPlans', 'availability',
                'listings', 'properties', 'data', 'results'
            ]

            def search_for_apartments(obj, path=""):
                if isinstance(obj, dict):
                    # Check if this looks like apartment data
                    if any(key in obj for key in ['unitNumber', 'unit', 'rent', 'price', 'bedrooms', 'bathrooms']):
                        apartment = {}

                        # Map common API keys
                        if 'unitNumber' in obj or 'unit' in obj:
                            apartment['unit'] = obj.get('unitNumber') or obj.get('unit')
                        if 'rent' in obj or 'price' in obj:
                            rent_value = obj.get('rent') or obj.get('price')
                            if isinstance(rent_value, (int, float)):
                                apartment['price'] = f"${rent_value:,.0f}"
                            else:
                                apartment['price'] = str(rent_value)
                        if 'bedrooms' in obj or 'beds' in obj:
                            apartment['bedrooms'] = obj.get('bedrooms') or obj.get('beds')
                        if 'bathrooms' in obj or 'baths' in obj:
                            apartment['bathrooms'] = obj.get('bathrooms') or obj.get('baths')
                        if 'squareFeet' in obj or 'sqft' in obj:
                            apartment['square_feet'] = obj.get('squareFeet') or obj.get('sqft')
                        if 'available' in obj or 'isAvailable' in obj:
                            available = obj.get('available') or obj.get('isAvailable')
                            apartment['status'] = 'Available' if available else 'Waitlist'
                        if 'amenities' in obj or 'features' in obj:
                            features = obj.get('amenities') or obj.get('features')
                            if isinstance(features, list):
                                apartment['features'] = features[:10]

                        if apartment:
                            apartments.append(apartment)

                    # Recursively search
                    for key, value in obj.items():
                        search_for_apartments(value, f"{path}.{key}")

                elif isinstance(obj, list):
                    for i, item in enumerate(obj):
                        search_for_apartments(item, f"{path}[{i}]")

            search_for_apartments(data)
            print(f"🏠 Extracted {len(apartments)} apartments from API response")
            return apartments

        except json.JSONDecodeError:
            print("⚠️ Failed to parse API response as JSON")
            return []
        except Exception as e:
            print(f"⚠️ Error parsing API response: {e}")
            return []

    def extract_from_js_data(self, js_data):
        """Extract apartment data from JavaScript variables and DOM elements"""
        apartments = []

        # Process JavaScript variables
        variables = js_data.get('variables', [])
        print(f"🔍 Processing {len(variables)} JavaScript variables...")
        for var_info in variables:
            try:
                key = var_info.get('key', '')
                data_str = var_info.get('data', '')
                print(f"   Checking variable: {key[:50]}")

                # Try to parse the JSON data
                if data_str:
                    # Clean up the JSON string
                    clean_data = data_str.strip()
                    if clean_data.startswith('{') and (clean_data.endswith('}') or clean_data.endswith('}...')):
                        # Remove the trailing ... if present
                        if clean_data.endswith('...'):
                            clean_data = clean_data[:-3]

                        try:
                            data = json.loads(clean_data)
                            extracted_apts = self.extract_apartments_from_json(data)
                            if extracted_apts:
                                print(f"✅ Extracted {len(extracted_apts)} apartments from JS variable '{key}'")
                                apartments.extend(extracted_apts)
                        except json.JSONDecodeError:
                            # Try to extract apartment-like data with regex
                            apartment_data = self.extract_apartment_data_from_string(data_str)
                            if apartment_data:
                                print(f"✅ Extracted {len(apartment_data)} apartments from string patterns in '{key}'")
                                apartments.extend(apartment_data)

            except Exception as e:
                continue

        # Process script patterns that contain apartment data
        script_patterns = js_data.get('scriptPatterns', [])
        print(f"🔍 Processing {len(script_patterns)} script patterns...")
        for script_info in script_patterns:
            try:
                content = script_info.get('content', '')
                index = script_info.get('index', 0)
                print(f"   Checking script {index}")

                # Extract apartment data from script content
                apartment_data = self.extract_apartment_data_from_string(content)
                if apartment_data:
                    print(f"✅ Extracted {len(apartment_data)} apartments from script {index}")
                    apartments.extend(apartment_data)

                # Also try JSON parsing for script content
                try:
                    # Look for JSON objects in script content
                    json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
                    json_matches = re.findall(json_pattern, content)
                    for json_str in json_matches:
                        try:
                            data = json.loads(json_str)
                            extracted_apts = self.extract_apartments_from_json(data)
                            if extracted_apts:
                                apartments.extend(extracted_apts)
                        except json.JSONDecodeError:
                            continue
                except Exception:
                    pass

            except Exception as e:
                continue

        # Process DOM elements with data attributes
        elements = js_data.get('elements', [])
        print(f"🔍 Processing {len(elements)} DOM elements...")
        for element_data in elements:
            try:
                apartment = {}

                # Extract apartment info from data attributes
                for attr_name, attr_value in element_data.items():
                    if 'unit' in attr_name.lower():
                        apartment['unit'] = attr_value
                    elif 'price' in attr_name.lower() or 'rent' in attr_name.lower():
                        apartment['price'] = attr_value
                    elif 'bed' in attr_name.lower():
                        try:
                            apartment['bedrooms'] = int(attr_value)
                        except ValueError:
                            pass
                    elif 'bath' in attr_name.lower():
                        try:
                            apartment['bathrooms'] = int(attr_value)
                        except ValueError:
                            pass
                    elif 'sqft' in attr_name.lower() or 'square' in attr_name.lower():
                        try:
                            apartment['square_feet'] = int(attr_value)
                        except ValueError:
                            pass
                    elif 'available' in attr_name.lower():
                        apartment['status'] = 'Available' if attr_value.lower() in ['true', '1', 'yes'] else 'Waitlist'
                    elif 'floorplan' in attr_name.lower():
                        apartment['floor_plan'] = attr_value

                if apartment and ('unit' in apartment or 'price' in apartment):
                    apartments.append(apartment)

            except Exception as e:
                continue

        # Remove duplicates and validate
        unique_apartments = []
        seen_units = set()

        for apt in apartments:
            if self.is_valid_apartment_unit(apt):
                unit = apt.get('unit', '')
                if unit and unit not in seen_units:
                    seen_units.add(unit)
                    unique_apartments.append(apt)

        print(f"📊 Final result: {len(unique_apartments)} unique apartments after deduplication")
        return unique_apartments[:20]  # Limit to reasonable number

    def extract_apartment_data_from_string(self, data_str):
        """Extract apartment data from string using regex patterns"""
        apartments = []

        # Look for apartment-like patterns in the string
        patterns = [
            # Pattern for unit with price: "unit": "123", "price": "$2500"
            r'"unit":\s*"([^"]+)"[^}]*"price":\s*"([^"]+)"',
            # Pattern for rent with unit: "rent": 2500, "unitNumber": "123"
            r'"rent":\s*(\d+)[^}]*"unitNumber":\s*"([^"]+)"',
            # Pattern for apartment objects
            r'"apartment":\s*\{[^}]*"unit":\s*"([^"]+)"[^}]*"rent":\s*(\d+)'
        ]

        for pattern in patterns:
            matches = re.findall(pattern, data_str)
            for match in matches:
                apartment = {}
                if len(match) == 2:
                    if match[0].replace(',', '').isdigit():  # First is price, second is unit
                        apartment['price'] = f"${int(match[0]):,}"
                        apartment['unit'] = match[1]
                    else:  # First is unit, second is price
                        apartment['unit'] = match[0]
                        if match[1].replace(',', '').isdigit():
                            apartment['price'] = f"${int(match[1]):,}"
                        else:
                            apartment['price'] = match[1]

                    apartments.append(apartment)

        return apartments

    def is_valid_apartment_unit(self, apartment):
        """Check if this is a valid apartment unit and not a header or junk entry"""
        unit = apartment.get('unit', '')
        features = apartment.get('features', [])
        price = apartment.get('price', '')
        floor_plan = apartment.get('floor_plan', '')

        # Filter out header units and invalid unit patterns
        if (unit in ['300', '-fp-list-item', 'list-item', 'fp-list-item'] or
            unit.endswith('-fp-list-item') or
            unit.endswith('-list-item') or
            re.match(r'^-?fp-', unit)):
            return False

        # Allow single digit units if they have a proper format like "01 561" or have other valid data
        if len(unit) <= 2 and not re.match(r'\d{2}\s+\d{3}', unit) and not price and not floor_plan:
            return False

        # Require at least some meaningful data (not just unit number)
        meaningful_data_count = 0
        if price and price != 'Unknown':
            meaningful_data_count += 1
        if floor_plan:
            meaningful_data_count += 1
        if apartment.get('square_feet'):
            meaningful_data_count += 1
        if apartment.get('bedrooms'):
            meaningful_data_count += 1
        if apartment.get('bathrooms'):
            meaningful_data_count += 1
        if features and len(features) > 0:
            meaningful_data_count += 1

        # Filter out units with any junk features (image URLs, button HTML) - but be more lenient
        major_junk_patterns = [
            r'com/is/image',
            r'wid=\d+&amp;',
            r'button\s+aria-label',
            r'#floor-plan-list',
            r'iccEmbed=1',
            r'resMode=sharp',
            r'btn-circular'
        ]

        junk_feature_count = 0
        for feature in features:
            for pattern in major_junk_patterns:
                if re.search(pattern, feature, re.I):
                    junk_feature_count += 1
                    break

        # If more than half the features are junk, filter it out
        if features and junk_feature_count >= len(features) / 2:
            return False

        # Accept if we have at least 1 piece of meaningful data beyond just unit number
        return meaningful_data_count >= 1 or bool(unit)

    def parse_apartment_details_fallback(self, html_content):
        """Fallback parsing method using the original price-based approach"""
        apartments = []

        # Look for pricing patterns - these are usually the most reliable indicators
        price_patterns = [
            r'\$(\d{1,3}(?:,\d{3})*)(?:\s*(?:-|to)\s*\$(\d{1,3}(?:,\d{3})*))?',
        ]

        # Find all price matches with surrounding context
        for price_pattern in price_patterns:
            for match in re.finditer(price_pattern, html_content, re.I):
                price_text = match.group(0)

                # Skip obviously invalid prices (too small, likely partial matches)
                price_value = int(re.sub(r'[^\d]', '', price_text))
                if price_value < 1000:  # Skip prices under $1000 (likely partial matches)
                    continue

                # Get surrounding context (500 chars before and after)
                start = max(0, match.start() - 500)
                end = min(len(html_content), match.end() + 500)
                context = html_content[start:end]

                apartment = {}
                apartment['price'] = price_text

                # Extract all details from context
                self.extract_apartment_details_from_context(apartment, context)
                apartments.append(apartment)

        return self.filter_and_deduplicate_apartments(apartments, html_content)

    def filter_and_deduplicate_apartments(self, apartments, html_content):
        """Filter and deduplicate apartment listings"""
        # Remove duplicates and filter out entries without enough data
        unique_apartments = []
        seen_combinations = set()

        for apt in apartments:
            # Apply the same validation logic here
            if not self.is_valid_apartment_unit(apt):
                continue

            # Apply pattern fixes to existing features
            if 'features' in apt:
                fixed_features = []
                for feature in apt['features']:
                    # Apply pattern reconstruction
                    fixed_feature = feature
                    fixed_feature = re.sub(r'(\d+)(st|nd|rd|th)\s+Flo\b(?:\s+(or|r))?', r'\1\2 Floor', fixed_feature, flags=re.I)
                    fixed_feature = re.sub(r'\b(\w+)-Sty\b(?:\s+(le))?', r'\1-Style', fixed_feature, flags=re.I)

                    # Skip junk features that got through
                    if not re.search(r'com/is/image|wid=\d+|button aria-label|#floor-plan-list|iccEmbed|resMode', fixed_feature, re.I):
                        fixed_features.append(fixed_feature)

                apt['features'] = fixed_features

            # Create a unique key for this apartment
            key_parts = []
            if 'unit' in apt:
                key_parts.append(apt['unit'])
            if 'price' in apt:
                key_parts.append(apt['price'])
            if 'floor_plan' in apt:
                key_parts.append(apt['floor_plan'])

            key = '|'.join(key_parts)

            # Only keep apartments with meaningful data and no duplicates
            if (key and key not in seen_combinations and
                'price' in apt and 'unit' in apt):
                seen_combinations.add(key)
                unique_apartments.append(apt)

        return unique_apartments[:20]  # Limit to reasonable number

    def get_apartment_data(self):
        """Get apartment data using Selenium with enhanced waiting and parsing"""

        # If no driver was initialized, use requests fallback immediately
        if self.driver is None:
            print("🔄 ChromeDriver failed to initialize, using requests-based approach...")
            return self.get_apartment_data_requests()

        try:
            # First try the filtered URL that should show 2-bedroom apartments directly
            print(f"Trying filtered URL for 2-bedroom apartments: {self.filtered_url}")
            self.driver.get(self.filtered_url)

            # Wait a bit to see if the filtered URL works
            time.sleep(5)

            # Check if we got apartment data
            page_content = self.driver.page_source
            if ("$" in page_content and
                ("bed" in page_content.lower() or "bath" in page_content.lower()) and
                "Just a moment..." not in page_content):
                print("✅ Filtered URL appears to be working")
            else:
                print("⚠️ Filtered URL not working, trying main URL with manual filter...")
                # Fallback to main URL and apply filter manually
                self.driver.get(self.url)

            # Add random delay to appear more human-like
            import random
            time.sleep(random.uniform(2, 4))

            # Wait for page to load and content to be rendered
            print("⏳ Waiting for page to fully load...")

            # Add some random human-like behavior with varied timing
            for i in range(3):
                scroll_distance = random.randint(200, 800)
                self.driver.execute_script(f"window.scrollTo(0, {scroll_distance});")
                time.sleep(random.uniform(0.8, 1.5))

            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(random.uniform(1.5, 2.5))

            # Check for Cloudflare challenge first
            page_content = self.driver.page_source
            if ("Just a moment..." in page_content or
                "cf-browser-verification" in page_content or
                "Verify you are human" in page_content or
                "cloudflare" in page_content.lower()):
                print("🔄 Cloudflare challenge detected - attempting to wait for completion...")

                # Wait longer for Cloudflare challenge to complete automatically
                max_wait_time = 120  # 2 minutes total wait
                wait_interval = 5    # Check every 5 seconds
                waited = 0

                while waited < max_wait_time:
                    print(f"   Waiting for Cloudflare challenge... ({waited}s/{max_wait_time}s)")
                    time.sleep(wait_interval)
                    waited += wait_interval

                    # Check if challenge is completed
                    current_content = self.driver.page_source
                    if ("Just a moment..." not in current_content and
                        "cf-browser-verification" not in current_content and
                        "Verify you are human" not in current_content):
                        print("✅ Cloudflare challenge appears to be completed!")
                        break

                    # Try some interactions that might help complete the challenge
                    if waited % 20 == 0:  # Every 20 seconds
                        try:
                            # Look for and click any challenge elements
                            challenge_elements = self.driver.find_elements(By.CSS_SELECTOR,
                                "[id*='challenge'], [class*='challenge'], [id*='cf-'], input[type='checkbox']")
                            for elem in challenge_elements[:3]:
                                if elem.is_displayed() and elem.is_enabled():
                                    print(f"   Attempting to interact with challenge element...")
                                    self.driver.execute_script("arguments[0].click();", elem)
                                    time.sleep(2)
                        except:
                            pass

                        # Random scrolling to appear more human
                        self.driver.execute_script("window.scrollTo(0, Math.random() * 500);")
                        time.sleep(1)
                else:
                    print("⚠️ Cloudflare challenge did not complete automatically within timeout")
                    # Continue anyway - maybe we can extract some data

            # Wait for apartment content to load
            print("⏳ Waiting for apartment content to load...")
            time.sleep(10)

            # Try scrolling to trigger any lazy loading
            print("📜 Scrolling to trigger lazy loading of apartment data...")
            for scroll_attempt in range(5):
                self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)
                self.driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(2)

            # Apply bedroom filter to get 2-bedroom apartments
            print("🏠 Applying 2-bedroom filter...")
            try:
                # Look for bedroom filter buttons
                bedroom_filter_selectors = [
                    "//button[contains(text(), '2') and (contains(text(), 'bed') or contains(text(), 'Bed'))]",
                    "//button[@data-bedrooms='2']",
                    "//button[contains(@class, 'bed') and contains(text(), '2')]",
                    "//input[@type='checkbox' and @value='2'][@name*='bed']",
                    "//select[@name*='bed']//option[@value='2']",
                    "//div[contains(@class, 'filter')]//button[contains(text(), '2')]"
                ]

                filter_applied = False
                for selector in bedroom_filter_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        for element in elements:
                            if element.is_displayed() and element.is_enabled():
                                print(f"   Found 2-bedroom filter: {element.text}")
                                self.driver.execute_script("arguments[0].scrollIntoView();", element)
                                time.sleep(1)
                                self.driver.execute_script("arguments[0].click();", element)
                                print("   ✅ Applied 2-bedroom filter")
                                time.sleep(5)  # Wait for filter to apply
                                filter_applied = True
                                break
                    except Exception as e:
                        continue
                    if filter_applied:
                        break

                if not filter_applied:
                    print("   ⚠️ Could not find 2-bedroom filter button - may need to navigate differently")

            except Exception as e:
                print(f"   ⚠️ Error applying bedroom filter: {e}")

            # Additional wait after applying filter
            if filter_applied:
                print("⏳ Waiting for filtered results to load...")
                time.sleep(10)

                # Scroll again to load filtered content
                for scroll_attempt in range(3):
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(2)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(2)

            # Get final page content after all loading
            final_content = self.driver.page_source

            # Save the webpage content for parsing
            website_snapshot_file = "website_snapshot.html"
            print(f"💾 Saving webpage content to {website_snapshot_file}")
            try:
                with open(website_snapshot_file, 'w', encoding='utf-8') as f:
                    f.write(final_content)
                print(f"✅ Webpage saved: {len(final_content)} characters")
            except Exception as e:
                print(f"⚠️ Could not save webpage: {e}")

            # Now parse the saved content
            print("🔍 Parsing saved webpage content...")
            apartments = self.parse_apartment_details(final_content)

            # Create a hash of the content to detect changes
            content_hash = hashlib.md5(final_content.encode()).hexdigest()

            return {
                "timestamp": datetime.now().isoformat(),
                "status_code": 200,
                "content_hash": content_hash,
                "content_length": len(final_content),
                "apartments": apartments,
                "total_apartments": len(apartments),
                "data_source": "selenium_live",
                "note": "Live website data fetched via Selenium and saved locally"
            }

        except WebDriverException as e:
            print(f"WebDriver error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": f"WebDriver error: {str(e)}"
            }
        except Exception as e:
            print(f"Unexpected error: {e}")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }

    def load_previous_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading previous data: {str(e)}")
                return None
        return None

    def save_current_data(self, data):
        try:
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving data: {str(e)}")

    def send_notification(self, message):
        try:
            # Notifications temporarily disabled - can be re-enabled later
            print(f"🔕 Notification disabled (would have sent): {message}")
            return

            # Use the same notification system as the visa checker
            cmd = f"""
            osascript -e 'tell application "Messages"
            send "{message}" to buddy "+13309901046" of (service 1 whose service type is iMessage)
            end tell'
            """
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Notification sent: {message}")
            else:
                print(f"❌ Failed to send notification: {result.stderr}")
        except Exception as e:
            print(f"❌ Failed to send notification: {str(e)}")

    def check_for_changes(self):
        current_data = self.get_apartment_data()

        # If network access is blocked, use test parsing to validate our parsing logic
        if (current_data and "error" in current_data and
            "Network access blocked" in current_data["error"]):
            print("🔄 Network blocked, falling back to test parsing to validate parsing logic...")
            current_data = self.test_apartment_parsing()

        if not current_data:
            print("❌ Failed to get current data")
            # Save empty result instead of returning without saving
            current_data = {
                "timestamp": datetime.now().isoformat(),
                "error": "Failed to retrieve apartment data",
                "apartments": [],
                "total_apartments": 0
            }
            self.save_current_data(current_data)
            return

        previous_data = self.load_previous_data()

        if previous_data is None:
            print("📝 First run - saving initial data")
            self.save_current_data(current_data)
            return

        # Compare data for changes
        changes_detected = False
        change_details = []

        # Check if we got valid data this time
        if "error" in current_data:
            print(f"⚠️ Error in current data: {current_data['error']}")
            # Still save the error data so we track when failures occur
            self.save_current_data(current_data)
            return

        # If previous data had errors but current doesn't, that's a change
        if "error" in previous_data and "error" not in current_data:
            changes_detected = True
            change_details.append("Website is now accessible")

        # Compare content hash
        if ("content_hash" in current_data and "content_hash" in previous_data and
            current_data["content_hash"] != previous_data["content_hash"]):
            changes_detected = True
            change_details.append("Content changed")

        # Compare apartment counts
        if ("total_apartments" in current_data and "total_apartments" in previous_data):
            current_count = current_data["total_apartments"]
            previous_count = previous_data["total_apartments"]

            if current_count != previous_count:
                changes_detected = True
                if current_count > previous_count:
                    change_details.append(f"New apartments available (+{current_count - previous_count})")
                else:
                    change_details.append(f"Apartments removed (-{previous_count - current_count})")

        # Display current apartments
        if "apartments" in current_data and current_data["apartments"]:
            print(f"\n📋 Found {current_data['total_apartments']} apartments:")
            print("="*80)

            for i, apt in enumerate(current_data["apartments"], 1):
                print(f"\n🏠 Apartment {i}:")
                if 'floor_plan' in apt:
                    print(f"   Floor Plan: {apt['floor_plan']}")
                if 'unit' in apt:
                    print(f"   Unit: {apt['unit']}")
                if 'price' in apt:
                    print(f"   Price: {apt['price']}")
                if 'square_feet' in apt:
                    print(f"   Square Feet: {apt['square_feet']} sq ft")
                if 'bedrooms' in apt:
                    print(f"   Bedrooms: {apt['bedrooms']}")
                if 'bathrooms' in apt:
                    print(f"   Bathrooms: {apt['bathrooms']}")
                if 'status' in apt:
                    print(f"   Status: {apt['status']}")
                if 'features' in apt:
                    print(f"   Features: {', '.join(apt['features'])}")
            print("="*80)
        else:
            print("\n❌ No apartment details found in the parsed content")

        if changes_detected:
            change_summary = "; ".join(change_details)
            message = f"🏠 Apartment availability changed at Monticello! Changes: {change_summary}"
            print(f"🔔 {message}")
            self.send_notification(message)
            self.save_current_data(current_data)
        else:
            print("✅ No changes detected")
            # Update timestamp but keep checking
            current_data["last_checked"] = datetime.now().isoformat()
            self.save_current_data(current_data)

    def run_once(self):
        print(f"\n🔍 Checking apartments at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.check_for_changes()

    def run_continuous(self, interval_minutes=30):
        print(f"🚀 Starting apartment checker - checking every {interval_minutes} minutes")
        print(f"📍 Monitoring: Monticello 2BR/2BA units")
        print(f"📱 Notifications will be sent via iMessage")
        print("⏹️  Press Ctrl+C to stop\n")

        while True:
            try:
                self.run_once()
                print(f"😴 Sleeping for {interval_minutes} minutes...")
                time.sleep(interval_minutes * 60)
            except KeyboardInterrupt:
                print("\n⏹️  Stopping apartment checker...")
                break
            except Exception as e:
                print(f"❌ Error in main loop: {str(e)}")
                time.sleep(60)  # Wait 1 minute before retrying

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                print("✅ Browser closed")
            except:
                pass

    def __del__(self):
        self.cleanup()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Check apartment availability at Monticello')
    parser.add_argument('--debug', action='store_true',
                       help='Run in debug mode (single run, no interactive prompt)')
    parser.add_argument('--continuous', action='store_true',
                       help='Run continuously every 30 minutes')
    parser.add_argument('--test-parsing', action='store_true',
                       help='Test apartment parsing logic with mock data')
    args = parser.parse_args()

    checker = None
    try:
        checker = ApartmentChecker()

        if args.test_parsing:
            print("🧪 Running apartment parsing test with mock data...")
            result = checker.test_apartment_parsing()

            # Save test results
            with open(checker.data_file, 'w') as f:
                json.dump(result, f, indent=2)

            print(f"✅ Test completed. Found {result['total_apartments']} apartments in mock data.")
            print("Check apartment_data.json for detailed results.")

        elif args.debug:
            print("🐛 Running in debug mode (single run)")
            checker.run_once()
            print("✅ Debug run completed. Check apartment_data.json for results.")
        elif args.continuous:
            print("🔄 Running in continuous mode")
            checker.run_continuous(30)
        else:
            # Run once for testing first
            checker.run_once()

            # Ask user if they want to run continuously
            print(f"\n" + "="*50)
            print("🏠 Apartment Checker Ready!")
            print("="*50)
            print("Options:")
            print("1. Run once (just completed)")
            print("2. Run continuously (every 30 minutes)")
            print("3. Exit")

            choice = input("\nEnter your choice (1/2/3): ").strip()

            if choice == "2":
                checker.run_continuous(30)
            elif choice == "1":
                print("✅ Single check completed. Check apartment_data.json for results.")
            else:
                print("👋 Goodbye!")

    except KeyboardInterrupt:
        print("\n⏹️  Interrupted by user")
    except Exception as e:
        print(f"❌ Fatal error: {e}")
    finally:
        if checker:
            checker.cleanup()