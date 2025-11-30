#!/usr/bin/env python3
"""Test script to validate configuration and dependencies."""

import sys
import os
from pathlib import Path


def test_env_file():
    """Test if .env file exists and has required variables."""
    print("Checking .env file...")
    
    if not Path(".env").exists():
        print("  ❌ .env file not found")
        print("  → Copy .env.example to .env and configure it")
        return False
    
    required_vars = [
        "SUPABASE_URL",
        "SUPABASE_KEY",
        "ENCRYPTION_KEY"
    ]
    
    from dotenv import load_dotenv
    load_dotenv()
    
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"  ❌ Missing environment variables: {', '.join(missing)}")
        return False
    
    print("  ✓ .env file configured correctly")
    return True


def test_dependencies():
    """Test if all dependencies are installed."""
    print("\nChecking dependencies...")
    
    required_packages = [
        ("fastapi", "FastAPI"),
        ("uvicorn", "Uvicorn"),
        ("telethon", "Telethon"),
        ("supabase", "Supabase"),
        ("cryptography", "Cryptography"),
        ("aiosqlite", "aiosqlite"),
        ("websockets", "WebSockets")
    ]
    
    all_installed = True
    for package, name in required_packages:
        try:
            __import__(package)
            print(f"  ✓ {name}")
        except ImportError:
            print(f"  ❌ {name} not installed")
            all_installed = False
    
    if not all_installed:
        print("\n  → Run: uv sync")
        return False
    
    return True


def test_directories():
    """Test if required directories exist."""
    print("\nChecking directories...")
    
    required_dirs = ["src", "static", "data"]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"  ✓ {dir_name}/")
        else:
            print(f"  ❌ {dir_name}/ not found")
            if dir_name == "data":
                print(f"  → Creating {dir_name}/")
                dir_path.mkdir(parents=True, exist_ok=True)
            else:
                all_exist = False
    
    return all_exist


def test_static_files():
    """Test if static files exist."""
    print("\nChecking static files...")
    
    if not Path("static/index.html").exists():
        print("  ❌ static/index.html not found")
        return False
    
    print("  ✓ index.html")
    return True


def test_python_version():
    """Test Python version."""
    print("\nChecking Python version...")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print(f"  ❌ Python {version.major}.{version.minor} detected")
        print("  → Python 3.11 or higher required")
        return False
    
    print(f"  ✓ Python {version.major}.{version.minor}")
    return True


def test_supabase_connection():
    """Test Supabase connection."""
    print("\nTesting Supabase connection...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        from supabase import create_client
        
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            print("  ⚠️  Skipped (credentials not configured)")
            return True
        
        client = create_client(url, key)
        # Try a simple query
        client.table("telegram_accounts").select("id").limit(1).execute()
        
        print("  ✓ Supabase connection successful")
        return True
    
    except Exception as e:
        print(f"  ❌ Supabase connection failed: {e}")
        print("  → Check your Supabase URL and key")
        print("  → Make sure you ran the migration SQL")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("Telegram Dashboard Configuration Test")
    print("=" * 60)
    
    tests = [
        ("Python Version", test_python_version),
        ("Dependencies", test_dependencies),
        ("Directories", test_directories),
        ("Static Files", test_static_files),
        ("Environment", test_env_file),
        ("Supabase", test_supabase_connection),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ❌ Error running test: {e}")
            results.append((name, False))
    
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    all_passed = True
    for name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if not result:
            all_passed = False
    
    print("=" * 60)
    
    if all_passed:
        print("\n✓ All tests passed! You're ready to start the application.")
        print("\nRun: ./start.sh")
        return 0
    else:
        print("\n❌ Some tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
