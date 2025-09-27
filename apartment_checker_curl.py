#!/usr/bin/env python3

import time
import json
import os
from datetime import datetime
import hashlib
import subprocess
import re

class ApartmentChecker:
    def __init__(self):
        self.url = "https://www.irvinecompanyapartments.com/locations/northern-california/santa-clara/monticello/availability.html?beds=2&baths=2#floor-plan-list"
        self.data_file = "apartment_data.json"

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
                # Get surrounding context (500 chars before and after)
                start = max(0, match.start() - 500)
                end = min(len(html_content), match.end() + 500)
                context = html_content[start:end]

                apartment = {}
                apartment['price'] = match.group(0)

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

                # Extract unit number from context
                unit_patterns = [
                    r'(?:unit|apt\.?|#)\s*([A-Z0-9\-]+)',
                    r'([A-Z]\d+[A-Z]?)',  # Pattern like A101, B205A
                    r'(\d{3,4}[A-Z]?)'   # Pattern like 1201, 205A
                ]
                for unit_pattern in unit_patterns:
                    unit_match = re.search(unit_pattern, context, re.I)
                    if unit_match:
                        apartment['unit'] = unit_match.group(1)
                        break

                # Extract availability status from context
                if re.search(r'available|ready', context, re.I):
                    apartment['status'] = 'Available'
                elif re.search(r'waitlist', context, re.I):
                    apartment['status'] = 'Waitlist'
                else:
                    apartment['status'] = 'Unknown'

                # Extract features from context
                features = []
                feature_keywords = ['balcony', 'patio', 'garage', 'parking', 'pool', 'gym', 'fitness',
                                  'washer', 'dryer', 'dishwasher', 'ac', 'air conditioning', 'fireplace',
                                  'hardwood', 'carpet', 'tile', 'granite', 'stainless', 'pet friendly',
                                  'in-unit', 'walk-in closet', 'view']

                for keyword in feature_keywords:
                    if re.search(keyword, context, re.I):
                        features.append(keyword.title())

                if features:
                    apartment['features'] = list(set(features))  # Remove duplicates

                apartments.append(apartment)

        # Remove duplicates and filter out entries without enough data
        unique_apartments = []
        seen_prices = set()

        for apt in apartments:
            # Only keep apartments with meaningful data
            if 'price' in apt and apt['price'] not in seen_prices:
                seen_prices.add(apt['price'])
                unique_apartments.append(apt)

        return unique_apartments[:20]  # Limit to reasonable number

    def get_apartment_data(self):
        """Get apartment data using curl with browser-like headers"""
        try:
            print(f"Fetching data from: {self.url}")

            # Use curl with realistic browser headers (inspired by prenotami approach)
            curl_command = [
                'curl', '-s',
                '--noproxy', '*',  # Bypass proxy
                '-H', 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                '-H', 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                '-H', 'Accept-Language: en-US,en;q=0.9',
                '-H', 'Accept-Encoding: gzip, deflate, br',
                '-H', 'DNT: 1',
                '-H', 'Connection: keep-alive',
                '-H', 'Upgrade-Insecure-Requests: 1',
                '-H', 'Sec-Fetch-Dest: document',
                '-H', 'Sec-Fetch-Mode: navigate',
                '-H', 'Sec-Fetch-Site: none',
                '-H', 'Sec-Fetch-User: ?1',
                '-H', 'Cache-Control: max-age=0',
                '--compressed',
                '--connect-timeout', '30',
                '--max-time', '60',
                '--insecure',  # Ignore SSL issues
                self.url
            ]

            # Add a small delay to avoid being flagged as a bot
            time.sleep(2)

            result = subprocess.run(curl_command, capture_output=True, text=True, timeout=90)

            if result.returncode == 0:
                content = result.stdout

                if len(content) < 1000:
                    print(f"⚠️ Received very short response ({len(content)} chars), might be blocked")

                # Parse apartment details from HTML
                apartments = self.parse_apartment_details(content)

                # Create a hash of the content to detect changes
                content_hash = hashlib.md5(content.encode()).hexdigest()

                return {
                    "timestamp": datetime.now().isoformat(),
                    "status_code": 200,  # Assume success if curl succeeded
                    "content_hash": content_hash,
                    "content_length": len(content),
                    "apartments": apartments,
                    "total_apartments": len(apartments),
                    "content_preview": content[:1000] + "..." if len(content) > 1000 else content
                }
            else:
                print(f"Curl error: {result.stderr}")
                return {
                    "timestamp": datetime.now().isoformat(),
                    "error": f"Curl error: {result.stderr}"
                }

        except subprocess.TimeoutExpired:
            print("Request timeout")
            return {
                "timestamp": datetime.now().isoformat(),
                "error": "Request timeout"
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
        if not current_data:
            print("❌ Failed to get current data")
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

if __name__ == "__main__":
    try:
        checker = ApartmentChecker()

        # Run once for testing
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