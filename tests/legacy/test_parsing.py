#!/usr/bin/env python3
"""
Test script for the enhanced airline schedule parsing logic
"""

from schedule_parser import parse_schedule

# Sample text compatible with new parser format
sample_united_text = """PILOT MONTHLY BID PACKAGE - NOVEMBER 2024
105 4-Day Trip Credit: 18.30
201 3-Day Trip Credit: 14.45
308 2-Day Trip Credit: 8.15
412 5-Day Trip Credit: 22.30
"""


def test_parsing():
    print("Testing enhanced airline schedule parsing...")

    # Test with the new unified parser
    print("\nFull parsing result:")
    trips = parse_schedule(sample_united_text.encode("utf-8"), "sample.txt")

    print(f"Found {len(trips)} trips:")
    for i, trip in enumerate(trips, 1):
        print(f"{i}. Trip {trip['id']}: {trip['days']} days, Credit: {trip['credit']}")
        if "raw" in trip:
            print(f"   Raw: {trip['raw']}")

    return trips


if __name__ == "__main__":
    test_parsing()
