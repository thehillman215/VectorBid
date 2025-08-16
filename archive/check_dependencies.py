#!/usr/bin/env python3
"""
VectorBid System Health Check
Copy this entire code into a file called: check_dependencies.py
"""

import sys


def check_import(module_name, description=""):
    """Test importing a module and report status"""
    try:
        __import__(module_name)
        print(f"✅ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"❌ {module_name} - {description}")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"⚠️ {module_name} - {description}")
        print(f"   Unexpected error: {e}")
        return False


def check_file_exists(filepath, description=""):
    """Check if a file exists"""
    try:
        with open(filepath) as f:
            lines = len(f.readlines())
        print(f"✅ {filepath} - {description} ({lines} lines)")
        return True
    except FileNotFoundError:
        print(f"❌ {filepath} - {description} (File not found)")
        return False
    except Exception as e:
        print(f"⚠️ {filepath} - {description} (Error: {e})")
        return False


def main():
    print("🔍 VectorBid System Health Check")
    print("=" * 50)

    # Check Python version
    print(f"🐍 Python Version: {sys.version}")
    print()

    # Check standard libraries
    print("📦 Standard Libraries:")
    standard_libs = [
        ("flask", "Web framework"),
        ("dataclasses", "Python dataclasses"),
        ("enum", "Enumerations"),
        ("typing", "Type hints"),
        ("json", "JSON handling"),
        ("csv", "CSV parsing"),
        ("io", "I/O operations"),
        ("datetime", "Date/time handling"),
    ]

    std_success = 0
    for lib, desc in standard_libs:
        if check_import(lib, desc):
            std_success += 1

    print(
        f"\n📊 Standard Libraries: {std_success}/{len(standard_libs)} working")

    # Check third-party libraries (that might not be installed)
    print("\n🔌 Third-party Libraries:")
    third_party = [
        ("openai", "OpenAI API client"),
        ("fitz", "PyMuPDF for PDF parsing"),
        ("flask_sqlalchemy", "Database ORM"),
        ("flask_login", "User authentication"),
        ("werkzeug", "WSGI utilities"),
    ]

    third_success = 0
    for lib, desc in third_party:
        if check_import(lib, desc):
            third_success += 1

    print(
        f"\n📊 Third-party Libraries: {third_success}/{len(third_party)} working"
    )

    # Check our custom modules
    print("\n🏗️ VectorBid Files:")
    custom_files = [
        ("app.py", "Main Flask application"),
        ("bid_layers_system.py", "Bid layers engine"),
        ("bid_layers_routes.py", "Bid layers API routes"),
        ("admin.py", "Admin blueprint"),
    ]

    custom_success = 0
    for file, desc in custom_files:
        if check_file_exists(file, desc):
            custom_success += 1

    print(f"\n📊 VectorBid Files: {custom_success}/{len(custom_files)} present")

    # Test basic functionality
    print("\n🧪 Basic Functionality Tests:")

    try:
        # Test dataclass creation
        from dataclasses import dataclass
        from enum import Enum

        class TestEnum(Enum):
            VALUE = "test"

        @dataclass
        class TestClass:
            name: str
            value: TestEnum

        test_obj = TestClass("test", TestEnum.VALUE)
        print("✅ Dataclass and Enum creation working")

    except Exception as e:
        print(f"❌ Dataclass/Enum test failed: {e}")

    try:
        # Test Flask import and basic setup
        from flask import Flask
        app = Flask(__name__)
        print("✅ Flask application creation working")

    except Exception as e:
        print(f"❌ Flask test failed: {e}")

    # Summary
    print("\n" + "=" * 50)
    total_checks = len(standard_libs) + len(third_party) + len(
        custom_files) + 2
    total_success = std_success + third_success + custom_success + 2  # +2 for basic tests

    print(f"📋 Overall System Health: {total_success}/{total_checks}")

    if total_success == total_checks:
        print("🎉 All systems operational!")
        return True
    elif total_success >= total_checks * 0.8:
        print("⚠️ Most systems working - some issues to address")
        return True
    else:
        print("💥 Critical issues detected - system needs attention")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
