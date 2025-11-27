"""
Safety Monitor for Real Pentesting Agent

Enforces security controls to prevent misuse:
- IP whitelist validation
- Rate limiting
- Command sanitization
- Audit logging
"""

import json
import time
import ipaddress
import logging
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timedelta

class SafetyMonitor:
    """Monitors and enforces safety controls for pentesting actions"""
    
    def __init__(self, config_path: str = "safety/whitelist.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Rate limiting tracking
        self.action_timestamps: List[float] = []
        self.episode_action_count = 0
        
        # Setup logging
        self._setup_logging()
        
        # Emergency kill switch
        self.kill_switch_active = False
        
    def _load_config(self) -> Dict:
        """Load safety configuration from JSON file"""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Safety config not found: {self.config_path}")
        
        with open(self.config_path, 'r') as f:
            return json.load(f)
    
    def _setup_logging(self):
        """Setup audit logging"""
        log_dir = Path("logs/audit")
        log_dir.mkdir(parents=True, exist_ok=True)
        
        log_file = log_dir / f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        self.logger.info("Safety Monitor initialized")
    
    def validate_target_ip(self, target_ip: str) -> bool:
        """
        Validate that target IP is in whitelist
        
        Args:
            target_ip: IP address to validate
            
        Returns:
            True if IP is allowed, False otherwise
        """
        try:
            target = ipaddress.ip_address(target_ip)
            
            # Check explicit allowed targets
            if target_ip in self.config.get("allowed_targets", []):
                self.logger.info(f"✓ Target IP {target_ip} is explicitly whitelisted")
                return True
            
            # Check IP ranges
            for ip_range in self.config.get("allowed_ip_ranges", []):
                network = ipaddress.ip_network(ip_range)
                if target in network:
                    self.logger.info(f"✓ Target IP {target_ip} is in allowed range {ip_range}")
                    return True
            
            self.logger.warning(f"✗ Target IP {target_ip} is NOT in whitelist - BLOCKED")
            return False
            
        except ValueError as e:
            self.logger.error(f"Invalid IP address: {target_ip} - {e}")
            return False
    
    def validate_port(self, port: int) -> bool:
        """Validate that port is in allowed list"""
        allowed_ports = self.config.get("allowed_ports", [])
        
        if port in allowed_ports:
            return True
        
        self.logger.warning(f"✗ Port {port} is not in allowed list - BLOCKED")
        return False
    
    def check_rate_limit(self) -> bool:
        """
        Check if action rate limit is exceeded
        
        Returns:
            True if action is allowed, False if rate limit exceeded
        """
        current_time = time.time()
        max_per_minute = self.config.get("max_actions_per_minute", 30)
        
        # Remove timestamps older than 1 minute
        self.action_timestamps = [
            ts for ts in self.action_timestamps 
            if current_time - ts < 60
        ]
        
        # Check rate limit
        if len(self.action_timestamps) >= max_per_minute:
            self.logger.warning(f"✗ Rate limit exceeded: {len(self.action_timestamps)}/{max_per_minute} actions per minute")
            return False
        
        # Check episode limit
        max_per_episode = self.config.get("max_actions_per_episode", 100)
        if self.episode_action_count >= max_per_episode:
            self.logger.warning(f"✗ Episode action limit exceeded: {self.episode_action_count}/{max_per_episode}")
            return False
        
        return True
    
    def record_action(self, action: str, target: str, success: bool):
        """
        Record an action in audit log
        
        Args:
            action: Action name/command
            target: Target IP/host
            success: Whether action succeeded
        """
        current_time = time.time()
        self.action_timestamps.append(current_time)
        self.episode_action_count += 1
        
        if self.config.get("log_all_commands", True):
            status = "SUCCESS" if success else "FAILED"
            self.logger.info(f"[{status}] Action: {action} | Target: {target}")
    
    def sanitize_command(self, command: str) -> Optional[str]:
        """
        Sanitize command to prevent dangerous operations
        
        Args:
            command: Command to sanitize
            
        Returns:
            Sanitized command if safe, None if blocked
        """
        # Check blocked commands
        blocked = self.config.get("blocked_commands", [])
        for blocked_cmd in blocked:
            if blocked_cmd in command:
                self.logger.error(f"✗ BLOCKED dangerous command: {command}")
                return None
        
        # Additional safety checks
        dangerous_patterns = [
            "rm -rf /",
            "mkfs",
            "dd if=/dev/zero",
            ":(){ :|:& };:",  # Fork bomb
            "> /dev/sda",
            "chmod -R 777 /",
        ]
        
        for pattern in dangerous_patterns:
            if pattern in command:
                self.logger.error(f"✗ BLOCKED dangerous pattern in command: {command}")
                return None
        
        return command
    
    def activate_kill_switch(self, reason: str):
        """
        Activate emergency kill switch
        
        Args:
            reason: Reason for activation
        """
        self.kill_switch_active = True
        self.logger.critical(f"🚨 EMERGENCY KILL SWITCH ACTIVATED: {reason}")
    
    def is_kill_switch_active(self) -> bool:
        """Check if kill switch is active"""
        return self.kill_switch_active
    
    def reset_episode(self):
        """Reset episode-specific counters"""
        self.episode_action_count = 0
        self.logger.info("Episode counters reset")
    
    def get_stats(self) -> Dict:
        """Get current safety statistics"""
        return {
            "actions_last_minute": len(self.action_timestamps),
            "actions_this_episode": self.episode_action_count,
            "kill_switch_active": self.kill_switch_active,
            "max_actions_per_minute": self.config.get("max_actions_per_minute"),
            "max_actions_per_episode": self.config.get("max_actions_per_episode")
        }


# Singleton instance
_monitor_instance = None

def get_safety_monitor() -> SafetyMonitor:
    """Get singleton safety monitor instance"""
    global _monitor_instance
    if _monitor_instance is None:
        _monitor_instance = SafetyMonitor()
    return _monitor_instance
