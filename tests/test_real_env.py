"""
Test Real Environment - Smoke test for RealLinuxEnv

Tests:
- Environment initialization
- Action execution
- Observation space
- State tracking
"""

import unittest
import sys
import os
import numpy as np

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from env.real_linux_env import RealLinuxEnv

class TestRealLinuxEnv(unittest.TestCase):
    """Test Real Linux Environment"""
    
    def setUp(self):
        """Setup test environment"""
        try:
            self.env = RealLinuxEnv(target_ip="172.20.0.10")
        except Exception as e:
            self.skipTest(f"Could not initialize environment: {e}")
    
    def test_environment_initialization(self):
        """Test that environment initializes correctly"""
        self.assertIsNotNone(self.env)
        self.assertEqual(self.env.target_ip, "172.20.0.10")
        self.assertEqual(len(self.env.actions), 20)
    
    def test_action_space(self):
        """Test action space is correct"""
        self.assertEqual(self.env.action_space.n, 20)
    
    def test_observation_space(self):
        """Test observation space shape"""
        self.assertEqual(self.env.observation_space.shape, (9,))
    
    def test_reset(self):
        """Test environment reset"""
        obs, info = self.env.reset()
        
        # Check observation shape
        self.assertEqual(obs.shape, (9,))
        
        # Check initial state
        self.assertEqual(self.env.access_level, 0)
        self.assertEqual(self.env.ports_found, 0)
        self.assertEqual(self.env.steps, 0)
    
    def test_step_wait_action(self):
        """Test simple wait action (should always work)"""
        self.env.reset()
        
        # Action 19 is "wait"
        obs, reward, terminated, truncated, info = self.env.step(19)
        
        # Check return types
        self.assertIsInstance(obs, np.ndarray)
        self.assertIsInstance(reward, float)
        self.assertIsInstance(terminated, bool)
        self.assertIsInstance(truncated, bool)
        self.assertIsInstance(info, dict)
        
        # Check info contains expected keys
        self.assertIn("action", info)
        self.assertIn("output", info)
    
    def test_step_nmap_action(self):
        """Test nmap action (action 0)"""
        self.env.reset()
        
        # This will execute real nmap if target is reachable
        obs, reward, terminated, truncated, info = self.env.step(0)
        
        # Check that action was recorded
        self.assertIn("action", info)
        self.assertIn("nmap", info["action"])
        
        # If successful, ports_found should be updated
        if info.get("success", False):
            print(f"Nmap found ports: {self.env.discovered_ports}")
    
    def test_episode_termination(self):
        """Test that episode terminates after max steps"""
        self.env.reset()
        
        # Run for max_steps + 1
        for i in range(self.env.max_steps + 1):
            obs, reward, terminated, truncated, info = self.env.step(19)  # Wait action
            
            if i >= self.env.max_steps - 1:
                self.assertTrue(truncated, "Episode should truncate after max steps")
                break

class TestRealLinuxEnvIntegration(unittest.TestCase):
    """Integration tests requiring Docker container"""
    
    def setUp(self):
        """Check if Docker container is running"""
        import subprocess
        try:
            result = subprocess.run(
                ["docker", "ps", "--filter", "name=redteam_target", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if "redteam_target" not in result.stdout:
                self.skipTest("Docker containers not running. Run 'docker-compose up -d' first.")
            
            self.env = RealLinuxEnv(target_ip="172.20.0.10")
            
        except Exception as e:
            self.skipTest(f"Docker not available: {e}")
    
    def test_full_episode_simulation(self):
        """Test a full episode with multiple actions"""
        obs, _ = self.env.reset()
        
        actions_to_test = [
            0,   # nmap scan
            19,  # wait
            5,   # hydra (may take time)
        ]
        
        for action in actions_to_test:
            obs, reward, terminated, truncated, info = self.env.step(action)
            print(f"Action {action}: {info['action']} - {info.get('output', '')[:50]}")
            
            if terminated or truncated:
                break
        
        # Check that we got through some actions
        self.assertGreater(self.env.steps, 0)

if __name__ == '__main__':
    print("Running Real Environment Tests...")
    print("=" * 60)
    print("Note: Some tests require Docker containers to be running")
    print("Run 'docker-compose up -d' before running these tests")
    print("=" * 60)
    unittest.main(verbosity=2)
