# test_bid_layers.py - Create this file in your Replit project

print("🧪 Testing VectorBid Enhanced Bid Layers System")
print("=" * 50)

try:
    # Test 1: Import and basic functionality
    print("Test 1: Importing modules...")
    from bid_layers_system import BidLayersSystem, create_weekends_off_layer
    print("✅ Imports successful")

    # Create a system
    system = BidLayersSystem()
    print(f"✅ System created. Max layers: {system.max_layers}")

    # Add a test layer
    layer = create_weekends_off_layer(10)
    success = system.add_layer(layer)
    print(f"✅ Layer added successfully: {success}")
    print(f"✅ Total layers: {len(system.layers)}")
    print(f"✅ Layer name: {system.layers[0].name}")

except Exception as e:
    print(f"❌ Test 1 Failed: {e}")
    exit()

print("\n" + "=" * 50)

try:
    # Test 2: Trip analysis functionality
    print("Test 2: Analyzing sample trips...")

    sample_trips = [{
        'trip_id': 'TEST001',
        'pairing_id': 'T001',
        'days': 3,
        'credit_hours': 18.5,
        'includes_weekend': False,
        'layover_cities': ['LAX'],
        'is_red_eye': False,
        'departure_time': '08:00',
        'is_commutable': True,
        'is_international': False
    }, {
        'trip_id': 'TEST002',
        'pairing_id': 'T002',
        'days': 4,
        'credit_hours': 22.0,
        'includes_weekend': True,
        'layover_cities': ['ORD'],
        'is_red_eye': True,
        'departure_time': '23:30',
        'is_commutable': False,
        'is_international': False
    }]

    # Analyze trips
    evaluated = system.evaluate_all_trips(sample_trips)
    print(f"✅ Analyzed {len(evaluated)} trips")

    for trip in evaluated:
        print(
            f"  Trip {trip['trip_id']}: Score {trip['total_score']:.1f} - {trip['bid_recommendation']}"
        )
        print(f"    Matching layers: {trip['matching_layers']}")

except Exception as e:
    print(f"❌ Test 2 Failed: {e}")

print("\n" + "=" * 50)

try:
    # Test 3: PBS code generation
    print("Test 3: Generating PBS code...")

    pbs_code = system.generate_pbs_output(evaluated)
    print("✅ Generated PBS Code:")
    print("-" * 30)
    print(pbs_code)
    print("-" * 30)

except Exception as e:
    print(f"❌ Test 3 Failed: {e}")

print("\n" + "=" * 50)

try:
    # Test 4: Layer summary
    print("Test 4: Getting layer summary...")

    summary = system.get_layer_summary()
    print(f"✅ Total layers: {summary['total_layers']}")
    print(f"✅ Active layers: {summary['active_layers']}")
    print("✅ Layer details:")
    for layer_detail in summary['layers_detail']:
        print(
            f"  - {layer_detail['name']} (Priority: {layer_detail['priority']})"
        )

except Exception as e:
    print(f"❌ Test 4 Failed: {e}")

print("\n🎉 All tests completed!")
