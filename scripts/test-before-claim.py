#!/usr/bin/env python3
"""
Automated Testing Enforcement Script
Forces functional testing before any status claims
"""
import subprocess
import json
import sys
import time
import requests
from pathlib import Path

class VectorBidTester:
    def __init__(self):
        self.base_url = "http://localhost:8001"
        self.tests_passed = 0
        self.tests_failed = 0
        self.results = []
    
    def test_server_running(self):
        """Test 1: Basic server connectivity"""
        try:
            response = requests.get(f"{self.base_url}/", timeout=5)
            if response.status_code == 200:
                self.log_test("✅ Server Running", "Landing page loads")
                return True
            else:
                self.log_test("❌ Server Issue", f"Status code: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("❌ Server Down", f"Cannot connect: {e}")
            return False
    
    def test_health_endpoint(self):
        """Test 2: Health and database connectivity"""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("db") == "ok":
                    self.log_test("✅ Database Connected", f"Health: {data}")
                    return True
                else:
                    self.log_test("❌ Database Issue", f"Health response: {data}")
                    return False
            else:
                self.log_test("❌ Health Check Failed", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("❌ Health Check Error", f"Error: {e}")
            return False
    
    def test_llm_integration(self):
        """Test 3: LLM preference parsing"""
        try:
            payload = {"preferences_text": "I want weekends off and no early departures"}
            response = requests.post(
                f"{self.base_url}/api/parse_preferences", 
                json=payload, 
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("method") == "llm" and data.get("confidence", 0) > 0.8:
                    self.log_test("✅ LLM Integration Working", f"Confidence: {data.get('confidence')}")
                    return True
                elif data.get("method") == "fallback":
                    self.log_test("⚠️ LLM Fallback Only", "API key not configured")
                    return False
                else:
                    self.log_test("❌ LLM Integration Broken", f"Response: {data}")
                    return False
            else:
                self.log_test("❌ LLM API Error", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("❌ LLM Request Failed", f"Error: {e}")
            return False
    
    def test_optimization_engine(self):
        """Test 4: Core optimization functionality"""
        payload = {
            "feature_bundle": {
                "context": {
                    "ctx_id": "test", "pilot_id": "test", "month": "2025-03", 
                    "seat": "FO", "equip": ["73G"], "seniority_percentile": 0.5,
                    "airline": "UAL", "base": "SFO"
                },
                "preference_schema": {
                    "pilot_id": "test", "airline": "UAL", "base": "SFO", 
                    "seat": "FO", "equip": ["73G"],
                    "hard_constraints": {"no_red_eyes": False},
                    "soft_prefs": {"weekend_priority": {"weight": 0.9}}
                },
                "analytics_features": {}, "compliance_flags": {},
                "pairing_features": {"pairings": []}
            },
            "K": 3
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/optimize", 
                json=payload, 
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if len(candidates) > 0:
                    self.log_test("✅ Optimization Working", f"Generated {len(candidates)} candidates")
                    return True
                else:
                    self.log_test("❌ Optimization Empty", "No candidates generated")
                    return False
            else:
                self.log_test("❌ Optimization Failed", f"Status: {response.status_code}, Response: {response.text}")
                return False
        except Exception as e:
            self.log_test("❌ Optimization Error", f"Error: {e}")
            return False
    
    def test_pbs_generation(self):
        """Test 5: PBS layers generation"""
        payload = {
            "feature_bundle": {
                "context": {
                    "ctx_id": "test", "pilot_id": "test", "month": "2025-03",
                    "seat": "FO", "equip": ["73G"], "seniority_percentile": 0.5,
                    "airline": "UAL", "base": "SFO"
                },
                "preference_schema": {
                    "pilot_id": "test", "airline": "UAL", "base": "SFO",
                    "seat": "FO", "equip": ["73G"],
                    "hard_constraints": {"no_red_eyes": False},
                    "soft_prefs": {"weekend_priority": {"weight": 0.9}}
                },
                "analytics_features": {}, "compliance_flags": {},
                "pairing_features": {"pairings": []}
            },
            "candidates": []
        }
        
        try:
            response = requests.post(
                f"{self.base_url}/api/generate_layers",
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                artifact = data.get("artifact", {})
                layers = artifact.get("layers", [])
                if len(layers) > 0:
                    self.log_test("✅ PBS Generation Working", f"Generated {len(layers)} layers")
                    return True
                else:
                    self.log_test("❌ PBS Generation Empty", "No PBS layers generated")
                    return False
            else:
                self.log_test("❌ PBS Generation Failed", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("❌ PBS Generation Error", f"Error: {e}")
            return False
    
    def test_admin_portal(self):
        """Test 6: Admin portal accessibility"""
        try:
            response = requests.get(f"{self.base_url}/admin", timeout=5)
            if response.status_code == 200:
                self.log_test("✅ Admin Portal Accessible", "Admin interface loads")
                return True
            else:
                self.log_test("❌ Admin Portal Missing", f"Status: {response.status_code}")
                return False
        except Exception as e:
            self.log_test("❌ Admin Portal Error", f"Error: {e}")
            return False
    
    def log_test(self, status, message):
        """Log test result and update counters"""
        result = f"{status}: {message}"
        print(result)
        self.results.append(result)
        
        if status.startswith("✅"):
            self.tests_passed += 1
        else:
            self.tests_failed += 1
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🧪 VectorBid Functional Testing Suite")
        print("=" * 50)
        print(f"Testing against: {self.base_url}")
        print()
        
        tests = [
            self.test_server_running,
            self.test_health_endpoint, 
            self.test_llm_integration,
            self.test_optimization_engine,
            self.test_pbs_generation,
            self.test_admin_portal
        ]
        
        for test in tests:
            test()
            time.sleep(0.5)  # Brief pause between tests
        
        print()
        print("📊 Test Results Summary")
        print("=" * 50)
        print(f"✅ Passed: {self.tests_passed}")
        print(f"❌ Failed: {self.tests_failed}")
        print(f"📈 Success Rate: {(self.tests_passed/(self.tests_passed+self.tests_failed)*100):.1f}%")
        
        # Calculate realistic completion percentage
        functional_percent = (self.tests_passed / len(tests)) * 100
        print(f"🎯 Functional Completion: {functional_percent:.1f}%")
        
        if functional_percent < 50:
            print("\n🚨 CRITICAL: Less than 50% core functionality working")
            print("   DO NOT CLAIM PRODUCTION READINESS")
        elif functional_percent < 80:
            print("\n⚠️ WARNING: Significant functionality missing")
            print("   NOT READY FOR PILOT BETA")
        else:
            print("\n✅ GOOD: Core functionality mostly working")
            print("   Consider pilot beta testing")
        
        return functional_percent
    
    def generate_status_report(self):
        """Generate automated status report"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"""# Automated Test Report
**Generated**: {timestamp}
**Test Suite**: VectorBid Functional Testing

## Test Results
"""
        for result in self.results:
            report += f"- {result}\n"
        
        report += f"""
## Summary
- **Tests Passed**: {self.tests_passed}
- **Tests Failed**: {self.tests_failed}
- **Success Rate**: {(self.tests_passed/(self.tests_passed+self.tests_failed)*100):.1f}%
- **Functional Completion**: {(self.tests_passed/6)*100:.1f}%

## Status Assessment
"""
        functional_percent = (self.tests_passed / 6) * 100
        if functional_percent < 50:
            report += "🚨 **NOT READY**: Core functionality broken\n"
        elif functional_percent < 80:
            report += "⚠️ **INCOMPLETE**: Significant features missing\n"
        else:
            report += "✅ **FUNCTIONAL**: Most features working\n"
        
        # Write report to file
        report_path = Path("TEST_RESULTS.md")
        report_path.write_text(report)
        print(f"\n📄 Detailed report saved to: {report_path}")
        
        return report

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("""
VectorBid Testing Enforcement Script

Usage:
    python scripts/test-before-claim.py [--port PORT]
    
This script runs comprehensive functional tests and prevents
optimistic status claims by providing honest assessments.

The script tests:
1. Basic server connectivity
2. Database health
3. LLM integration 
4. Optimization engine
5. PBS generation
6. Admin portal

Results are logged to TEST_RESULTS.md with realistic completion percentages.
        """)
        return
    
    # Check if server is specified
    port = 8001
    if len(sys.argv) > 2 and sys.argv[1] == "--port":
        port = int(sys.argv[2])
    
    tester = VectorBidTester()
    tester.base_url = f"http://localhost:{port}"
    
    functional_percent = tester.run_all_tests()
    tester.generate_status_report()
    
    # Return exit code based on functionality
    if functional_percent < 50:
        sys.exit(1)  # Fail if less than 50% working
    else:
        sys.exit(0)  # Pass if at least 50% working

if __name__ == "__main__":
    main()