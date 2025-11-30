"""
Linux Agent Training with HoneyPot Data
========================================
Trains the Linux Agent using real-world command injection patterns.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from RedTeam_Linux_Agent.tools.command_library import CommandLibrary

def train_linux_honeypot(honeypot_path="training_data.json"):
    """
    Train Linux Agent with HoneyPot command patterns.
    
    Args:
        honeypot_path: Path to training_data.json
    """
    print("=" * 60)
    print("🍯 LINUX AGENT TRAINING WITH HONEYPOT DATA")
    print("=" * 60)
    
    # Initialize CommandLibrary
    cmd_lib = CommandLibrary(honeypot_data_path=honeypot_path)
    
    # Show dropper sequence
    dropper = cmd_lib.get_dropper_sequence()
    if dropper:
        print("\n✅ Learned Dropper Kill Chain:")
        for i, cmd in enumerate(dropper, 1):
            print(f"   {i}. {cmd}")
    
    print("\n" + "=" * 60)
    print("✅ LINUX AGENT READY")
    print("   Command injection patterns loaded from HoneyPot data.")
    print("   Agent can now execute real-world attack sequences.")
    print("=" * 60)

if __name__ == "__main__":
    honeypot_path = "../training_data.json"
    if not os.path.exists(honeypot_path):
        print(f"❌ Error: {honeypot_path} not found!")
        sys.exit(1)
    
    train_linux_honeypot(honeypot_path=honeypot_path)
