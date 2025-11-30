"""
Multi-Agent Chain Adapter for RedTeam Linux Agent
-------------------------------------------------
This script acts as the interface for the Kill Chain Controller.
It accepts a target from the Upstream Agent (OSINT) and returns results.

Usage:
    python chain_adapter.py --input '{"target_ip": "10.10.10.5", "os_type": "Linux", "scope": "strict"}'

Output (JSON):
    {
        "status": "success",
        "access_level": "root",
        "findings": ["Weak SSH", "Dirty Cow"],
        "next_stage_recommendation": "Post-Exploitation"
    }
"""
import sys
import json
import argparse
import torch
import numpy as np
from sb3_contrib import RecurrentPPO
from env.advanced_env import AdvancedKillChainEnv

def run_chain_step(input_data):
    target_ip = input_data.get("target_ip", "127.0.0.1")
    os_type = input_data.get("os_type", "Linux")
    
    print(f"🔗 CHAIN LINK ACTIVE: Target {target_ip} ({os_type})")
    
    # Load Model
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model_path = "redteam_lstm_final.zip"
    
    try:
        model = RecurrentPPO.load(model_path, device=device)
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to load model: {str(e)}"
        }
    
    # Init Env with specific target
    env = AdvancedKillChainEnv()
    obs, _ = env.reset(options={"os_type": os_type, "target_ip": target_ip})
    
    # Run Episode
    done = False
    lstm_states = None
    episode_starts = np.ones((1,), dtype=bool)
    
    findings = []
    max_access = "none"
    total_reward = 0
    
    while not done:
        action, lstm_states = model.predict(obs, state=lstm_states, episode_start=episode_starts, deterministic=True)
        obs, reward, terminated, truncated, info = env.step(action)
        done = terminated or truncated
        episode_starts = np.array([done])
        
        total_reward += reward
        
        # Capture Findings
        output = info.get('output', '')
        if "SUCCESS" in output or "found" in output.lower():
            findings.append(output)
            
        if "root" in output.lower() or "admin" in output.lower():
            max_access = "root"
        elif "user" in output.lower() and max_access == "none":
            max_access = "user"
            
    # Result Construction
    result = {
        "agent": "RedTeam_Linux_Agent",
        "target_ip": target_ip,
        "status": "completed",
        "total_reward": float(total_reward),
        "max_access_level": max_access,
        "findings": list(set(findings)), # Unique findings
        "success": bool(total_reward > 0)
    }
    
    return result

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="JSON input string")
    args = parser.parse_args()
    
    if args.input:
        try:
            data = json.loads(args.input)
            result = run_chain_step(data)
            print(json.dumps(result, indent=2))
        except json.JSONDecodeError:
            print(json.dumps({"status": "error", "message": "Invalid JSON input"}))
    else:
        # Test Mode
        test_input = {"target_ip": "192.168.1.100", "os_type": "Linux"}
        result = run_chain_step(test_input)
        print(json.dumps(result, indent=2))
