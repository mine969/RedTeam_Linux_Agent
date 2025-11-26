import os
import time
import numpy as np
import torch
from sb3_contrib import RecurrentPPO
from env.advanced_env import AdvancedKillChainEnv

def run_smart_agent():
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
    # We need to specify the device to ensure it runs on the correct hardware
    model = RecurrentPPO.load(model_path, device=device)
    
    # Initialize Environment
    print("🌍 Initializing Environment...")
    env = AdvancedKillChainEnv()
    
    # --- EVALUATION LOOP ---
    print("\n🎬 Starting Evaluation Episode...")
    obs, _ = env.reset()
    
    # LSTM states
    # RecurrentPPO uses LSTM states, we need to initialize them
    # For a single environment, num_envs = 1
    lstm_states = None
    num_envs = 1
    episode_starts = np.ones((num_envs,), dtype=bool)
    
    done = False
    total_reward = 0
    step_count = 0
    
    try:
        while not done:
            # Predict action
            # We must pass the LSTM state and episode start flags
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
    run_smart_agent()
