import os
import sys
import time
import argparse

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env.linux_env import LinuxSecEnv
from agent.dqn_brain import RedTeamAgent
from utils.report_generator import ReportGenerator

def run_agent(model_path=None, episodes=1, verbose=True):
    """
    Deploy the trained Red Team Agent.
    
    Args:
        model_path: Path to saved model (default: checkpoints/redteam_best.pth)
        episodes: Number of episodes to run
        verbose: Print detailed output
    """
    print("🚀 Initializing Red Team Agent Deployment...")
    print("=" * 60)
    
    # Initialize environment and agent
    env = LinuxSecEnv()
    agent = RedTeamAgent(state_dim=5, action_dim=20)
    
    # Load trained model
    if model_path is None:
        model_path = os.path.join("checkpoints", "redteam_best.pth")
    
    if not agent.load(model_path):
        print(f"⚠️ Warning: Could not load model from {model_path}")
        print("Running with untrained agent...")
    
    print(f"🎯 Target: Linux Server (Simulated)")
    print(f"🤖 Agent: RedTeam-v2 (Dueling Double DQN)")
    print(f"📊 Running {episodes} episode(s)...")
    print("=" * 60)
    
    for ep in range(episodes):
        if episodes > 1:
            print(f"\n--- Episode {ep + 1}/{episodes} ---")
        
        state, _ = env.reset()
        done = False
        total_reward = 0
        step_count = 0
        
        # Initialize report
        reporter = ReportGenerator(target_name=f"Target_Server_{ep}")
        
        while not done:
            # Agent acts (no exploration during deployment)
            action = agent.act(state, training=False)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
            step_count += 1
            total_reward += reward
            
            # Log action
            reporter.log_action(info['action'], info['output'])
            
            # Log findings
            if "SUCCESS" in info['output']:
                reporter.add_finding("Weak Credentials", "HIGH", 
                                   f"Found password via brute force: {info['output']}")
            if "Connection received" in info['output']:
                reporter.add_finding("Remote Code Execution", "CRITICAL", 
                                   "Reverse shell established.")
            if "root" in info['output'] and "whoami" in info['action']:
                reporter.add_finding("Privilege Escalation", "CRITICAL", 
                                   "Root access achieved.")
            
            # Print step info if verbose
            if verbose:
                print(f"Step {step_count}: {info['action']}")
                print(f"   └── {info['output']}")
                print(f"   └── Reward: {reward:.1f}")
            
            state = next_state
            
            # Optional: Add delay for readability
            if verbose:
                time.sleep(0.3)
        
        # Generate report
        report_path = reporter.generate_report()
        
        print("-" * 60)
        print(f"🏁 Episode {ep + 1} Finished")
        print(f"💰 Total Reward: {total_reward:.1f}")
        print(f"👣 Total Steps: {step_count}")
        print(f"📄 Report: {report_path}")
        
        # Success indicator
        if total_reward > 500:
            print("🎉 ROOT FLAG CAPTURED!")
        elif total_reward > 100:
            print("✅ Successful compromise")
        else:
            print("⚠️ Partial success")
    
    print("=" * 60)
    print("✅ Deployment Complete")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Deploy Red Team Linux Agent')
    parser.add_argument('--model', type=str, default=None, 
                       help='Path to model file (default: checkpoints/redteam_best.pth)')
    parser.add_argument('--episodes', type=int, default=1, 
                       help='Number of episodes to run')
    parser.add_argument('--quiet', action='store_true', 
                       help='Reduce output verbosity')
    
    args = parser.parse_args()
    run_agent(model_path=args.model, episodes=args.episodes, verbose=not args.quiet)
