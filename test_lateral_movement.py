import sys
import os
import time
import random

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from env.advanced_env import AdvancedKillChainEnv

def test_lateral_movement():
    print("🚀 Testing Lateral Movement Capabilities...")
    env = AdvancedKillChainEnv()
    obs, _ = env.reset()
    
    print(f"Target OS: {env.current_os}")
    
    # Cheat: Give ourselves access to test lateral movement
    print("\n🔓 Cheating: Granting Initial Access...")
    env.state["access_level"] = 1 # User Access
    env.state["kill_chain_phase"] = 2 # Initial Access Done
    
    # 1. Test Internal Subnet Scan (Action 25)
    print("\n📡 Action: Internal_Subnet_Scan (25)")
    obs, reward, done, _, info = env.step(25)
    print(f"   └── Output: {info['output']}")
    print(f"   └── Nodes Found: {env.state['lateral_nodes_found']}")
    print(f"   └── Reward: {reward}")
    
    if env.state['lateral_nodes_found'] > 0:
        print("✅ Scan Successful")
    else:
        print("❌ Scan Failed")

    # 2. Test Lateral Pivot (Action 26 - SMB Pass The Hash)
    print("\n🔗 Action: SMB_Pass_The_Hash (26)")
    # Force success for testing if possible, but it's random. Let's try a few times.
    for i in range(3):
        obs, reward, done, _, info = env.step(26)
        print(f"   └── Attempt {i+1}: {info['output']}")
        if "Successful" in info['output']:
            print("✅ Pivot Successful")
            break
            
    # 3. Test Tunneling (Action 29)
    print("\n🚇 Action: Tunneling_ProxyChains (29)")
    obs, reward, done, _, info = env.step(29)
    print(f"   └── Output: {info['output']}")
    
    print("\n🏁 Test Complete")

if __name__ == "__main__":
    test_lateral_movement()
