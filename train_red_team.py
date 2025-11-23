
import sys
import os
import time

# Add current directory to path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env.linux_env import LinuxSecEnv
from agent.dqn_brain import RedTeamAgent
from utils.report_generator import ReportGenerator

def train_red_team():
    print("🚩 Initializing Red Team Linux Operation...")
    
    env = LinuxSecEnv()
    agent = RedTeamAgent(state_dim=5, action_dim=20)
    
    episodes = 500
    
    print(f"🎯 Target: Linux Server (Simulated)")
    print(f"🤖 Agent: RedTeam-v1")
    print(f"📚 Training for {episodes} episodes...")
    print("-" * 50)
    
    for e in range(episodes):
        state, _ = env.reset()
        total_reward = 0
        done = False
        
        # Initialize Report for this "Engagement"
        reporter = ReportGenerator(target_name=f"Sim_Server_{e}")
        
        while not done:
            action = agent.act(state)
            next_state, reward, terminated, truncated, info = env.step(action)
            done = terminated or truncated
            
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
            
        if (e + 1) % 10 == 0:
            print(f"Episode {e+1}/{episodes} | Score: {total_reward:.1f} | Epsilon: {agent.epsilon:.2f}")
                    
    print("\n✅ Operation Complete. Agent is ready for deployment.")

if __name__ == "__main__":
    train_red_team()
