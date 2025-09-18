#!/usr/bin/env python3
"""
Environment validation script for AliranTunai
This script validates that all required environment variables and dependencies are available
"""

import os
import sys
import subprocess
import importlib
from typing import List, Tuple, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Color codes for output
class Colors:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(message: str, color: str) -> None:
    """Print colored message to console."""
    print(f"{color}{message}{Colors.ENDC}")

def print_header(title: str) -> None:
    """Print section header."""
    print_colored(f"\n{'='*50}", Colors.BLUE)
    print_colored(f" {title}", Colors.BOLD)
    print_colored(f"{'='*50}", Colors.BLUE)

def check_python_version() -> bool:
    """Check if Python version is compatible."""
    print_header("Python Version Check")
    
    version = sys.version_info
    required_major, required_minor = 3, 10
    
    if version.major >= required_major and version.minor >= required_minor:
        print_colored(f"✓ Python {version.major}.{version.minor}.{version.micro} - Compatible", Colors.GREEN)
        return True
    else:
        print_colored(f"✗ Python {version.major}.{version.minor}.{version.micro} - Requires Python {required_major}.{required_minor}+", Colors.RED)
        return False

def check_required_packages() -> bool:
    """Check if all required Python packages are installed."""
    print_header("Python Package Dependencies")
    
    required_packages = [
        'flask',
        'flask_cors',
        'pymongo',
        'python_telegram_bot',
        'openai',
        'requests',
        'python_dotenv',
        'pillow',
        'pytesseract',
        'pandas',
        'xlsxwriter'
    ]
    
    all_installed = True
    
    for package in required_packages:
        try:
            # Special handling for packages with different import names
            import_name = package
            if package == 'python_telegram_bot':
                import_name = 'telegram'
            elif package == 'python_dotenv':
                import_name = 'dotenv'
            elif package == 'pillow':
                import_name = 'PIL'
            
            importlib.import_module(import_name)
            print_colored(f"✓ {package} - Installed", Colors.GREEN)
        except ImportError:
            print_colored(f"✗ {package} - Missing", Colors.RED)
            all_installed = False
    
    return all_installed

def check_system_dependencies() -> bool:
    """Check if system dependencies are available."""
    print_header("System Dependencies")
    
    system_deps = [
        ('tesseract', 'tesseract --version'),
        ('nginx', 'nginx -v'),
        ('git', 'git --version'),
        ('curl', 'curl --version'),
    ]
    
    all_available = True
    
    for dep_name, command in system_deps:
        try:
            result = subprocess.run(
                command.split(), 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            if result.returncode == 0:
                print_colored(f"✓ {dep_name} - Available", Colors.GREEN)
            else:
                print_colored(f"✗ {dep_name} - Not working properly", Colors.RED)
                all_available = False
        except (subprocess.TimeoutExpired, FileNotFoundError):
            print_colored(f"✗ {dep_name} - Not found", Colors.RED)
            all_available = False
    
    return all_available

def check_environment_variables() -> bool:
    """Check if all required environment variables are set."""
    print_header("Environment Variables")
    
    required_vars = [
        ('MONGO_URI', 'MongoDB connection string'),
        ('TELEGRAM_BOT_TOKEN', 'Telegram bot token'),
        ('OPENAI_API_KEY', 'OpenAI API key'),
        ('WHATSAPP_VERIFY_TOKEN', 'WhatsApp verification token'),
        ('WHATSAPP_ACCESS_TOKEN', 'WhatsApp access token'),
        ('WHATSAPP_PHONE_NUMBER_ID', 'WhatsApp phone number ID'),
    ]
    
    optional_vars = [
        ('FLASK_ENV', 'Flask environment (defaults to production)'),
        ('LOG_LEVEL', 'Logging level (defaults to INFO)'),
        ('LOG_FILE', 'Log file path'),
    ]
    
    all_set = True
    
    print_colored("Required Variables:", Colors.BOLD)
    for var_name, description in required_vars:
        value = os.getenv(var_name)
        if value:
            # Mask sensitive values
            if 'TOKEN' in var_name or 'KEY' in var_name or 'URI' in var_name:
                masked_value = f"{value[:10]}...{value[-5:]}" if len(value) > 15 else "***"
            else:
                masked_value = value
            print_colored(f"✓ {var_name} = {masked_value}", Colors.GREEN)
        else:
            print_colored(f"✗ {var_name} - Not set ({description})", Colors.RED)
            all_set = False
    
    print_colored("\nOptional Variables:", Colors.BOLD)
    for var_name, description in optional_vars:
        value = os.getenv(var_name)
        if value:
            print_colored(f"✓ {var_name} = {value}", Colors.GREEN)
        else:
            print_colored(f"- {var_name} - Not set ({description})", Colors.YELLOW)
    
    return all_set

def test_mongodb_connection() -> bool:
    """Test MongoDB connection."""
    print_header("MongoDB Connection Test")
    
    mongo_uri = os.getenv('MONGO_URI')
    if not mongo_uri:
        print_colored("✗ MONGO_URI not set, skipping connection test", Colors.YELLOW)
        return False
    
    try:
        from pymongo import MongoClient
        from pymongo.server_api import ServerApi
        
        client = MongoClient(mongo_uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)
        client.admin.command('ping')
        
        # Test database access
        db = client['transactions_db']
        collections = db.list_collection_names()
        
        print_colored("✓ MongoDB connection successful", Colors.GREEN)
        print_colored(f"✓ Database accessible, collections: {collections}", Colors.GREEN)
        return True
    
    except Exception as e:
        print_colored(f"✗ MongoDB connection failed: {str(e)}", Colors.RED)
        return False

def test_openai_connection() -> bool:
    """Test OpenAI API connection."""
    print_header("OpenAI API Connection Test")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print_colored("✗ OPENAI_API_KEY not set, skipping connection test", Colors.YELLOW)
        return False
    
    try:
        from openai import OpenAI
        
        client = OpenAI(api_key=api_key)
        
        # Test with a simple completion request
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Test"}],
            max_tokens=5
        )
        
        print_colored("✓ OpenAI API connection successful", Colors.GREEN)
        return True
    
    except Exception as e:
        print_colored(f"✗ OpenAI API connection failed: {str(e)}", Colors.RED)
        return False

def check_file_permissions() -> bool:
    """Check file permissions for important directories."""
    print_header("File Permissions")
    
    paths_to_check = [
        ('/opt/aliran-tunai', 'Application directory'),
        ('/var/log/aliran-tunai', 'Log directory'),
        ('/tmp', 'Temporary directory'),
    ]
    
    all_ok = True
    
    for path, description in paths_to_check:
        if os.path.exists(path):
            if os.access(path, os.R_OK | os.W_OK):
                print_colored(f"✓ {path} - Read/Write access OK ({description})", Colors.GREEN)
            else:
                print_colored(f"✗ {path} - Insufficient permissions ({description})", Colors.RED)
                all_ok = False
        else:
            print_colored(f"- {path} - Directory doesn't exist ({description})", Colors.YELLOW)
    
    return all_ok

def check_network_connectivity() -> bool:
    """Check network connectivity to essential services."""
    print_header("Network Connectivity")
    
    endpoints_to_test = [
        ('api.openai.com', 'OpenAI API'),
        ('api.telegram.org', 'Telegram API'),
        ('graph.facebook.com', 'WhatsApp Business API'),
        ('8.8.8.8', 'Internet connectivity'),
    ]
    
    all_reachable = True
    
    for endpoint, description in endpoints_to_test:
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '5', endpoint],
                capture_output=True,
                timeout=10
            )
            if result.returncode == 0:
                print_colored(f"✓ {endpoint} - Reachable ({description})", Colors.GREEN)
            else:
                print_colored(f"✗ {endpoint} - Unreachable ({description})", Colors.RED)
                all_reachable = False
        except subprocess.TimeoutExpired:
            print_colored(f"✗ {endpoint} - Timeout ({description})", Colors.RED)
            all_reachable = False
        except Exception as e:
            print_colored(f"✗ {endpoint} - Error: {str(e)} ({description})", Colors.RED)
            all_reachable = False
    
    return all_reachable

def generate_report(checks_results: List[Tuple[str, bool]]) -> bool:
    """Generate final validation report."""
    print_header("Validation Summary")
    
    passed_checks = sum(1 for _, result in checks_results if result)
    total_checks = len(checks_results)
    
    for check_name, result in checks_results:
        status = "PASS" if result else "FAIL"
        color = Colors.GREEN if result else Colors.RED
        print_colored(f"{status:>6} - {check_name}", color)
    
    print_colored(f"\nOverall: {passed_checks}/{total_checks} checks passed", 
                  Colors.GREEN if passed_checks == total_checks else Colors.YELLOW)
    
    if passed_checks == total_checks:
        print_colored("\n🎉 All validation checks passed! Your environment is ready for deployment.", Colors.GREEN)
        return True
    else:
        print_colored(f"\n⚠️  {total_checks - passed_checks} validation checks failed. Please fix the issues before deploying.", Colors.YELLOW)
        return False

def main():
    """Main validation function."""
    print_colored("AliranTunai Environment Validation", Colors.BOLD)
    print_colored("=" * 50, Colors.BLUE)
    
    checks = [
        ("Python Version", check_python_version),
        ("Required Packages", check_required_packages),
        ("System Dependencies", check_system_dependencies),
        ("Environment Variables", check_environment_variables),
        ("MongoDB Connection", test_mongodb_connection),
        ("OpenAI API Connection", test_openai_connection),
        ("File Permissions", check_file_permissions),
        ("Network Connectivity", check_network_connectivity),
    ]
    
    results = []
    for check_name, check_function in checks:
        try:
            result = check_function()
            results.append((check_name, result))
        except Exception as e:
            print_colored(f"✗ {check_name} - Error during check: {str(e)}", Colors.RED)
            results.append((check_name, False))
    
    all_passed = generate_report(results)
    
    if not all_passed:
        print_colored("\nRecommendations:", Colors.BOLD)
        print_colored("1. Install missing system dependencies", Colors.YELLOW)
        print_colored("2. Set all required environment variables in .env file", Colors.YELLOW)
        print_colored("3. Verify database and API credentials", Colors.YELLOW)
        print_colored("4. Check network connectivity and firewall settings", Colors.YELLOW)
        print_colored("5. Run this script again after fixing issues", Colors.YELLOW)
        
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
    main()