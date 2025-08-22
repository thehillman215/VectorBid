#!/usr/bin/env python3
"""
Debug script to test the UI endpoints directly
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_optimization():
    """Test the optimization endpoint"""
    print("🧮 Testing Mathematical Optimization API...")
    
    payload = {
        "feature_bundle": {
            "context": {
                "ctx_id": "debug_math_001",
                "pilot_id": "debug_pilot",
                "airline": "UAL",
                "month": "2025.08",
                "base": "SFO",
                "seat": "CA",
                "equip": ["737"],
                "seniority_percentile": 0.65
            },
            "preference_schema": {
                "pilot_id": "debug_pilot",
                "airline": "UAL",
                "base": "SFO",
                "seat": "CA",
                "equip": ["737"],
                "hard_constraints": {
                    "no_red_eyes": False,
                    "days_off": []
                },
                "soft_prefs": {
                    "weekend_priority": {"weight": 0.8},
                    "credit": {"weight": 0.7},
                    "layovers": {"prefer": ["LAX"], "avoid": ["ORD"], "weight": 0.6}
                }
            },
            "analytics_features": {
                "base_stats": {
                    "LAX": {"award_rate": 0.8},
                    "DEN": {"award_rate": 0.9},
                    "ORD": {"award_rate": 0.7}
                }
            },
            "compliance_flags": {},
            "pairing_features": {
                "pairings": [
                    {
                        "id": "SFO-LAX-FAMILY",
                        "layover_city": "LAX",
                        "block_hours": 8.5,
                        "duty_hours": 11.0,
                        "rest_hours": 24.0,
                        "equipment": "737",
                        "report_time": "0900",
                        "trip_length": 2,
                        "is_commutable": True
                    },
                    {
                        "id": "SFO-DEN-CREDIT",
                        "layover_city": "DEN",
                        "block_hours": 12.2,
                        "duty_hours": 14.5,
                        "rest_hours": 15.0,
                        "equipment": "737",
                        "report_time": "0600",
                        "trip_length": 3,
                        "is_commutable": False
                    },
                    {
                        "id": "SFO-ORD-BALANCED",
                        "layover_city": "ORD",
                        "block_hours": 9.8,
                        "duty_hours": 12.5,
                        "rest_hours": 20.0,
                        "equipment": "737",
                        "report_time": "1200",
                        "trip_length": 2,
                        "is_commutable": True
                    }
                ]
            }
        },
        "K": 5
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/optimize", json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        candidates = result.get("candidates", [])
        
        print(f"✅ Success: Generated {len(candidates)} candidates")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i}. {candidate['candidate_id']}: score={candidate['score']:.3f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def test_llm_optimization():
    """Test the LLM-enhanced optimization endpoint"""
    print("\n🧠 Testing LLM-Enhanced Optimization API...")
    
    # First get candidates from basic optimization
    basic_result = test_optimization()
    if not basic_result:
        print("❌ Can't test LLM without basic optimization working")
        return None
    
    payload = {
        "feature_bundle": {
            "context": {
                "ctx_id": "debug_llm_001",
                "pilot_id": "debug_pilot",
                "airline": "UAL",
                "month": "2025.08",
                "base": "SFO",
                "seat": "CA",
                "equip": ["737"],
                "seniority_percentile": 0.65
            },
            "preference_schema": {
                "pilot_id": "debug_pilot",
                "airline": "UAL",
                "base": "SFO",
                "seat": "CA",
                "equip": ["737"],
                "hard_constraints": {
                    "no_red_eyes": False,
                    "days_off": []
                },
                "soft_prefs": {
                    "weekend_priority": {"weight": 0.8},
                    "credit": {"weight": 0.7},
                    "layovers": {"prefer": ["LAX"], "avoid": ["ORD"], "weight": 0.6}
                }
            },
            "analytics_features": {
                "base_stats": {
                    "LAX": {"award_rate": 0.8},
                    "DEN": {"award_rate": 0.9}
                }
            },
            "compliance_flags": {},
            "pairing_features": {
                "pairings": [
                    {
                        "id": "SFO-LAX-FAMILY",
                        "layover_city": "LAX",
                        "block_hours": 8.5,
                        "duty_hours": 11.0,
                        "rest_hours": 24.0,
                        "equipment": "737"
                    },
                    {
                        "id": "SFO-DEN-CREDIT",
                        "layover_city": "DEN",
                        "block_hours": 12.2,
                        "duty_hours": 14.5,
                        "rest_hours": 15.0,
                        "equipment": "737"
                    }
                ]
            }
        },
        "K": 5,
        "use_llm": True,
        "pilot_context": {
            "lifestyle": "family_first",
            "base": "SFO",
            "seniority_percentile": 0.65
        }
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/optimize_enhanced", json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        enhanced_candidates = result.get("enhanced_candidates", [])
        optimization_analysis = result.get("optimization_analysis", {})
        
        print(f"✅ Success: Enhanced {len(enhanced_candidates)} candidates")
        print(f"📊 Quality: {optimization_analysis.get('quality', 0):.2f}")
        print(f"🎯 Preference Alignment: {optimization_analysis.get('preference_alignment', 0):.2f}")
        
        ai_insights = result.get("ai_insights", {})
        print(f"🧠 Method: {ai_insights.get('method', 'unknown')}")
        print(f"🎪 Confidence: {ai_insights.get('confidence', 0):.2f}")
        
        return result
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def test_bid_layers():
    """Test bid layer generation"""
    print("\n🎯 Testing Bid Layer Generation...")
    
    # Get candidates first
    basic_result = test_optimization()
    if not basic_result:
        print("❌ Can't test layers without candidates")
        return None
    
    candidates = basic_result.get("candidates", [])
    if not candidates:
        print("❌ No candidates to generate layers from")
        return None
    
    payload = {
        "feature_bundle": {
            "context": {
                "ctx_id": "debug_layers_001",
                "pilot_id": "debug_pilot",
                "airline": "UAL",
                "month": "2025.08",
                "base": "SFO",
                "seat": "CA",
                "equip": ["737"],
                "seniority_percentile": 0.65
            },
            "preference_schema": {
                "pilot_id": "debug_pilot",
                "airline": "UAL",
                "base": "SFO",
                "seat": "CA",
                "equip": ["737"],
                "hard_constraints": {
                    "no_red_eyes": False,
                    "days_off": []
                },
                "soft_prefs": {
                    "weekend_priority": {"weight": 0.8},
                    "credit": {"weight": 0.7},
                    "layovers": {"prefer": ["LAX"], "avoid": ["ORD"], "weight": 0.6}
                }
            },
            "analytics_features": {},
            "compliance_flags": {},
            "pairing_features": {"pairings": []}
        },
        "candidates": candidates
    }
    
    try:
        response = requests.post(f"{BASE_URL}/api/generate_layers", json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        artifact = result.get("artifact", {})
        layers = artifact.get("layers", [])
        
        print(f"✅ Success: Generated {len(layers)} bid layers")
        print(f"📋 Format: {artifact.get('format', 'unknown')}")
        print(f"✈️ Airline: {artifact.get('airline', 'unknown')}")
        print(f"📅 Month: {artifact.get('month', 'unknown')}")
        
        for i, layer in enumerate(layers[:3], 1):  # Show first 3
            filters = layer.get("filters", [])
            print(f"  Layer {layer.get('n', i)}: {len(filters)} filters, prefer={layer.get('prefer', 'unknown')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return None

def main():
    """Run all tests"""
    print("VectorBid UI Debug Test Suite")
    print("=" * 50)
    
    # Test server connectivity
    try:
        response = requests.get(f"{BASE_URL}/test-llm", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running and test UI is accessible")
            print(f"🌐 Test UI: {BASE_URL}/test-llm")
        else:
            print(f"⚠️ Server running but test UI returned {response.status_code}")
    except Exception as e:
        print(f"❌ Server connectivity failed: {e}")
        print("Make sure the server is running: uvicorn app.main:app --reload")
        sys.exit(1)
    
    # Run API tests
    math_result = test_optimization()
    llm_result = test_llm_optimization()
    layer_result = test_bid_layers()
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Test Summary:")
    print(f"  Mathematical Optimization: {'✅ PASS' if math_result else '❌ FAIL'}")
    print(f"  LLM Enhancement: {'✅ PASS' if llm_result else '❌ FAIL'}")
    print(f"  Bid Layer Generation: {'✅ PASS' if layer_result else '❌ FAIL'}")
    
    if all([math_result, llm_result, layer_result]):
        print("\n🚀 All systems are working! The UI should now function correctly.")
        print(f"🌐 Open your browser to: {BASE_URL}/test-llm")
    else:
        print("\n⚠️ Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main()