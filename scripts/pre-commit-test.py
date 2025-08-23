#!/usr/bin/env python3
"""
Pre-commit hook: Prevents commits claiming functionality without testing
"""
import re
import sys
import subprocess
from pathlib import Path

def check_for_completion_claims(files):
    """Check if any files contain optimistic completion claims"""
    dangerous_patterns = [
        r"99%.*complete",
        r"100%.*complete", 
        r"✅.*complete",
        r"working.*successfully",
        r"fully.*functional",
        r"production.*ready",
        r"MVP.*complete"
    ]
    
    violations = []
    
    for file_path in files:
        if not file_path.endswith(('.md', '.txt', '.py')):
            continue
            
        try:
            content = Path(file_path).read_text()
            
            for pattern in dangerous_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    violations.append({
                        'file': file_path,
                        'pattern': pattern,
                        'matches': matches
                    })
        except Exception:
            continue
    
    return violations

def check_for_test_evidence(files):
    """Check if status claims include test evidence"""
    status_files = [f for f in files if 'STATUS' in f.upper() or 'DEVELOPMENT' in f.upper()]
    
    missing_evidence = []
    for file_path in status_files:
        try:
            content = Path(file_path).read_text()
            
            # Look for test evidence
            has_test_date = re.search(r"tested.*\d{4}-\d{2}-\d{2}", content, re.IGNORECASE)
            has_api_results = re.search(r"curl.*localhost", content, re.IGNORECASE)
            has_error_messages = re.search(r'".*error.*"', content, re.IGNORECASE)
            
            if not (has_test_date or has_api_results or has_error_messages):
                missing_evidence.append(file_path)
                
        except Exception:
            continue
    
    return missing_evidence

def main():
    # Get list of staged files
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        staged_files = result.stdout.strip().split('\n')
    except subprocess.CalledProcessError:
        print("❌ Error: Could not get staged files")
        sys.exit(1)
    
    if not staged_files or staged_files == ['']:
        print("✅ No staged files to check")
        sys.exit(0)
    
    print("🔍 Pre-commit testing enforcement...")
    print(f"Checking {len(staged_files)} staged files")
    
    # Check for dangerous completion claims
    violations = check_for_completion_claims(staged_files)
    missing_evidence = check_for_test_evidence(staged_files)
    
    if violations or missing_evidence:
        print("\n🚨 COMMIT BLOCKED: Suspicious completion claims detected")
        print("=" * 60)
        
        if violations:
            print("\n❌ Files with unsubstantiated completion claims:")
            for v in violations:
                print(f"   {v['file']}: {v['matches']}")
        
        if missing_evidence:
            print("\n❌ Status files missing test evidence:")
            for file in missing_evidence:
                print(f"   {file}")
        
        print("\n📋 To commit these changes, you must:")
        print("1. Run functional tests: python scripts/test-before-claim.py")
        print("2. Include test results and dates in status claims")
        print("3. Use realistic percentages based on actual testing")
        print("4. Or override with: git commit --no-verify")
        
        sys.exit(1)
    
    print("✅ Pre-commit checks passed")
    sys.exit(0)

if __name__ == "__main__":
    main()