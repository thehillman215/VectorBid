#!/usr/bin/env python3
"""
Test script for the enhanced airline schedule parsing logic
"""

from schedule_parser import parse_airline_schedule_text

# Sample United Airlines bid package text
sample_united_text = """
PILOT MONTHLY BID PACKAGE - NOVEMBER 2024

Trip 105
4-Day Trip
12NOV - 15NOV  
IAH-SFO-IAH
18:30

Trip 201  
3-Day Trip
16NOV - 18NOV
IAH-LAX-DEN-IAH  
14:45

Trip 308
2-Day Trip  
19NOV - 20NOV
IAH-ORD-IAH
8:15

Trip 412
5-Day Trip
21NOV - 25NOV
IAH-SFO-SEA-LAX-IAH
22:30
"""

def test_parsing():
    print("Testing enhanced airline schedule parsing...")
    
    # Test the block extraction first
    from schedule_parser import extract_trip_blocks, parse_trip_block
    blocks = extract_trip_blocks(sample_united_text)
    print(f"Found {len(blocks)} trip blocks")
    
    # Test direct block parsing
    parsed_trips = []
    for i, block in enumerate(blocks, 1):
        trip = parse_trip_block(block)
        if trip and trip.get('id'):
            parsed_trips.append(trip)
            print(f"Block {i} -> Trip {trip['id']}: {trip['routing']}")
    
    print(f"\nDirect block parsing found {len(parsed_trips)} trips")
    
    print("\nFull parsing result:")
    trips = parse_airline_schedule_text(sample_united_text)
    
    print(f"Found {len(trips)} trips:")
    for i, trip in enumerate(trips, 1):
        print(f"{i}. Trip {trip['id']}: {trip['duration']} days, {trip['routing']}, {trip['credit_hours']} hours")
        print(f"   Dates: {trip['dates']}, Weekend: {trip['includes_weekend']}")
    
    return trips

if __name__ == "__main__":
    test_parsing()