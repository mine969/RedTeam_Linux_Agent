"""
Run Real Agent - Execute Pentest against Docker Target

Loads trained model and executes real pentesting actions.
Generates report of findings.
"""

import os
import time
import json
import argparse
import gymnasium as gym
from stable_baselines3 import PPO
from datetime import datetime

from env.real_linux_env import RealLinuxEnv
from safety.monitor import get_safety_monitor

def generate_report(env, info_history, reward_history):
    """Generate simple JSON/Markdown report of findings"""
    report_dir = "reports/"
    os.makedirs(report_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report = {
        "target": env.target_ip,
        "timestamp": timestamp,
        "total_steps": len(info_history),
        "total_reward": sum(reward_history),
        "findings": {
            "open_ports": env.discovered_ports,
            "services": env.discovered_services,
            "credentials": env.credentials,
            "access_level": ["None", "User", "Root"][env.access_level],
            "flags_found": env.access_level == 2
        },
        "action_log": info_history
    }
    
    # Save JSON
    json_path = f"{report_dir}/report_{timestamp}.json"
    with open(json_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    # Save Markdown Summary
    md_path = f"{report_dir}/report_{timestamp}.md"
    with open(md_path, 'w') as f:
        f.write(f"# Pentest Report - {env.target_ip}\n\n")
        f.write(f"**Date:** {timestamp}\n")
        f.write(f"**Status:** {'✅ SUCCESS' if env.access_level == 2 else '⚠️ PARTIAL'}\n\n")
        
        f.write("## 🔍 Findings\n")
        f.write(f"- **Access Level:** {report['findings']['access_level']}\n")
        f.write(f"- **Open Ports:** {report['findings']['open_ports']}\n")
        f.write(f"- **Credentials:** {len(report['findings']['credentials'])} found\n")
        
        if report['findings']['credentials']:
            f.write("\n### Credentials Discovered\n")
            for user, password in report['findings']['credentials'].items():
                f.write(f"- `{user}:{password}`\n")
        
        f.write("\n## 📜 Action Log\n")
        for i, info in enumerate(info_history):
            icon = "✅" if info.get("success", True) else "❌"
            f.write(f"{i+1}. {icon} **{info['action']}**: {info.get('output', '').splitlines()[0]}\n")
            
    print(f"\n📄 Report generated: {md_path}")

def run_real_agent(target_ip="172.20.0.10", model_path="redteam_real_v1.zip"):
    print(f"🚀 Initializing Real Pentest against {target_ip}...")
    
    # Check Model
    if not os.path.exists(model_path):
        print(f"⚠️ Model {model_path} not found. Using random agent for testing.")
        model = None
    else:
        print(f"📂 Loading model: {model_path}")
        model = PPO.load(model_path)
    
    # Initialize Environment
    try:
        env = RealLinuxEnv(target_ip=target_ip)
    except ValueError as e:
        print(f"❌ Error: {e}")
        return
        
    obs, _ = env.reset()
    
    done = False
    total_reward = 0
    info_history = []
    reward_history = []
    
    print("\n🎬 Starting Episode...")
    
    try:
        while not done:
            if model:
                action, _ = model.predict(obs, deterministic=True)
            else:
                action = env.action_space.sample() # Random for testing
                
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            total_reward += reward
            info_history.append(info)
            reward_history.append(reward)
            
            # Print Progress
            step_num = len(info_history)
            print(f"Step {step_num}: {info['action']}")
            print(f"   └── {info.get('output', '').splitlines()[0]}")
            
            if done:
                print(f"\n🏁 Episode Finished. Total Reward: {total_reward}")
                
    except KeyboardInterrupt:
        print("\n🛑 Execution interrupted")
        
    finally:
        generate_report(env, info_history, reward_history)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Real Pentest Agent")
    parser.add_argument("--target", type=str, default="172.20.0.10", help="Target IP address")
    parser.add_argument("--model", type=str, default="redteam_real_v1.zip", help="Path to trained model")
    
    args = parser.parse_args()
    run_real_agent(args.target, args.model)
