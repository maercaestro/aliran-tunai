#!/usr/bin/env python3
"""
Health check script for AliranTunai services
This script performs comprehensive health checks for all application components
"""

import os
import sys
import time
import requests
import json
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
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

class HealthChecker:
    """Health checker for AliranTunai application components."""
    
    def __init__(self):
        self.api_base_url = "http://localhost:5000"
        self.services = ["aliran-tunai", "aliran-whatsapp"]
        self.health_data = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'overall_status': 'unknown',
            'checks': {}
        }
    
    def print_colored(self, message: str, color: str) -> None:
        """Print colored message to console."""
        print(f"{color}{message}{Colors.ENDC}")
    
    def print_header(self, title: str) -> None:
        """Print section header."""
        self.print_colored(f"\n{'='*60}", Colors.BLUE)
        self.print_colored(f" {title}", Colors.BOLD)
        self.print_colored(f"{'='*60}", Colors.BLUE)
    
    def check_systemd_services(self) -> bool:
        """Check if systemd services are running."""
        self.print_header("SystemD Services Health Check")
        
        all_services_ok = True
        service_statuses = {}
        
        for service in self.services:
            try:
                # Check if service is active
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                is_active = result.stdout.strip() == 'active'
                
                # Get detailed status
                status_result = subprocess.run(
                    ['systemctl', 'status', service, '--no-pager', '-l'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if is_active:
                    self.print_colored(f"✓ {service} - Running", Colors.GREEN)
                    service_statuses[service] = 'active'
                else:
                    self.print_colored(f"✗ {service} - Not running", Colors.RED)
                    all_services_ok = False
                    service_statuses[service] = 'inactive'
                    
                    # Show error details if service is failed
                    if 'failed' in status_result.stdout.lower():
                        self.print_colored(f"  Error details: {status_result.stdout[:200]}...", Colors.YELLOW)
            
            except subprocess.TimeoutExpired:
                self.print_colored(f"✗ {service} - Status check timeout", Colors.RED)
                all_services_ok = False
                service_statuses[service] = 'timeout'
            except Exception as e:
                self.print_colored(f"✗ {service} - Error checking status: {str(e)}", Colors.RED)
                all_services_ok = False
                service_statuses[service] = 'error'
        
        self.health_data['checks']['systemd_services'] = {
            'status': 'pass' if all_services_ok else 'fail',
            'details': service_statuses
        }
        
        return all_services_ok
    
    def check_api_endpoints(self) -> bool:
        """Check API endpoint health."""
        self.print_header("API Endpoints Health Check")
        
        endpoints_to_test = [
            ('/health', 'GET', None, 'Health check endpoint'),
            ('/whatsapp/webhook', 'GET', {
                'hub.mode': 'subscribe',
                'hub.verify_token': os.getenv('WHATSAPP_VERIFY_TOKEN', 'test'),
                'hub.challenge': 'health_check_challenge'
            }, 'WhatsApp webhook verification'),
        ]
        
        all_endpoints_ok = True
        endpoint_results = {}
        
        for path, method, params, description in endpoints_to_test:
            try:
                url = f"{self.api_base_url}{path}"
                
                if method == 'GET':
                    response = requests.get(url, params=params, timeout=10)
                else:
                    response = requests.post(url, json=params, timeout=10)
                
                response_time = response.elapsed.total_seconds()
                
                if response.status_code == 200:
                    self.print_colored(f"✓ {path} - OK ({response_time:.2f}s) - {description}", Colors.GREEN)
                    endpoint_results[path] = {
                        'status': 'pass',
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'description': description
                    }
                else:
                    self.print_colored(f"✗ {path} - HTTP {response.status_code} ({response_time:.2f}s) - {description}", Colors.RED)
                    all_endpoints_ok = False
                    endpoint_results[path] = {
                        'status': 'fail',
                        'status_code': response.status_code,
                        'response_time': response_time,
                        'description': description,
                        'error': f"HTTP {response.status_code}"
                    }
            
            except requests.exceptions.ConnectionError:
                self.print_colored(f"✗ {path} - Connection failed - {description}", Colors.RED)
                all_endpoints_ok = False
                endpoint_results[path] = {
                    'status': 'fail',
                    'description': description,
                    'error': 'Connection failed'
                }
            except requests.exceptions.Timeout:
                self.print_colored(f"✗ {path} - Timeout - {description}", Colors.RED)
                all_endpoints_ok = False
                endpoint_results[path] = {
                    'status': 'fail',
                    'description': description,
                    'error': 'Timeout'
                }
            except Exception as e:
                self.print_colored(f"✗ {path} - Error: {str(e)} - {description}", Colors.RED)
                all_endpoints_ok = False
                endpoint_results[path] = {
                    'status': 'fail',
                    'description': description,
                    'error': str(e)
                }
        
        self.health_data['checks']['api_endpoints'] = {
            'status': 'pass' if all_endpoints_ok else 'fail',
            'details': endpoint_results
        }
        
        return all_endpoints_ok
    
    def check_database_connection(self) -> bool:
        """Check MongoDB database connection."""
        self.print_header("Database Connection Health Check")
        
        mongo_uri = os.getenv('MONGO_URI')
        if not mongo_uri:
            self.print_colored("✗ MONGO_URI not configured", Colors.RED)
            self.health_data['checks']['database'] = {
                'status': 'fail',
                'error': 'MONGO_URI not configured'
            }
            return False
        
        try:
            from pymongo import MongoClient
            from pymongo.server_api import ServerApi
            
            # Test connection with timeout
            client = MongoClient(mongo_uri, server_api=ServerApi('1'), serverSelectionTimeoutMS=5000)
            
            start_time = time.time()
            client.admin.command('ping')
            response_time = time.time() - start_time
            
            # Test database operations
            db = client['transactions_db']
            collections = db.list_collection_names()
            
            # Test a simple query
            if 'entries' in collections:
                collection = db['entries']
                count = collection.count_documents({})
                self.print_colored(f"✓ MongoDB - Connected ({response_time:.2f}s, {count} documents)", Colors.GREEN)
            else:
                self.print_colored(f"✓ MongoDB - Connected ({response_time:.2f}s, no entries collection)", Colors.GREEN)
            
            # Check server status
            server_status = client.admin.command('serverStatus')
            uptime = server_status.get('uptime', 0)
            
            self.health_data['checks']['database'] = {
                'status': 'pass',
                'response_time': response_time,
                'collections': collections,
                'server_uptime': uptime,
                'document_count': count if 'entries' in collections else 0
            }
            
            return True
        
        except Exception as e:
            self.print_colored(f"✗ MongoDB - Connection failed: {str(e)}", Colors.RED)
            self.health_data['checks']['database'] = {
                'status': 'fail',
                'error': str(e)
            }
            return False
    
    def check_external_apis(self) -> bool:
        """Check external API connectivity."""
        self.print_header("External APIs Health Check")
        
        apis_to_test = [
            ('OpenAI API', self._test_openai_api),
            ('Telegram API', self._test_telegram_api),
            ('WhatsApp API', self._test_whatsapp_api),
        ]
        
        all_apis_ok = True
        api_results = {}
        
        for api_name, test_function in apis_to_test:
            try:
                result = test_function()
                if result['status'] == 'pass':
                    self.print_colored(f"✓ {api_name} - Connected", Colors.GREEN)
                else:
                    self.print_colored(f"✗ {api_name} - {result.get('error', 'Failed')}", Colors.RED)
                    all_apis_ok = False
                
                api_results[api_name.lower().replace(' ', '_')] = result
            
            except Exception as e:
                self.print_colored(f"✗ {api_name} - Error: {str(e)}", Colors.RED)
                all_apis_ok = False
                api_results[api_name.lower().replace(' ', '_')] = {
                    'status': 'fail',
                    'error': str(e)
                }
        
        self.health_data['checks']['external_apis'] = {
            'status': 'pass' if all_apis_ok else 'fail',
            'details': api_results
        }
        
        return all_apis_ok
    
    def _test_openai_api(self) -> Dict:
        """Test OpenAI API connection."""
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            return {'status': 'fail', 'error': 'API key not configured'}
        
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            
            # Test with minimal request
            response = client.models.list()
            return {'status': 'pass', 'models_available': len(response.data)}
        
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def _test_telegram_api(self) -> Dict:
        """Test Telegram API connection."""
        bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not bot_token:
            return {'status': 'fail', 'error': 'Bot token not configured'}
        
        try:
            response = requests.get(
                f"https://api.telegram.org/bot{bot_token}/getMe",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    return {
                        'status': 'pass',
                        'bot_username': bot_info.get('username'),
                        'bot_name': bot_info.get('first_name')
                    }
            
            return {'status': 'fail', 'error': f'HTTP {response.status_code}'}
        
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def _test_whatsapp_api(self) -> Dict:
        """Test WhatsApp Business API connection."""
        access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
        phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
        
        if not access_token or not phone_number_id:
            return {'status': 'fail', 'error': 'WhatsApp credentials not configured'}
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Test by getting phone number info
            response = requests.get(
                f"https://graph.facebook.com/v17.0/{phone_number_id}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'pass',
                    'phone_number': data.get('display_phone_number'),
                    'verified_name': data.get('verified_name')
                }
            
            return {'status': 'fail', 'error': f'HTTP {response.status_code}'}
        
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def check_system_resources(self) -> bool:
        """Check system resource usage."""
        self.print_header("System Resources Health Check")
        
        try:
            # Check disk usage
            disk_result = subprocess.run(
                ['df', '-h', '/'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check memory usage
            memory_result = subprocess.run(
                ['free', '-h'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Check CPU load
            load_result = subprocess.run(
                ['uptime'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            # Parse results
            disk_lines = disk_result.stdout.strip().split('\n')
            if len(disk_lines) > 1:
                disk_info = disk_lines[1].split()
                disk_usage = disk_info[4].rstrip('%') if len(disk_info) > 4 else 'N/A'
            
            memory_lines = memory_result.stdout.strip().split('\n')
            load_info = load_result.stdout.strip()
            
            # Evaluate health
            disk_ok = True
            try:
                if disk_usage != 'N/A' and int(disk_usage) > 90:
                    disk_ok = False
                    self.print_colored(f"⚠️  Disk usage: {disk_usage}% (High)", Colors.YELLOW)
                else:
                    self.print_colored(f"✓ Disk usage: {disk_usage}%", Colors.GREEN)
            except ValueError:
                self.print_colored("? Disk usage: Could not parse", Colors.YELLOW)
            
            self.print_colored(f"✓ Memory info available", Colors.GREEN)
            self.print_colored(f"✓ System load: {load_info}", Colors.GREEN)
            
            self.health_data['checks']['system_resources'] = {
                'status': 'pass' if disk_ok else 'warn',
                'disk_usage': disk_usage,
                'memory_info': memory_lines[1] if len(memory_lines) > 1 else 'N/A',
                'load_info': load_info
            }
            
            return disk_ok
        
        except Exception as e:
            self.print_colored(f"✗ System resources check failed: {str(e)}", Colors.RED)
            self.health_data['checks']['system_resources'] = {
                'status': 'fail',
                'error': str(e)
            }
            return False
    
    def check_log_files(self) -> bool:
        """Check log files for recent errors."""
        self.print_header("Log Files Health Check")
        
        log_paths = [
            '/var/log/aliran-tunai/app.log',
            '/var/log/syslog',
        ]
        
        all_logs_ok = True
        log_results = {}
        
        for log_path in log_paths:
            try:
                if not os.path.exists(log_path):
                    self.print_colored(f"- {log_path} - Not found (may be normal)", Colors.YELLOW)
                    log_results[log_path] = {'status': 'missing', 'note': 'Log file not found'}
                    continue
                
                # Check if log file is writable
                if not os.access(log_path, os.W_OK):
                    self.print_colored(f"✗ {log_path} - Not writable", Colors.RED)
                    all_logs_ok = False
                    log_results[log_path] = {'status': 'fail', 'error': 'Not writable'}
                    continue
                
                # Check for recent errors (last 100 lines)
                result = subprocess.run(
                    ['tail', '-100', log_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                error_count = result.stdout.lower().count('error')
                warning_count = result.stdout.lower().count('warning')
                
                if error_count > 10:
                    self.print_colored(f"⚠️  {log_path} - {error_count} recent errors found", Colors.YELLOW)
                    all_logs_ok = False
                    log_results[log_path] = {'status': 'warn', 'recent_errors': error_count, 'recent_warnings': warning_count}
                else:
                    self.print_colored(f"✓ {log_path} - OK ({error_count} errors, {warning_count} warnings)", Colors.GREEN)
                    log_results[log_path] = {'status': 'pass', 'recent_errors': error_count, 'recent_warnings': warning_count}
            
            except Exception as e:
                self.print_colored(f"✗ {log_path} - Error checking: {str(e)}", Colors.RED)
                all_logs_ok = False
                log_results[log_path] = {'status': 'fail', 'error': str(e)}
        
        self.health_data['checks']['log_files'] = {
            'status': 'pass' if all_logs_ok else 'warn',
            'details': log_results
        }
        
        return all_logs_ok
    
    def generate_health_report(self, all_checks_results: List[Tuple[str, bool]]) -> None:
        """Generate comprehensive health report."""
        self.print_header("Health Check Summary")
        
        passed_checks = sum(1 for _, result in all_checks_results if result)
        total_checks = len(all_checks_results)
        
        # Print individual check results
        for check_name, result in all_checks_results:
            status = "HEALTHY" if result else "UNHEALTHY"
            color = Colors.GREEN if result else Colors.RED
            self.print_colored(f"{status:>10} - {check_name}", color)
        
        # Overall status
        overall_healthy = passed_checks == total_checks
        overall_status = "HEALTHY" if overall_healthy else "DEGRADED"
        overall_color = Colors.GREEN if overall_healthy else Colors.YELLOW
        
        self.print_colored(f"\nOverall Status: {overall_status} ({passed_checks}/{total_checks} checks passed)", overall_color)
        
        # Update health data
        self.health_data['overall_status'] = 'healthy' if overall_healthy else 'degraded'
        self.health_data['checks_passed'] = passed_checks
        self.health_data['total_checks'] = total_checks
        
        # Save health report to file
        try:
            health_report_path = '/var/log/aliran-tunai/health_report.json'
            os.makedirs(os.path.dirname(health_report_path), exist_ok=True)
            
            with open(health_report_path, 'w') as f:
                json.dump(self.health_data, f, indent=2)
            
            self.print_colored(f"\n📄 Health report saved to: {health_report_path}", Colors.BLUE)
        except Exception as e:
            self.print_colored(f"\n⚠️  Could not save health report: {str(e)}", Colors.YELLOW)
        
        if not overall_healthy:
            self.print_colored("\nRecommendations:", Colors.BOLD)
            self.print_colored("1. Check failed services and restart if needed", Colors.YELLOW)
            self.print_colored("2. Verify network connectivity and API credentials", Colors.YELLOW)
            self.print_colored("3. Monitor system resources and clean up if needed", Colors.YELLOW)
            self.print_colored("4. Check application logs for detailed error information", Colors.YELLOW)
        else:
            self.print_colored("\n🎉 All systems are healthy!", Colors.GREEN)
    
    def run_all_checks(self) -> bool:
        """Run all health checks."""
        self.print_colored("AliranTunai Health Check", Colors.BOLD)
        self.print_colored("=" * 60, Colors.BLUE)
        
        checks = [
            ("SystemD Services", self.check_systemd_services),
            ("API Endpoints", self.check_api_endpoints),
            ("Database Connection", self.check_database_connection),
            ("External APIs", self.check_external_apis),
            ("System Resources", self.check_system_resources),
            ("Log Files", self.check_log_files),
        ]
        
        results = []
        for check_name, check_function in checks:
            try:
                result = check_function()
                results.append((check_name, result))
            except Exception as e:
                self.print_colored(f"✗ {check_name} - Error during check: {str(e)}", Colors.RED)
                results.append((check_name, False))
        
        self.generate_health_report(results)
        
        # Return overall health status
        return all(result for _, result in results)


def main():
    """Main health check function."""
    health_checker = HealthChecker()
    
    # Parse command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == '--json':
        # JSON output mode for monitoring systems
        is_healthy = health_checker.run_all_checks()
        print(json.dumps(health_checker.health_data))
        sys.exit(0 if is_healthy else 1)
    else:
        # Human-readable output mode
        is_healthy = health_checker.run_all_checks()
        sys.exit(0 if is_healthy else 1)


if __name__ == '__main__':
    main()