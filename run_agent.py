import os
import time
import argparse
import numpy as np
import torch
from sb3_contrib import RecurrentPPO
from env.advanced_env import AdvancedKillChainEnv

def run_smart_agent(target_ip=None, os_type=None):
    print("🚀 Initializing Red Team Agent Runner...")
    
    # Check GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Hardware Acceleration: {device.type.upper()}")

    model_path = "redteam_lstm_final.zip"
    if not os.path.exists(model_path):
        print(f"❌ Error: Model file '{model_path}' not found. Please train the agent first.")
        return

    print(f"📂 Loading Model: {model_path}")
    
    # Load Model
    model = RecurrentPPO.load(model_path, device=device)
    
    # Initialize Environment
    print("🌍 Initializing Environment...")
    env = AdvancedKillChainEnv()
    
    # Configure Target
    options = {}
    if target_ip:
        options['target_ip'] = target_ip
    if os_type:
        options['os_type'] = os_type
        
    print(f"🎯 Target: {options.get('target_ip', '127.0.0.1')} ({options.get('os_type', 'Random')})")
    
    # --- EVALUATION LOOP ---
    print("\n🎬 Starting Evaluation Episode...")
    obs, _ = env.reset(options=options)
    
    # LSTM states
    lstm_states = None
    num_envs = 1
    episode_starts = np.ones((num_envs,), dtype=bool)
    
    done = False
    total_reward = 0
    step_count = 0
    
    try:
        while not done:
            # Predict action
            action, lstm_states = model.predict(
                obs, 
                state=lstm_states, 
                episode_start=episode_starts,
                deterministic=True
            )
            
            # Step environment
            obs, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            episode_starts = np.array([done])
            
            total_reward += reward
            step_count += 1
            
            # Print Step Info
            print(f"Step {step_count}: Action: {info['action']}")
            print(f"   └── Output: {info.get('output', '')}")
            
            # Optional: Add a small delay for readability
            time.sleep(0.5)
            
        print("-" * 50)
        print(f"🏁 Episode Finished.")
        print(f"💰 Total Reward: {total_reward}")
        print(f"👣 Total Steps: {step_count}")

    except KeyboardInterrupt:
        print("\n🛑 Execution interrupted by user.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--target_ip", type=str, help="Target IP Address")
    parser.add_argument("--os_type", type=str, help="Target OS (Linux, Windows, macOS)")
    args = parser.parse_args()
    
    run_smart_agent(target_ip=args.target_ip, os_type=args.os_type)
