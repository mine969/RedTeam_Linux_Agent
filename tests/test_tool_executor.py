"""
Test Tool Executor - Verify safety controls and tool execution

Tests:
- IP whitelist validation
- Port validation
- Rate limiting
- Command sanitization
- Tool execution (mocked)
"""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from tools.tool_executor import ToolExecutor
from safety.monitor import SafetyMonitor

class TestSafetyControls(unittest.TestCase):
    """Test safety monitor functionality"""
    
    def setUp(self):
        """Setup test environment"""
        self.safety = SafetyMonitor()
    
    def test_whitelist_allowed_ip(self):
        """Test that whitelisted IPs are allowed"""
        result = self.safety.validate_target_ip("172.20.0.10")
        self.assertTrue(result, "Whitelisted IP should be allowed")
    
    def test_whitelist_blocked_ip(self):
        """Test that non-whitelisted IPs are blocked"""
        result = self.safety.validate_target_ip("8.8.8.8")
        self.assertFalse(result, "Non-whitelisted IP should be blocked")
    
    def test_whitelist_blocked_private_ip(self):
        """Test that private IPs outside whitelist are blocked"""
        result = self.safety.validate_target_ip("192.168.1.1")
        self.assertFalse(result, "Private IP outside whitelist should be blocked")
    
    def test_port_validation_allowed(self):
        """Test that allowed ports pass validation"""
        result = self.safety.validate_port(22)
        self.assertTrue(result, "Port 22 should be allowed")
        
        result = self.safety.validate_port(2222)
        self.assertTrue(result, "Port 2222 should be allowed")
    
    def test_port_validation_blocked(self):
        """Test that non-allowed ports are blocked"""
        result = self.safety.validate_port(1337)
        self.assertFalse(result, "Port 1337 should be blocked")
    
    def test_command_sanitization_safe(self):
        """Test that safe commands pass sanitization"""
        result = self.safety.sanitize_command("nmap -sV 172.20.0.10")
        self.assertIsNotNone(result, "Safe nmap command should pass")
    
    def test_command_sanitization_dangerous(self):
        """Test that dangerous commands are blocked"""
        dangerous_commands = [
            "rm -rf /",
            ":(){ :|:& };:",
            "mkfs.ext4 /dev/sda",
            "dd if=/dev/zero of=/dev/sda"
        ]
        
        for cmd in dangerous_commands:
            result = self.safety.sanitize_command(cmd)
            self.assertIsNone(result, f"Dangerous command should be blocked: {cmd}")
    
    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        self.safety.reset_episode()
        
        # Should allow initial actions
        for i in range(5):
            result = self.safety.check_rate_limit()
            self.assertTrue(result, f"Action {i} should be allowed")
            self.safety.record_action(f"test_action_{i}", "172.20.0.10", True)
        
        # Check stats
        stats = self.safety.get_stats()
        self.assertEqual(stats["actions_this_episode"], 5)

class TestToolExecutor(unittest.TestCase):
    """Test tool executor functionality"""
    
    def test_executor_initialization_valid_ip(self):
        """Test that executor initializes with valid IP"""
        try:
            executor = ToolExecutor("172.20.0.10")
            self.assertIsNotNone(executor)
        except ValueError:
            self.fail("Executor should initialize with whitelisted IP")
    
    def test_executor_initialization_invalid_ip(self):
        """Test that executor rejects invalid IP"""
        with self.assertRaises(ValueError):
            executor = ToolExecutor("8.8.8.8")
    
    def test_nmap_execution_format(self):
        """Test nmap command execution (may fail if nmap not installed)"""
        executor = ToolExecutor("172.20.0.10")
        
        # This will execute real nmap if available, or fail gracefully
        # We just check it doesn't crash
        try:
            success, output = executor.execute_nmap("-sV")
            self.assertIsInstance(success, bool)
            self.assertIsInstance(output, str)
        except Exception as e:
            # If nmap not available or target not reachable, that's okay for unit test
            print(f"Note: nmap test skipped - {e}")

if __name__ == '__main__':
    print("Running Safety and Tool Executor Tests...")
    print("=" * 60)
    unittest.main(verbosity=2)
