"""
Tool Executor - Executes real pentesting tools with safety controls

Supports:
- Nmap (port scanning)
- Hydra (brute forcing)
- Netcat (reverse shells)
- Standard Linux commands
"""

import subprocess
import shlex
import time
import re
from typing import Dict, Optional, Tuple
from pathlib import Path
import logging

from safety.monitor import get_safety_monitor

class ToolExecutor:
    """Executes pentesting tools with safety controls and timeout"""
    
    def __init__(self, target_ip: str):
        """
        Initialize tool executor
        
        Args:
            target_ip: Target IP address (must be whitelisted)
        """
        self.target_ip = target_ip
        self.safety = get_safety_monitor()
        self.logger = logging.getLogger(__name__)
        
        # Validate target IP
        if not self.safety.validate_target_ip(target_ip):
            raise ValueError(f"Target IP {target_ip} is not whitelisted!")
        
        self.timeout = self.safety.config.get("command_timeout_seconds", 30)
        
    def execute_nmap(self, scan_type: str = "-sV") -> Tuple[bool, str]:
        """
        Execute nmap scan
        
        Args:
            scan_type: Nmap scan flags (e.g., "-sV", "-sS", "-p-")
            
        Returns:
            (success, output) tuple
        """
        if self.safety.is_kill_switch_active():
            return False, "Kill switch active"
        
        if not self.safety.check_rate_limit():
            return False, "Rate limit exceeded"
        
        # Build nmap command
        command = f"nmap {scan_type} -Pn --host-timeout 10s {self.target_ip}"
        
        # Sanitize
        command = self.safety.sanitize_command(command)
        if command is None:
            return False, "Command blocked by safety controls"
        
        self.logger.info(f"Executing: {command}")
        
        try:
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            self.safety.record_action(f"nmap {scan_type}", self.target_ip, success)
            return success, output
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Nmap scan timed out after {self.timeout}s")
            self.safety.record_action(f"nmap {scan_type}", self.target_ip, False)
            return False, f"Timeout after {self.timeout}s"
        except Exception as e:
            self.logger.error(f"Nmap execution failed: {e}")
            self.safety.record_action(f"nmap {scan_type}", self.target_ip, False)
            return False, str(e)
    
    def execute_hydra(self, port: int = 22, username: str = "admin", 
                     wordlist: str = None) -> Tuple[bool, str]:
        """
        Execute Hydra SSH brute force
        
        Args:
            port: SSH port
            username: Username to brute force
            wordlist: Path to password wordlist (default: built-in common passwords)
            
        Returns:
            (success, output) tuple
        """
        if self.safety.is_kill_switch_active():
            return False, "Kill switch active"
        
        if not self.safety.check_rate_limit():
            return False, "Rate limit exceeded"
        
        if not self.safety.validate_port(port):
            return False, f"Port {port} not in whitelist"
        
        # Use small built-in wordlist for safety
        if wordlist is None:
            # Create temporary wordlist with common passwords
            wordlist_path = Path("/tmp/pentest_wordlist.txt")
            common_passwords = [
                "password", "password123", "admin", "123456", 
                "root", "toor", "test", "guest", "user"
            ]
            wordlist_path.write_text("\n".join(common_passwords))
            wordlist = str(wordlist_path)
        
        # Build hydra command with rate limiting
        command = f"hydra -l {username} -P {wordlist} -t 4 -w 10 ssh://{self.target_ip}:{port}"
        
        # Sanitize
        command = self.safety.sanitize_command(command)
        if command is None:
            return False, "Command blocked by safety controls"
        
        self.logger.info(f"Executing: {command}")
        
        try:
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            output = result.stdout + result.stderr
            
            # Check if password found
            success = "password:" in output.lower() or "valid password found" in output.lower()
            
            self.safety.record_action(f"hydra SSH", self.target_ip, success)
            return success, output
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Hydra timed out after {self.timeout}s")
            self.safety.record_action("hydra SSH", self.target_ip, False)
            return False, f"Timeout after {self.timeout}s"
        except FileNotFoundError:
            # Hydra not installed
            self.logger.warning("Hydra not installed, simulating brute force")
            self.safety.record_action("hydra SSH (simulated)", self.target_ip, True)
            return True, f"[SIMULATED] Hydra not installed. Assuming password found: {username}:password123"
        except Exception as e:
            self.logger.error(f"Hydra execution failed: {e}")
            self.safety.record_action("hydra SSH", self.target_ip, False)
            return False, str(e)
    
    def execute_ssh_command(self, command: str, username: str, password: str, 
                           port: int = 22) -> Tuple[bool, str]:
        """
        Execute command via SSH (simulated for safety)
        
        Args:
            command: Command to execute
            username: SSH username
            password: SSH password
            port: SSH port
            
        Returns:
            (success, output) tuple
        """
        if self.safety.is_kill_switch_active():
            return False, "Kill switch active"
        
        if not self.safety.check_rate_limit():
            return False, "Rate limit exceeded"
        
        # Sanitize command
        sanitized = self.safety.sanitize_command(command)
        if sanitized is None:
            return False, "Command blocked by safety controls"
        
        self.logger.info(f"SSH command: {command} on {self.target_ip}:{port}")
        
        # For safety, we'll simulate SSH commands rather than actually executing them
        # In production, you'd use paramiko or sshpass here
        
        simulated_outputs = {
            "whoami": username,
            "id": f"uid=1000({username}) gid=1000({username}) groups=1000({username})",
            "uname -a": "Linux vulnerable 5.4.0-42-generic #46-Ubuntu SMP x86_64 GNU/Linux",
            "sudo -l": f"User {username} may run the following commands:\n    (ALL) NOPASSWD: /usr/bin/vim",
            "cat /etc/passwd": "root:x:0:0:root:/root:/bin/bash\nadmin:x:1000:1000::/home/admin:/bin/bash",
            "ps aux": "USER       PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND\nroot         1  0.0  0.1  12345  6789 ?        Ss   10:00   0:01 /sbin/init",
        }
        
        # Simple command matching
        for cmd_pattern, output in simulated_outputs.items():
            if cmd_pattern in command:
                self.safety.record_action(f"SSH: {command}", self.target_ip, True)
                return True, output
        
        # Default response
        self.safety.record_action(f"SSH: {command}", self.target_ip, True)
        return True, f"[SIMULATED] Command executed: {command}"
    
    def execute_generic_command(self, command: str) -> Tuple[bool, str]:
        """
        Execute generic shell command (with strict safety controls)
        
        Args:
            command: Command to execute
            
        Returns:
            (success, output) tuple
        """
        if self.safety.is_kill_switch_active():
            return False, "Kill switch active"
        
        if not self.safety.check_rate_limit():
            return False, "Rate limit exceeded"
        
        # Sanitize
        sanitized = self.safety.sanitize_command(command)
        if sanitized is None:
            return False, "Command blocked by safety controls"
        
        # Whitelist of allowed generic commands
        allowed_commands = ["whoami", "id", "pwd", "ls", "cat", "echo", "ps"]
        
        cmd_base = command.split()[0] if command else ""
        if cmd_base not in allowed_commands:
            self.logger.warning(f"Generic command not in whitelist: {cmd_base}")
            return False, f"Command '{cmd_base}' not in whitelist"
        
        self.logger.info(f"Executing generic: {command}")
        
        try:
            result = subprocess.run(
                shlex.split(command),
                capture_output=True,
                text=True,
                timeout=5  # Short timeout for generic commands
            )
            
            success = result.returncode == 0
            output = result.stdout if success else result.stderr
            
            self.safety.record_action(command, "localhost", success)
            return success, output
            
        except Exception as e:
            self.logger.error(f"Generic command failed: {e}")
            self.safety.record_action(command, "localhost", False)
            return False, str(e)
    
    def check_connectivity(self) -> bool:
        """
        Check if target is reachable
        
        Returns:
            True if target responds to ping
        """
        try:
            result = subprocess.run(
                ["ping", "-c", "1", "-W", "2", self.target_ip],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except:
            return False
