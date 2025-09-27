#!/usr/bin/env python3

import json
import re
import os
from datetime import datetime
import hashlib

class ManualApartmentChecker:
    def __init__(self):
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

    def parse_html_file(self, html_file_path):
        """Parse a saved HTML file"""
        try:
            with open(html_file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            print(f"📄 Parsing HTML file: {html_file_path}")
            print(f"📏 File size: {len(content)} characters")

            # Parse apartment details
            apartments = self.parse_apartment_details(content)

            # Create data structure
            data = {
                "timestamp": datetime.now().isoformat(),
                "source": html_file_path,
                "status_code": 200,
                "content_hash": hashlib.md5(content.encode()).hexdigest(),
                "content_length": len(content),
                "apartments": apartments,
                "total_apartments": len(apartments),
                "content_preview": content[:1000] + "..." if len(content) > 1000 else content
            }

            # Save data
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2)

            return data

        except FileNotFoundError:
            print(f"❌ File not found: {html_file_path}")
            return None
        except Exception as e:
            print(f"❌ Error parsing file: {e}")
            return None

    def display_apartments(self, data):
        """Display apartment information"""
        if not data or "apartments" not in data:
            print("❌ No apartment data to display")
            return

        print(f"\n📋 Found {data['total_apartments']} apartments:")
        print("="*80)

        for i, apt in enumerate(data["apartments"], 1):
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

if __name__ == "__main__":
    checker = ManualApartmentChecker()

    print("🏠 Manual Apartment Checker")
    print("="*50)
    print("This tool can parse apartment data from saved HTML files.")
    print("To use:")
    print("1. Save the apartment webpage as an HTML file")
    print("2. Run: python manual_apartment_checker.py <filename.html>")
    print("3. Or place 'apartments.html' in this directory")
    print("="*50)

    # Check for HTML files
    html_files = [f for f in os.listdir('.') if f.endswith('.html')]

    if html_files:
        print(f"\n📁 Found HTML files: {', '.join(html_files)}")
        file_to_parse = html_files[0]  # Use first HTML file found

        data = checker.parse_html_file(file_to_parse)
        if data:
            checker.display_apartments(data)
            print(f"\n✅ Data saved to {checker.data_file}")
    else:
        print("\n📝 Instructions:")
        print("1. Go to the apartment website in your browser")
        print("2. Right-click -> 'Save Page As' -> save as 'apartments.html'")
        print("3. Run this script again")
        print("4. The parser will extract all apartment details automatically")