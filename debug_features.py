#!/usr/bin/env python3

import re

def debug_feature_extraction():
    """Debug the feature extraction to see what's happening"""

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

    # Extract the amenities section
    amenities_match = re.search(r'<div class="fapt-fp-unit__column--amenities"[^>]*>.*?<div class="fapt-fp-unit__column-inner--amenities"[^>]*><div>(.*?)</div>', sample_html, re.DOTALL | re.I)
    if amenities_match:
        amenities_html = amenities_match.group(1)
        print("Amenities HTML:")
        print(repr(amenities_html))
        print()

        # Test different regex patterns
        print("Testing pattern 1: <span(?![^>]*disclaimer)[^>]*>([^<]+)(?:<span[^>]*>.*?</span>)?</span>")
        feature_span_pattern = r'<span(?![^>]*disclaimer)[^>]*>([^<]+)(?:<span[^>]*>.*?</span>)?</span>'
        feature_matches = re.findall(feature_span_pattern, amenities_html, re.DOTALL | re.I)
        print(f"Pattern 1 matches: {feature_matches}")
        print()

        print("Testing pattern 2: <span(?![^>]*disclaimer)[^>]*>(.*?)</span>")
        outer_span_pattern = r'<span(?![^>]*disclaimer)[^>]*>(.*?)</span>'
        all_span_matches = re.findall(outer_span_pattern, amenities_html, re.DOTALL | re.I)
        print(f"Pattern 2 matches: {all_span_matches}")
        print()

        # Let's clean up each one and see what we get
        print("Processing Pattern 2 matches:")
        for i, span_content in enumerate(all_span_matches):
            print(f"  Match {i+1}: {repr(span_content)}")
            # Remove any nested spans and HTML tags
            clean_text = re.sub(r'<[^>]*>', '', span_content)
            clean_text = re.sub(r'&amp;', '&', clean_text)
            clean_text = re.sub(r'&lt;', '<', clean_text)
            clean_text = re.sub(r'&gt;', '>', clean_text)
            clean_text = clean_text.strip()
            print(f"    Clean: {repr(clean_text)}")

            # Check if this should be included
            should_include = (len(clean_text) > 2 and
                clean_text not in [', ', ' ', ','] and
                not re.match(r'^[\s,.-]*$', clean_text) and
                not re.search(r'com/is/image|wid=\d+|button aria-label|Mandatory Fee', clean_text, re.I))
            print(f"    Include: {should_include}")
            print()

if __name__ == "__main__":
    debug_feature_extraction()