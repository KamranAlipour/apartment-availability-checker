#!/usr/bin/env python3

import re

def test_fixed_feature_extraction():
    """Test the fixed feature extraction logic with the actual HTML structure"""

    # Sample HTML structure from the actual website for unit "01 561"
    sample_html = '''
    <div class="fapt-fp-unit__column fapt-fp-unit__column--amenities"><div class="fapt-fp-unit__column-inner fapt-fp-unit__column-inner--amenities"><div><span>
                        5th Floor<span>, </span></span><span>
                        No Neighbors Above<span>, </span></span><span>
                        Stainless Steel Appliances<span>, </span></span><span>
                        Walk-in Closet<span>, </span></span><span>
                        Washer &amp; Dryer In Home<!----></span> <span class="fapt-fp-unit__disclaimer">
                            Mandatory Fee: utility billing fee ($5.55/month, Conservice), and utilities (monthly, cost varies).
                        </span></div></div></div>
    '''

    # Extract amenities/features using the correct HTML structure
    amenities_patterns = [
        r'<div class="fapt-fp-unit__column--amenities"[^>]*>.*?<div class="fapt-fp-unit__column-inner--amenities"[^>]*><div>(.*?)</div>',
        r'<div[^>]*amenities[^>]*>(.*?)</div>',
        r'<div[^>]*features[^>]*>(.*?)</div>',
        r'<div[^>]*column-inner--amenities[^>]*>(.*?)</div>'
    ]

    amenities_match = None
    for pattern in amenities_patterns:
        amenities_match = re.search(pattern, sample_html, re.DOTALL | re.I)
        if amenities_match:
            break

    if amenities_match:
        amenities_html = amenities_match.group(1)
        features = []

        # NEW APPROACH: Parse the specific structure where each feature is in its own span
        # Extract all span content and filter out disclaimer spans and junk
        outer_span_pattern = r'<span[^>]*>(.*?)</span>'
        all_span_matches = re.findall(outer_span_pattern, amenities_html, re.DOTALL | re.I)

        for span_content in all_span_matches:
            # Remove any nested spans and HTML tags
            clean_text = re.sub(r'<[^>]*>', '', span_content)
            clean_text = re.sub(r'&amp;', '&', clean_text)
            clean_text = re.sub(r'&lt;', '<', clean_text)
            clean_text = re.sub(r'&gt;', '>', clean_text)
            clean_text = clean_text.strip()

            # Remove trailing commas and whitespace
            clean_text = re.sub(r'[,\s]+$', '', clean_text)
            clean_text = clean_text.strip()

            # Skip obvious separators, disclaimers, and junk
            if (len(clean_text) > 2 and
                clean_text not in [', ', ' ', ',', ''] and
                not re.match(r'^[\s,.-]*$', clean_text) and
                not clean_text.lower() in ['and', 'or', 'with', 'the'] and
                not re.match(r'^\d+$', clean_text) and
                not re.search(r'com/is/image|wid=\d+|button aria-label|Mandatory Fee|utility billing fee', clean_text, re.I)):
                features.append(clean_text)

        # Remove duplicates while preserving order
        if features:
            seen = set()
            unique_features = []
            for feature in features:
                feature_lower = feature.lower().strip()
                if feature_lower not in seen and len(feature_lower) > 2:
                    seen.add(feature_lower)
                    unique_features.append(feature)
            features = unique_features[:10]  # Limit to reasonable number

        return features

    return []

if __name__ == "__main__":
    print("Testing FIXED feature extraction with sample HTML...")

    features = test_fixed_feature_extraction()

    print(f"\nExtracted {len(features)} features:")
    for i, feature in enumerate(features, 1):
        print(f"{i}. {feature}")

    expected_features = [
        "5th Floor",
        "No Neighbors Above",
        "Stainless Steel Appliances",
        "Walk-in Closet",
        "Washer & Dryer In Home"
    ]

    print(f"\nExpected {len(expected_features)} features:")
    for i, feature in enumerate(expected_features, 1):
        print(f"{i}. {feature}")

    # Check if we got all expected features
    success = len(features) == len(expected_features)
    for expected in expected_features:
        if expected not in features:
            success = False
            break

    if success:
        print("\n✅ SUCCESS: All expected features extracted correctly!")
    else:
        print(f"\n❌ FAILURE: Expected {expected_features}, got {features}")