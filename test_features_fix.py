#!/usr/bin/env python3

import re

def test_feature_extraction():
    """Test the feature extraction logic with the actual HTML structure"""

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
    # Based on actual HTML: features are in multiple spans like: <span>5th Floor<span>, </span></span><span>No Neighbors Above<span>, </span></span>
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
        # Pattern: <span>Feature Name<span>, </span></span><span>Next Feature<span>, </span></span>
        # Extract each main feature span (excluding nested spans with commas and disclaimer spans)
        feature_span_pattern = r'<span(?![^>]*disclaimer)[^>]*>([^<]+)(?:<span[^>]*>.*?</span>)?</span>'
        feature_matches = re.findall(feature_span_pattern, amenities_html, re.DOTALL | re.I)

        for feature_text in feature_matches:
            # Clean up the feature text
            clean_feature = re.sub(r'&amp;', '&', feature_text.strip())
            clean_feature = re.sub(r'&lt;', '<', clean_feature)
            clean_feature = re.sub(r'&gt;', '>', clean_feature)
            clean_feature = clean_feature.strip()

            # Skip empty, short, or junk content
            if (len(clean_feature) > 2 and
                clean_feature not in [', ', ' ', ''] and
                not re.match(r'^[\s,.-]*$', clean_feature) and
                not clean_feature.lower() in ['and', 'or', 'with', 'the'] and
                not re.match(r'^\d+$', clean_feature) and
                not re.search(r'com/is/image|wid=\d+|button aria-label|Mandatory Fee', clean_feature, re.I)):
                features.append(clean_feature)

        # If the span-based approach didn't work, fall back to the original approach
        if len(features) < 2:
            features = []

            # Try to find all outer spans and extract their immediate text content
            outer_span_pattern = r'<span(?![^>]*disclaimer)[^>]*>(.*?)</span>'
            all_span_matches = re.findall(outer_span_pattern, amenities_html, re.DOTALL | re.I)

            feature_candidates = []
            for span_content in all_span_matches:
                # Remove any nested spans and HTML tags
                clean_text = re.sub(r'<[^>]*>', '', span_content)
                clean_text = re.sub(r'&amp;', '&', clean_text)
                clean_text = re.sub(r'&lt;', '<', clean_text)
                clean_text = re.sub(r'&gt;', '>', clean_text)
                clean_text = clean_text.strip()

                # Skip obvious separators and junk
                if (len(clean_text) > 2 and
                    clean_text not in [', ', ' ', ','] and
                    not re.match(r'^[\s,.-]*$', clean_text) and
                    not re.search(r'com/is/image|wid=\d+|button aria-label|Mandatory Fee', clean_text, re.I)):
                    feature_candidates.append(clean_text)

            # Reconstruct features by looking for meaningful content
            combined_text = ' '.join(feature_candidates)

            # Try to split on common patterns
            if len(combined_text) > 10:
                # Look for comma-separated patterns or natural break points
                feature_items = re.split(r'(?:,\s*|\s{2,})', combined_text)
                for item in feature_items:
                    item = item.strip()
                    if (len(item) > 3 and
                        not re.match(r'^[\s,.-]*$', item) and
                        not item.lower() in ['and', 'or', 'with', 'the'] and
                        not re.match(r'^\d+$', item)):
                        features.append(item)

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
    print("Testing feature extraction with sample HTML...")

    features = test_feature_extraction()

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