#!/usr/bin/env python3

import json
import re
from datetime import datetime

class ApartmentParser:
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

    def test_with_existing_data(self):
        """Test the parser with existing apartment data"""
        try:
            with open(self.data_file, 'r') as f:
                data = json.load(f)

            if 'content_preview' in data:
                print("🔍 Testing apartment parser with existing HTML content...")
                print("="*80)

                # Parse the content preview (limited data)
                apartments = self.parse_apartment_details(data['content_preview'])

                if apartments:
                    print(f"📋 Found {len(apartments)} apartments from content preview:")
                    print("="*80)

                    for i, apt in enumerate(apartments, 1):
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
                    print("❌ No apartment details found in the content preview")
                    print("   This is expected since content preview is limited to first 1000 chars")
                    print("   The full parser would work better with complete HTML content")

            else:
                print("❌ No content preview found in existing data")

        except FileNotFoundError:
            print("❌ No existing apartment data file found")
        except Exception as e:
            print(f"❌ Error reading data: {e}")


if __name__ == "__main__":
    parser = ApartmentParser()
    parser.test_with_existing_data()

    print("\n" + "="*80)
    print("✅ PARSER FUNCTIONALITY:")
    print("="*80)
    print("The updated apartment checker now includes:")
    print("• Price extraction (e.g., $2,500, $2,800-$3,200)")
    print("• Square footage parsing (e.g., 1,200 sq ft)")
    print("• Bedroom/bathroom counts (e.g., 2 bed, 2 bath)")
    print("• Unit numbers/identifiers")
    print("• Availability status (Available/Waitlist)")
    print("• Feature detection (balcony, garage, etc.)")
    print("• Duplicate removal and data validation")
    print("• Formatted output display")
    print("="*80)