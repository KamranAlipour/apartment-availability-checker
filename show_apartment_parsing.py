#!/usr/bin/env python3

import json
import re
from datetime import datetime

def parse_apartment_details_from_data():
    """Parse the existing apartment data to show how the parser works"""

    # Load the existing data
    try:
        with open('apartment_data.json', 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("❌ No apartment_data.json found")
        return

    print("🔍 Parsing existing apartment data...")
    print("="*80)

    if 'content_preview' in data:
        content = data['content_preview']
        print(f"📄 Content length: {len(content)} characters")

        # Look for pricing patterns
        price_matches = re.findall(r'\$[\d,]+', content)
        print(f"💰 Found {len(price_matches)} price references: {price_matches[:5]}")

        # Look for square footage
        sqft_matches = re.findall(r'(\d{3,4})\s*(?:sq\.?\s*ft\.?|square\s*feet)', content, re.I)
        print(f"📐 Found {len(sqft_matches)} square footage references: {sqft_matches[:5]}")

        # Look for bed/bath info
        bed_matches = re.findall(r'(\d+)\s*(?:bed|br)', content, re.I)
        bath_matches = re.findall(r'(\d+)\s*(?:bath|ba)', content, re.I)
        print(f"🛏️ Found {len(bed_matches)} bedroom references: {bed_matches[:5]}")
        print(f"🚿 Found {len(bath_matches)} bathroom references: {bath_matches[:5]}")

        # Show content sample
        print(f"\n📋 Content sample:")
        print("-" * 50)
        print(content[:500] + "..." if len(content) > 500 else content)
        print("-" * 50)

    else:
        print("❌ No content preview in data file")

    print("\n✅ NEXT STEPS:")
    print("="*80)
    print("1. The apartment checker is set up and ready")
    print("2. It will parse full HTML content when it successfully fetches from website")
    print("3. Currently blocked by network proxy - you may need to:")
    print("   • Run from a different network")
    print("   • Configure proxy settings")
    print("   • Use selenium with Chrome (if permissions allow)")
    print("4. When working, it will show apartment details like:")
    print("   🏠 Apartment 1:")
    print("      Price: $2,850")
    print("      Square Feet: 1,240 sq ft")
    print("      Bedrooms: 2")
    print("      Bathrooms: 2")
    print("      Status: Available")
    print("      Features: Balcony, Garage, Pool")

if __name__ == "__main__":
    parse_apartment_details_from_data()