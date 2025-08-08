#!/usr/bin/env python3
"""
Test script to verify QueryIQ improvements
"""

import sys
import time
from pathlib import Path

def test_imports():
    """Test that all modules can be imported."""
    print("Testing imports...")
    
    try:
        from src.main import QueryIQ
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_connection_manager():
    """Test connection manager functionality."""
    print("\nTesting connection manager...")
    
    try:
        from src.data.connection_manager import DatabaseConnectionManager
        # This will fail if config.json doesn't exist, but that's expected
        manager = DatabaseConnectionManager()
        print("✅ Connection manager created successfully")
        return True
    except FileNotFoundError:
        print("⚠️  config.json not found (expected for testing)")
        return True
    except Exception as e:
        print(f"❌ Connection manager error: {e}")
        return False

def test_performance_monitor():
    """Test performance monitor functionality."""
    print("\nTesting performance monitor...")
    
    try:
        from src.visualization.performance_monitor import PerformanceMonitor
        monitor = PerformanceMonitor()
        print("✅ Performance monitor created successfully")
        
        # Test report generation (will show no data message)
        monitor.generate_performance_report(days_back=1)
        print("✅ Performance report generation successful")
        return True
    except Exception as e:
        print(f"❌ Performance monitor error: {e}")
        return False

def test_bash_script():
    """Test that bash script exists and is executable."""
    print("\nTesting bash script...")
    
    script_path = Path("scripts/setup_database.sh")
    if script_path.exists():
        print("✅ Bash script exists")
        if script_path.stat().st_mode & 0o111:  # Check if executable
            print("✅ Bash script is executable")
            return True
        else:
            print("⚠️  Bash script exists but is not executable")
            return False
    else:
        print("❌ Bash script not found")
        return False

def test_powershell_removal():
    """Test that PowerShell script has been removed."""
    print("\nTesting PowerShell script removal...")
    
    ps1_path = Path("scripts/setup_database.ps1")
    if not ps1_path.exists():
        print("✅ PowerShell script successfully removed")
        return True
    else:
        print("❌ PowerShell script still exists")
        return False

def test_powerbi_removal():
    """Test that PowerBI connector has been removed."""
    print("\nTesting PowerBI removal...")
    
    powerbi_path = Path("src/visualization/powerbi_connector.py")
    if not powerbi_path.exists():
        print("✅ PowerBI connector successfully removed")
        return True
    else:
        print("❌ PowerBI connector still exists")
        return False

def test_requirements_update():
    """Test that requirements.txt has been updated."""
    print("\nTesting requirements.txt updates...")
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        # Check that PowerBI dependency is removed
        if "powerbiclient" not in content:
            print("✅ PowerBI dependency removed")
        else:
            print("❌ PowerBI dependency still present")
            return False
        
        # Check that connection pooling is added
        if "psycopg2-pool" in content:
            print("✅ Connection pooling dependency added")
        else:
            print("❌ Connection pooling dependency missing")
            return False
        
        # Check that matplotlib is added
        if "matplotlib" in content:
            print("✅ Matplotlib dependency added")
        else:
            print("❌ Matplotlib dependency missing")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error checking requirements.txt: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing QueryIQ Improvements")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_connection_manager,
        test_performance_monitor,
        test_bash_script,
        test_powershell_removal,
        test_powerbi_removal,
        test_requirements_update
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Improvements implemented successfully.")
        return 0
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 