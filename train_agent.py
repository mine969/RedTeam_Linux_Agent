
import os
import gymnasium as gym
from stable_baselines3 import PPO
from sb3_contrib import RecurrentPPO
from stable_baselines3.common.vec_env import DummyVecEnv, SubprocVecEnv
from stable_baselines3.common.callbacks import CheckpointCallback
from env.advanced_env import AdvancedKillChainEnv

import torch

def train_smart_agent():
    print("Initializing Super-Smart Red Team Agent (2025 Edition)...")
    
    # Check GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Hardware Acceleration: {device.type.upper()} (Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'None'})")
    if device.type == 'cpu':
        print("WARNING: Training on CPU will be slow!")
    else:
        print("GPU Detected & Enabled for Training.")
    
    # Create Log Dir
    log_dir = "logs/"
    os.makedirs(log_dir, exist_ok=True)
    
    # Initialize Environment
    # We use DummyVecEnv for simple sequential execution, or SubprocVecEnv for parallel
    env = DummyVecEnv([lambda: AdvancedKillChainEnv()])
    
    # Initialize Recurrent PPO Agent
    # MultiInputLstmPolicy: Handles Dict observation spaces with LSTM
    model = RecurrentPPO(
        "MultiInputLstmPolicy",
        env,
        verbose=1,
        learning_rate=0.0003,
        n_steps=128,
        batch_size=64,
        n_epochs=10,
        gamma=0.99,
        gae_lambda=0.95,
        clip_range=0.2,
        ent_coef=0.01, # Entropy coefficient to encourage exploration
        tensorboard_log=log_dir,
        policy_kwargs=dict(
            lstm_hidden_size=256,
            n_lstm_layers=2,
            enable_critic_lstm=True,
        ),
    )
    
    print("Starting Training with Curriculum & Business Logic...")
    print("   - Algorithm: Recurrent PPO (LSTM)")
    print("   - Target OS: Multi-OS (Linux, Windows, macOS)")
    print("   - Logic: Mitre ATT&CK Kill Chain")
    
    # Train
    # In a real scenario, this would be 1,000,000+ steps
    # For demo/initial setup, we run 10,000
    total_timesteps = 10000
    
    checkpoint_callback = CheckpointCallback(
        save_freq=1000,
        save_path='./checkpoints/',
        name_prefix='redteam_lstm_model'
    )
    
    model.learn(
        total_timesteps=total_timesteps, 
        callback=checkpoint_callback,
        progress_bar=True
    )
    
    print("Training Complete!")
    
    # Save Final Model
    model.save("redteam_lstm_final")
    print("Model saved to redteam_lstm_final.zip")

    # --- EVALUATION ---
    print("\nRunning Evaluation Episode...")
    obs = env.reset()
    # LSTM states
    lstm_states = None
    num_envs = 1
    # Episode start signals are used to reset the lstm states
    episode_starts = np.ones((num_envs,), dtype=bool)
    
    done = False
    total_reward = 0
    
    while not done:
        action, lstm_states = model.predict(
            obs, 
            state=lstm_states, 
            episode_start=episode_starts,
            deterministic=True
        )
        obs, rewards, dones, infos = env.step(action)
        episode_starts = dones
        total_reward += rewards[0]
        
        print(f"Action: {infos[0]['action']} | Output: {infos[0].get('output', '')}")
        
        if dones[0]:
            done = True
            print(f"Episode Finished. Total Reward: {total_reward}")

if __name__ == "__main__":
    train_smart_agent()
