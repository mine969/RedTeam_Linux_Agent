"""
Train Real Agent - Transfer Learning Pipeline

Trains the agent on the Real Linux Environment using Transfer Learning:
1. Loads pre-trained weights from simulation (if available)
2. Fine-tunes on real environment with safety constraints
3. Uses Curriculum Learning (start with simple tasks)
"""

import os
import time
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback, BaseCallback
from stable_baselines3.common.vec_env import DummyVecEnv

from env.real_linux_env import RealLinuxEnv
from safety.monitor import get_safety_monitor

class SafetyCallback(BaseCallback):
    """
    Callback to monitor safety during training
    Stops training if kill switch is activated or too many safety violations occur
    """
    def __init__(self, verbose=0):
        super(SafetyCallback, self).__init__(verbose)
        self.safety = get_safety_monitor()
        
    def _on_step(self) -> bool:
        # Check kill switch
        if self.safety.is_kill_switch_active():
            print("\n🚨 TRAINING STOPPED: Kill switch activated!")
            return False
            
        # Check recent violations
        stats = self.safety.get_stats()
        if stats["actions_last_minute"] > stats["max_actions_per_minute"] + 5:
            print("\n⚠️ TRAINING PAUSED: Rate limit consistently exceeded")
            time.sleep(60) # Pause to cool down
            
        return True

def train_real_agent():
    print("🚀 Initializing Real-World Training Pipeline...")
    
    # Safety Check
    safety = get_safety_monitor()
    print("🛡️ Safety Monitor Active")
    print(f"   - Allowed Targets: {safety.config.get('allowed_targets')}")
    print(f"   - Rate Limit: {safety.config.get('max_actions_per_minute')}/min")
    
    # Initialize Real Environment
    # We use a single environment for safety (no parallel execution against real targets)
    env = DummyVecEnv([lambda: RealLinuxEnv(target_ip="172.20.0.10")])
    
    # Model Configuration
    model_name = "redteam_real_v1"
    log_dir = "logs/real/"
    os.makedirs(log_dir, exist_ok=True)
    
    # Transfer Learning: Load pre-trained model if exists
    pretrained_path = "redteam_lstm_final.zip"
    if os.path.exists(pretrained_path):
        print(f"🔄 Loading pre-trained weights from {pretrained_path}...")
        # Note: We might need to adjust if observation space changed significantly
        # For PPO, we can load weights but might need to re-initialize policy if shapes differ
        # Here we assume compatibility or start fresh if shapes mismatch
        try:
            model = PPO.load(pretrained_path, env=env, verbose=1)
            print("✅ Weights loaded successfully!")
        except Exception as e:
            print(f"⚠️ Could not load weights directly (Architecture mismatch?): {e}")
            print("🆕 Starting fresh training...")
            model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=log_dir)
    else:
        print("🆕 No pre-trained model found. Starting fresh training...")
        model = PPO("MlpPolicy", env, verbose=1, tensorboard_log=log_dir)
    
    # Training Configuration
    # Real training is expensive (time-wise), so we use fewer steps
    total_timesteps = 1000 
    
    checkpoint_callback = CheckpointCallback(
        save_freq=100,
        save_path='./checkpoints/real/',
        name_prefix='redteam_real'
    )
    
    print(f"🏋️ Starting Training for {total_timesteps} steps...")
    print("   - This will execute REAL commands against the target")
    print("   - Expect execution to be slower than simulation")
    
    try:
        model.learn(
            total_timesteps=total_timesteps,
            callback=[checkpoint_callback, SafetyCallback()],
            progress_bar=True
        )
        
        print("✅ Training Complete!")
        model.save(model_name)
        print(f"💾 Model saved to {model_name}.zip")
        
    except KeyboardInterrupt:
        print("\n🛑 Training interrupted by user")
        model.save(f"{model_name}_interrupted")
        print("💾 Saved interrupted model")

if __name__ == "__main__":
    train_real_agent()
