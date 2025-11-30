"""
Test the 10k-step trained LSTM model to see what it learned.
"""
import os
import numpy as np
import torch
from sb3_contrib import RecurrentPPO
from env.advanced_env import AdvancedKillChainEnv

def test_model(num_episodes=5):
    print("=" * 70)
    print("🧪 TESTING 10K-STEP TRAINED MODEL")
    print("=" * 70)
    
    # Check GPU
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"🖥️  Device: {device.type.upper()}")
    if torch.cuda.is_available():
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    
    model_path = "redteam_lstm_final.zip"
    if not os.path.exists(model_path):
        print(f"❌ Model not found: {model_path}")
        return
    
    print(f"📂 Loading Model: {model_path}")
    model = RecurrentPPO.load(model_path, device=device)
    
    # Initialize Environment
    env = AdvancedKillChainEnv()
    
    print(f"\n🎯 Running {num_episodes} test episodes...\n")
    
    episode_rewards = []
    episode_lengths = []
    successful_episodes = 0
    
    for episode in range(num_episodes):
        print(f"\n{'='*70}")
        print(f"📍 EPISODE {episode + 1}/{num_episodes}")
        print(f"{'='*70}")
        
        obs, _ = env.reset()
        lstm_states = None
        episode_starts = np.ones((1,), dtype=bool)
        
        done = False
        total_reward = 0
        step_count = 0
        actions_taken = []
        
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
            actions_taken.append(info['action'])
            
            # Print step info
            output = info.get('output', 'No output.')
            print(f"  Step {step_count:2d}: {info['action']:<35} | Reward: {reward:6.2f}")
            if output and output != "No output.":
                print(f"           └─ {output}")
        
        episode_rewards.append(total_reward)
        episode_lengths.append(step_count)
        
        if total_reward > 0:
            successful_episodes += 1
        
        print(f"\n  {'─'*66}")
        print(f"  🏁 Episode {episode + 1} Complete")
        print(f"  💰 Total Reward: {total_reward:.2f}")
        print(f"  👣 Steps Taken: {step_count}")
        print(f"  📊 Success: {'✅ YES' if total_reward > 0 else '❌ NO'}")
    
    # Summary Statistics
    print(f"\n{'='*70}")
    print("📊 OVERALL STATISTICS")
    print(f"{'='*70}")
    print(f"  Episodes Run: {num_episodes}")
    print(f"  Successful Episodes: {successful_episodes}/{num_episodes} ({successful_episodes/num_episodes*100:.1f}%)")
    print(f"  Average Reward: {np.mean(episode_rewards):.2f} ± {np.std(episode_rewards):.2f}")
    print(f"  Best Reward: {np.max(episode_rewards):.2f}")
    print(f"  Worst Reward: {np.min(episode_rewards):.2f}")
    print(f"  Average Steps: {np.mean(episode_lengths):.1f}")
    print(f"{'='*70}")
    
    # Capability Assessment
    print("\n🎓 CAPABILITY ASSESSMENT (10K Steps Training)")
    print(f"{'='*70}")
    
    avg_reward = np.mean(episode_rewards)
    
    if avg_reward > 100:
        print("  ✅ EXCELLENT: Agent consistently completes objectives")
        print("     - Understands kill chain progression")
        print("     - Makes strategic decisions")
        print("     - Achieves root/admin access regularly")
    elif avg_reward > 0:
        print("  ⚠️  MODERATE: Agent shows some learning")
        print("     - Can perform basic reconnaissance")
        print("     - Sometimes gains initial access")
        print("     - Needs more training for consistency")
    elif avg_reward > -50:
        print("  ⚠️  BASIC: Agent has learned minimal strategy")
        print("     - Avoids worst actions")
        print("     - Shows some pattern recognition")
        print("     - Requires significantly more training")
    else:
        print("  ❌ POOR: Agent needs more training")
        print("     - Random or repetitive behavior")
        print("     - No clear strategy")
        print("     - Recommend 100K+ steps for real learning")
    
    print(f"{'='*70}")
    print("\n💡 RECOMMENDATION:")
    print("   For production-ready agent: Train for 500K - 1M steps")
    print("   Current 10K steps = Early exploration phase")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_model(num_episodes=5)
