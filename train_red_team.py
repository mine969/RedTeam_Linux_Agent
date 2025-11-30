
import sys
import os
import time
import argparse

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env.linux_env import LinuxSecEnv
from agent.dqn_brain import RedTeamAgent
from utils.report_generator import ReportGenerator

def train_red_team(episodes=500, resume_from=None):
    print("🚩 Initializing Red Team Linux Operation...")
    print("=" * 60)
    
    env = LinuxSecEnv()
    agent = RedTeamAgent(state_dim=5, action_dim=20)
    
    # Create checkpoints directory
    checkpoint_dir = "checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Resume from checkpoint if specified
    start_episode = 0
    if resume_from:
        checkpoint_path = os.path.join(checkpoint_dir, f"redteam_ep{resume_from}.pth")
        if agent.load(checkpoint_path):
            start_episode = resume_from
            print(f"📂 Resumed from episode {start_episode}")
        else:
            print(f"⚠️ Could not load checkpoint, starting from scratch")
    
    print(f"🎯 Target: Linux Server (Simulated)")
    print(f"🤖 Agent: RedTeam-v2 (Dueling Double DQN)")
    print(f"📚 Training for {episodes} episodes (starting from {start_episode})...")
    print("=" * 60)
    
    best_reward = -float('inf')
    
    for e in range(start_episode, episodes):
        state, _ = env.reset()
        total_reward = 0
        done = False
        step_count = 0
        
        # Initialize Report for this "Engagement"
        reporter = ReportGenerator(target_name=f"Sim_Server_{e}")
        
        while not done:
            action = agent.act(state)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            step_count += 1
            
            # Log Action
            reporter.log_action(info['action'], info['output'])
            
            # Log Findings
            if "SUCCESS" in info['output']:
                reporter.add_finding("Weak Credentials", "HIGH", f"Found password via brute force: {info['output']}")
            if "Connection received" in info['output']:
                reporter.add_finding("Remote Code Execution", "CRITICAL", "Reverse shell established.")
            if "root" in info['output'] and "whoami" in info['action']:
                reporter.add_finding("Privilege Escalation", "CRITICAL", "Root access achieved.")
            
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            total_reward += reward
            
            agent.replay()
            
        # Generate Report if we won
        if total_reward > 100:
            report_path = reporter.generate_report()
            if (e + 1) % 10 == 0:
                print(f"📄 Report generated: {report_path}")
        
        # Save best model
        if total_reward > best_reward:
            best_reward = total_reward
            best_path = os.path.join(checkpoint_dir, "redteam_best.pth")
            agent.save(best_path)
            
        # Save checkpoint every 50 episodes
        if (e + 1) % 50 == 0:
            checkpoint_path = os.path.join(checkpoint_dir, f"redteam_ep{e+1}.pth")
            agent.save(checkpoint_path)
            
        # Progress reporting
        if (e + 1) % 10 == 0:
            print(f"Episode {e+1}/{episodes} | Score: {total_reward:.1f} | Steps: {step_count} | "
                  f"Epsilon: {agent.epsilon:.3f} | Best: {best_reward:.1f}")
    
    # Save final model
    final_path = os.path.join(checkpoint_dir, "redteam_final.pth")
    agent.save(final_path)
    
    print("=" * 60)
    print(f"✅ Operation Complete. Agent is ready for deployment.")
    print(f"📊 Best Score: {best_reward:.1f}")
    print(f"💾 Models saved in: {checkpoint_dir}/")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Train Red Team Linux Agent')
    parser.add_argument('--episodes', type=int, default=500, help='Number of episodes to train')
    parser.add_argument('--resume', type=int, default=None, help='Resume from episode number')
    
    args = parser.parse_args()
    train_red_team(episodes=args.episodes, resume_from=args.resume)
