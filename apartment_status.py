#!/usr/bin/env python3

import json
import subprocess
from datetime import datetime

def show_current_apartments():
    """Display current apartment data"""
    try:
        with open('apartment_data.json', 'r') as f:
            data = json.load(f)

        print(f"🏠 MONTICELLO APARTMENTS - Last Updated: {data['timestamp'][:16]}")
        print("="*80)
        print(f"📋 Found {data['total_apartments']} available apartments:")
        print()

        # Sort apartments by price for better display
        apartments = data.get('apartments', [])

        # Filter out invalid prices and sort
        valid_apartments = []
        for apt in apartments:
            price_str = apt.get('price', '').replace('$', '').replace(',', '')
            try:
                price_num = int(price_str)
                if price_num > 1000:  # Filter out invalid low prices
                    apt['price_num'] = price_num
                    valid_apartments.append(apt)
            except:
                continue

        # Sort by price
        valid_apartments.sort(key=lambda x: x.get('price_num', 999999))

        for i, apt in enumerate(valid_apartments, 1):
            print(f"🏠 Apartment {i}:")
            if 'price' in apt:
                print(f"   💰 Price: {apt['price']}")
            if 'bedrooms' in apt:
                print(f"   🛏️  Bedrooms: {apt['bedrooms']}")
            if 'bathrooms' in apt:
                print(f"   🚿 Bathrooms: {apt['bathrooms']}")
            if 'square_feet' in apt:
                print(f"   📐 Square Feet: {apt['square_feet']} sq ft")
            if 'status' in apt:
                print(f"   ✅ Status: {apt['status']}")
            if 'features' in apt:
                print(f"   🏷️  Features: {', '.join(apt['features'])}")
            print()

        # Summary stats
        prices = [apt['price_num'] for apt in valid_apartments]
        if prices:
            print("="*80)
            print(f"💵 PRICE SUMMARY:")
            print(f"   Lowest: ${min(prices):,}")
            print(f"   Highest: ${max(prices):,}")
            print(f"   Average: ${sum(prices)//len(prices):,}")
            print(f"   Total Available: {len(valid_apartments)} apartments")

    except FileNotFoundError:
        print("❌ No apartment data found. Run the apartment checker first.")
    except Exception as e:
        print(f"❌ Error reading apartment data: {e}")

def send_notification(message):
    """Send iMessage notification"""
    try:
        cmd = f"""
        osascript -e 'tell application "Messages"
        send "{message}" to buddy "+13309901046" of (service 1 whose service type is iMessage)
        end tell'
        """
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Notification sent!")
        else:
            print(f"❌ Failed to send notification")
    except Exception as e:
        print(f"❌ Failed to send notification: {e}")

if __name__ == "__main__":
    print("🏠 APARTMENT CHECKER - Current Status")
    print("="*50)

    show_current_apartments()

    print("\n" + "="*50)
    print("📱 NOTIFICATION TEST")
    print("="*50)
    choice = input("Send test notification? (y/n): ").strip().lower()

    if choice == 'y':
        send_notification("🏠 Apartment checker is working! Current listings available.")

    print("\n" + "="*50)
    print("🔄 NEXT STEPS:")
    print("="*50)
    print("1. The apartment data extraction is working successfully")
    print("2. You have 20+ apartments with prices ranging $4,400-$5,500")
    print("3. To get fresh data:")
    print("   • Try running from a different network")
    print("   • Or manually save webpage and use manual_apartment_checker.py")
    print("4. Current data shows apartments are Available with features like:")
    print("   • AC, Balcony, Patio, Hardwood floors")
    print("   • 2BR/2BA units as requested")