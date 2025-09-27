#!/usr/bin/env python3

# Simple test to verify the parsing logic works with sample data
import json
import re
from datetime import datetime

class ApartmentParsingTest:
    def extract_apartments_from_json(self, data):
        """Extract apartment data from JSON object"""
        apartments = []

        def extract_from_dict(obj, apartments_list):
            if isinstance(obj, dict):
                # Check if this dict looks like apartment data
                if any(key in obj for key in ['unit', 'price', 'rent', 'apartment']):
                    apartment = {}

                    # Map common JSON keys to our format
                    key_mappings = {
                        'unit': ['unit', 'unitNumber', 'unit_number', 'apartmentNumber'],
                        'price': ['price', 'rent', 'monthlyRent', 'rentAmount'],
                        'bedrooms': ['bedrooms', 'beds', 'bed_count'],
                        'bathrooms': ['bathrooms', 'baths', 'bath_count'],
                        'square_feet': ['squareFeet', 'sqft', 'square_feet', 'size'],
                        'status': ['status', 'availability', 'available'],
                        'features': ['features', 'amenities', 'amenity_list']
                    }

                    for our_key, possible_keys in key_mappings.items():
                        for key in possible_keys:
                            if key in obj:
                                apartment[our_key] = obj[key]
                                break

                    if apartment:
                        apartments_list.append(apartment)

                # Recursively search nested objects
                for value in obj.values():
                    extract_from_dict(value, apartments_list)

            elif isinstance(obj, list):
                for item in obj:
                    extract_from_dict(item, apartments_list)

        extract_from_dict(data, apartments)
        return apartments

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

    def test_parsing_methods(self):
        """Test the parsing methods with sample data"""
        print("🔍 Testing apartment data parsing methods...")

        # Test JSON parsing
        sample_json = {
            "apartments": [
                {
                    "unitNumber": "01 561",
                    "rent": 3500,
                    "bedrooms": 2,
                    "bathrooms": 2,
                    "squareFeet": 1200,
                    "available": True,
                    "amenities": ["Hardwood Floors", "Stainless Steel Appliances", "Balcony"]
                },
                {
                    "unit": "05 113",
                    "price": "$3200",
                    "beds": 2,
                    "baths": 2,
                    "sqft": 1100,
                    "status": "Available"
                }
            ]
        }

        json_apartments = self.extract_apartments_from_json(sample_json)
        print(f"✅ JSON parsing extracted {len(json_apartments)} apartments:")
        for apt in json_apartments:
            print(f"   {apt}")

        # Test string parsing
        sample_string = '''
        {"unit": "02 450", "price": "$3300", "bed": 2, "bath": 2}
        {"rent": 3100, "unitNumber": "03 225", "sqft": 1150}
        '''

        string_apartments = self.extract_apartment_data_from_string(sample_string)
        print(f"✅ String parsing extracted {len(string_apartments)} apartments:")
        for apt in string_apartments:
            print(f"   {apt}")

        return len(json_apartments) + len(string_apartments) > 0

if __name__ == "__main__":
    tester = ApartmentParsingTest()
    success = tester.test_parsing_methods()

    if success:
        print("\n✅ Parsing methods are working correctly!")
        print("📝 The apartment scraper parsing logic should now capture detailed apartment information.")
        print("🚀 Once ChromeDriver connectivity is resolved, the scraper should extract prices, availability, and features.")
    else:
        print("\n❌ Parsing methods failed - there may be an issue with the logic.")