
import gymnasium as gym
from gymnasium import spaces
import numpy as np
import random
from typing import Dict, List, Tuple

class AdvancedKillChainEnv(gym.Env):
    """
    Advanced Red Team Environment (2025 Edition)
    
    Features:
    - Multi-OS Support (Linux, Windows, macOS)
    - Mitre ATT&CK Kill Chain Phases
    - Business Logic Reward System
    - Stealth & Noise Tracking
    """
    
    metadata = {'render_modes': ['human']}

    def __init__(self):
        super(AdvancedKillChainEnv, self).__init__()
        
        # --- CONFIGURATION ---
        self.os_types = ["Linux", "Windows", "macOS"]
        self.current_os = "Linux"
        
        # --- ACTION SPACE (The 2025 Arsenal) ---
        # We group actions by Kill Chain phase for logic, but the agent sees a flat list.
        self.actions = [
            # RECON (0-4)
            "Autonomous_Swarm_Recon",       # 0: Passive AI Recon
            "MultiCloud_Shadow_API_Enum",   # 1: Cloud Bucket/Metadata
            "IPv6_Ghost_Scan",              # 2: Low-rate Nmap
            "Botnet_Distributed_Scan",      # 3: Masscan (Noisy)
            "Deepfake_Voice_Phishing",      # 4: Email Vectors
            
            # INITIAL ACCESS (5-9)
            "ZeroDay_LLM_Injection",        # 5: Modern Web Exploit
            "Quantum_VPN_Decryption",       # 6: VPN Vuln
            "Biometric_Spoofing_Auth",      # 7: Credential Stuffing
            "NFC_Clone_Attack",             # 8: Physical/Local
            "AI_Model_Poisoning",           # 9: Dependency Confusion
            
            # EXECUTION (10-14)
            "PowerShell_Reflective_Load",   # 10: Windows LOLBin
            "eBPF_Stealth_Shell",           # 11: Linux Standard
            "MacOS_TCC_Bypass",             # 12: macOS Specific
            "Container_Escape_K8s",         # 13: Sudo/Perm abuse
            "WASM_Heap_Overflow",           # 14: Client-side
            
            # PERSISTENCE (15-19)
            "UEFI_Bootkit_Implant",         # 15: Windows Persistence
            "Systemd_Service_Masquerade",   # 16: Linux Persistence
            "MacOS_Kext_Injection",         # 17: macOS Persistence
            "Hypervisor_Level_Persistence", # 18: Windows Advanced
            "Hardware_Firmware_Backdoor",   # 19: Linux Kernel Stealth
            
            # PRIVILEGE ESCALATION (20-24)
            "AD_Kerberos_Ticket_Forge",     # 20: Windows Enum
            "Linux_Kernel_Race_Condition",  # 21: Linux Enum
            "ZeroDay_Kernel_PrivEsc",       # 22: Linux Kernel
            "Windows_Hello_Bypass",         # 23: Windows Service
            "Secure_Enclave_Extraction",    # 24: macOS Creds
            
            # EXFILTRATION & IMPACT (25-29) - BUSINESS LOGIC
            "Exfil_Vector_Embeddings_DB",   # 25: $$$ High Value
            "Exfil_Executive_Voice_Prints", # 26: $$ Medium Value
            "Quantum_Ransomware_Crypt",     # 27: $$$ High Impact (Noisy)
            "Deepfake_CEO_Broadcast",       # 28: $ Low Value (Noisy)
            "Blockchain_Log_Poisoning",     # 29: Stealth Restore
        ]
        
        self.action_space = spaces.Discrete(len(self.actions))
        
        # --- OBSERVATION SPACE ---
        # We use a Dict space for structured "Human-like" understanding
        self.observation_space = spaces.Dict({
            "os_type": spaces.Discrete(3),          # 0:Linux, 1:Win, 2:Mac
            "kill_chain_phase": spaces.Discrete(7), # 0:Recon -> 6:Impact
            "stealth_meter": spaces.Box(low=0, high=100, shape=(1,), dtype=np.float32), # 100=Invisible, 0=Detected
            "access_level": spaces.Discrete(3),     # 0:None, 1:User, 2:Root/Admin
            "vulns_known": spaces.MultiBinary(5),   # Bitmask of known vulns
            "business_value_found": spaces.Box(low=0, high=1000, shape=(1,), dtype=np.float32)
        })
        
        # Internal State
        self.state = {}
        self.max_steps = 100
        self.current_step = 0

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Randomize Target
        self.current_os_idx = random.randint(0, 2)
        self.current_os = self.os_types[self.current_os_idx]
        
        # Reset State
        self.state = {
            "os_type": self.current_os_idx,
            "kill_chain_phase": 0, # Recon
            "stealth_meter": 100.0,
            "access_level": 0,
            "vulns_known": np.zeros(5, dtype=np.int8),
            "business_value_found": 0.0
        }
        
        self.current_step = 0
        return self._get_obs(), {}

    def _get_obs(self):
        return {
            "os_type": self.state["os_type"],
            "kill_chain_phase": self.state["kill_chain_phase"],
            "stealth_meter": np.array([self.state["stealth_meter"]], dtype=np.float32),
            "access_level": self.state["access_level"],
            "vulns_known": self.state["vulns_known"],
            "business_value_found": np.array([self.state["business_value_found"]], dtype=np.float32)
        }

    def step(self, action_id):
        self.current_step += 1
        action_name = self.actions[action_id]
        
        # Base Reward (Time Penalty)
        reward = -0.1 
        done = False
        truncated = False
        info = {"action": action_name, "os": self.current_os}
        
        # --- CURIOSITY (Intrinsic Motivation) ---
        # Simple Count-Based Exploration
        # We hash the state to track visits
        state_hash = hash((
            self.state["os_type"],
            self.state["kill_chain_phase"],
            self.state["access_level"],
            tuple(self.state["vulns_known"]),
            self.state["stealth_meter"] // 10 # Discretize stealth for hashing
        ))
        
        if not hasattr(self, "state_visits"):
            self.state_visits = {}
            
        visit_count = self.state_visits.get(state_hash, 0) + 1
        self.state_visits[state_hash] = visit_count
        
        # Intrinsic Reward: Higher for novel states
        intrinsic_reward = 1.0 / np.sqrt(visit_count)
        reward += intrinsic_reward

        # --- LOGIC ENGINE ---
        
        # 1. OS Mismatch Check
        if "PowerShell" in action_name and self.current_os != "Windows":
            reward -= 5.0 # Fail command
            info["output"] = "FAIL: PowerShell not available on " + self.current_os
            return self._get_obs(), reward, done, truncated, info
            
        if "eBPF" in action_name and self.current_os == "Windows":
            reward -= 5.0 # Fail command
            info["output"] = "FAIL: eBPF not available on " + self.current_os
            return self._get_obs(), reward, done, truncated, info

        # 2. Kill Chain Progression Logic
        
        # RECON
        if action_id <= 4:
            if self.state["kill_chain_phase"] == 0:
                self.state["kill_chain_phase"] = 1 # Advance
                reward += 1.0 # Small progress reward
                if "Botnet" in action_name:
                    self.state["stealth_meter"] -= 20
                    info["output"] = "Recon successful but noisy (Botnet)."
                else:
                    info["output"] = "Stealth recon successful."
            else:
                info["output"] = "Recon already done."

        # INITIAL ACCESS
        elif 5 <= action_id <= 9:
            if self.state["kill_chain_phase"] >= 1 and self.state["access_level"] == 0:
                if random.random() > 0.4:
                    self.state["access_level"] = 1
                    self.state["kill_chain_phase"] = 2
                    reward += 10.0 # Gain Shell
                    info["output"] = "Initial Access Gained! (+10)"
                else:
                    self.state["stealth_meter"] -= 10
                    info["output"] = "Exploit failed."
            else:
                reward -= 5.0 # Fail command
                info["output"] = "Cannot exploit without recon or already have access."

        # EXECUTION & PERSISTENCE
        elif 10 <= action_id <= 19:
            if self.state["access_level"] >= 1:
                # Actions 15-19 are Persistence
                if action_id >= 15:
                     reward += 5.0
                     info["output"] = "Persistence established."
                else:
                     info["output"] = "Command executed."
            else:
                reward -= 5.0 # Fail command
                info["output"] = "No access to execute commands."

        # PRIVILEGE ESCALATION
        elif 20 <= action_id <= 24:
            if self.state["access_level"] == 1:
                if random.random() > 0.5:
                    self.state["access_level"] = 2 # Admin/Root
                    reward += 50.0 # Escalate to Root
                    info["output"] = "Privilege Escalation Successful! (ROOT/ADMIN) (+50)"
                else:
                    self.state["stealth_meter"] -= 15
                    info["output"] = "PrivEsc failed."
            else:
                info["output"] = "Need user access first."

        # EXFILTRATION & IMPACT
        elif 25 <= action_id <= 29:
            if self.state["access_level"] >= 1:
                if "Vector_Embeddings" in action_name:
                    if self.state["access_level"] == 2:
                        reward += 100.0 # Find Flag / High Value
                        self.state["business_value_found"] += 100
                        info["output"] = "CRITICAL: Vector Embeddings DB Exfiltrated! (+100)"
                        done = True # Mission Complete
                    else:
                        reward -= 5.0
                        info["output"] = "Need Root/Admin to access Database."
                
                elif "Voice_Prints" in action_name:
                    reward += 30.0
                    self.state["business_value_found"] += 30
                    info["output"] = "Executive Voice Prints exfiltrated."
                    
                elif "Ransomware" in action_name:
                    reward += 50.0
                    self.state["stealth_meter"] = 0 # Very Noisy
                    info["output"] = "Quantum Ransomware deployed."
                    done = True
            else:
                info["output"] = "No access to exfiltrate."

        # Stealth Penalty (Trigger Detection)
        if self.state["stealth_meter"] <= 0:
            reward -= 20.0 # Trigger detection
            done = True
            info["output"] = "DETECTED! Mission Failed. (-20)"

        # Truncate
        if self.current_step >= self.max_steps:
            reward -= 5.0 # Timeout
            truncated = True

        return self._get_obs(), reward, done, truncated, info
