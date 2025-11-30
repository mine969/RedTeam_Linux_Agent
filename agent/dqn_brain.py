"""
Red Team Linux Agent - Advanced DQN Brain
==========================================

The "Brain" of the Red Team Linux Agent.
Upgraded to match the sophistication of the Web and OSINT agents.

Architecture:
- Deep Dueling DQN (8192 -> 4096 -> 2048 -> 1024 neurons)
- GPU Accelerated (TF32, CuDNN Benchmark)
- Double DQN with Soft Updates
- Massive Batch Size (4096) for RTX 2070
"""

import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from typing import Tuple
import os

class ExperienceMemory:
    """
    High-Performance Experience Memory.
    Uses pre-allocated Numpy arrays for O(1) storage and retrieval.
    """
    def __init__(self, state_size: int, action_size: int, capacity: int = 50000):
        self.capacity = capacity
        self.pointer = 0
        self.current_size = 0
        
        # Pre-allocate memory blocks for maximum speed
        self.states = np.zeros((capacity, state_size), dtype=np.float32)
        self.actions = np.zeros((capacity, 1), dtype=np.int64)
        self.rewards = np.zeros((capacity, 1), dtype=np.float32)
        self.next_states = np.zeros((capacity, state_size), dtype=np.float32)
        self.dones = np.zeros((capacity, 1), dtype=np.float32)
        
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    def save(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """Saves a single experience to memory."""
        self.states[self.pointer] = state
        self.actions[self.pointer] = action
        self.rewards[self.pointer] = reward
        self.next_states[self.pointer] = next_state
        self.dones[self.pointer] = done
        
        # Circular buffer: wrap around when full
        self.pointer = (self.pointer + 1) % self.capacity
        self.current_size = min(self.current_size + 1, self.capacity)

    def recall_batch(self, batch_size: int) -> Tuple[torch.Tensor, ...]:
        """Randomly recalls a batch of past experiences for training."""
        indices = np.random.randint(0, self.current_size, size=batch_size)
        
        return (
            torch.FloatTensor(self.states[indices]).to(self.device),
            torch.LongTensor(self.actions[indices]).to(self.device),
            torch.FloatTensor(self.rewards[indices]).to(self.device),
            torch.FloatTensor(self.next_states[indices]).to(self.device),
            torch.FloatTensor(self.dones[indices]).to(self.device)
        )

    def __len__(self) -> int:
        return self.current_size


class RedTeamBrain(nn.Module):
    """
    Deep Dueling Neural Network for Red Team Operations.
    Massive architecture to capture complex attack patterns.
    """
    def __init__(self, input_size: int, output_size: int):
        super(RedTeamBrain, self).__init__()
        
        # Deep Feature Extraction (MAX GPU MODE - RTX 2070 Optimized)
        self.feature_layer = nn.Sequential(
            nn.Linear(input_size, 8192),  # Massive input layer
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(8192, 4096),        # Deep abstraction
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(4096, 2048),        # Intermediate
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(2048, 1024),        # Bottleneck
            nn.ReLU()
        )
        
        # Value Stream (V) - How good is the current tactical state?
        self.value_stream = nn.Sequential(
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, 1)
        )
        
        # Advantage Stream (A) - Which attack action is best right now?
        self.advantage_stream = nn.Sequential(
            nn.Linear(1024, 1024),
            nn.ReLU(),
            nn.Linear(1024, output_size)
        )
        
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Passes information through the Dueling Network."""
        features = self.feature_layer(x)
        values = self.value_stream(features)
        advantages = self.advantage_stream(features)
        
        # Dueling DQN Aggregation
        # Q(s,a) = V(s) + (A(s,a) - mean(A(s,a)))
        q_values = values + (advantages - advantages.mean(dim=1, keepdim=True))
        return q_values


class RedTeamAgent:
    """
    Advanced Red Team Agent Controller.
    Manages the deep brain, memory, and learning process.
    """
    def __init__(self, state_dim: int, action_dim: int):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Hyperparameters (Optimized for RTX 2070)
        self.gamma = 0.99           # Discount factor for future rewards
        self.epsilon = 1.0          # Initial exploration rate
        self.epsilon_min = 0.05     # Minimum exploration
        self.epsilon_decay = 0.9995 # Slow decay for thorough learning
        self.batch_size = 4096      # MAX BATCH for RTX 2070
        self.learning_rate = 0.0002 # Lower LR for larger batch
        self.tau = 0.005            # Soft update rate
        
        # Hardware Setup
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🚀 Red Team Brain initialized on: {self.device}")
        
        if self.device.type == 'cuda':
            print(f"   GPU Model: {torch.cuda.get_device_name(0)}")
            torch.backends.cudnn.benchmark = True  # Auto-tune for max speed
            torch.backends.cuda.matmul.allow_tf32 = True  # Enable TF32 for speed
            print(f"   ⚡ CuDNN Benchmark: ENABLED")
            print(f"   ⚡ TF32 Math: ENABLED (MAX Speed Mode)")
            print(f"   📦 Batch Size: 4096 (MAX)")
            print(f"   🧠 Network Size: 8192 neurons (MAX)")
        
        # Components
        self.memory = ExperienceMemory(state_dim, action_dim, capacity=50000)
        
        # Main Brain (Policy Network - The one that learns)
        self.brain = RedTeamBrain(state_dim, action_dim).to(self.device)
        
        # Target Brain (Stable Network - The reference)
        self.target_brain = RedTeamBrain(state_dim, action_dim).to(self.device)
        self.target_brain.load_state_dict(self.brain.state_dict())
        self.target_brain.eval()  # Never train this directly!
        
        # Optimizer
        self.optimizer = optim.Adam(self.brain.parameters(), lr=self.learning_rate)
        self.loss_function = nn.MSELoss()

    def act(self, state: np.ndarray, training: bool = True) -> int:
        """
        Decides what to do next.
        Either explores randomly (Curiosity) or uses the Brain (Experience).
        """
        # Exploration
        if training and np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
        
        # Exploitation
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.brain(state_tensor)
        
        return int(q_values.argmax().item())

    def remember(self, state: np.ndarray, action: int, reward: float, next_state: np.ndarray, done: bool):
        """Stores a new experience in memory."""
        self.memory.save(state, action, reward, next_state, done)

    def replay(self):
        """
        The Learning Step.
        Reviews a batch of past memories and updates the brain to be smarter.
        Uses Double DQN to prevent overestimation.
        """
        if len(self.memory) < self.batch_size:
            return
        
        # 1. Recall a batch of memories
        states, actions, rewards, next_states, dones = self.memory.recall_batch(self.batch_size)
        
        # 2. Predict what we THOUGHT would happen (Current Q)
        current_q_values = self.brain(states).gather(1, actions).squeeze(1)
        
        # 3. Calculate what ACTUALLY happened (Target Q) using Double DQN
        # Step A: Main Brain picks the best action for the next state
        best_actions = self.brain(next_states).argmax(1).unsqueeze(1)
        
        # Step B: Target Brain calculates the value of that action
        # This prevents the agent from being "overconfident"
        next_q_values = self.target_brain(next_states).gather(1, best_actions).squeeze(1)
        
        # Step C: Bellman Equation
        target_q_values = rewards.squeeze(1) + (1 - dones.squeeze(1)) * self.gamma * next_q_values
        
        # 4. Calculate the mistake (Loss)
        loss = self.loss_function(current_q_values, target_q_values.detach())
        
        # 5. Correct the Brain (Backpropagation)
        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()
        
        # 6. Soft Update: Slowly blend Main Brain into Target Brain
        self.soft_update()
        
        # 7. Reduce curiosity slightly (become more confident)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def soft_update(self):
        """
        Slowly updates the Target Brain to match the Main Brain.
        This creates a "Moving Target" that is stable but eventually catches up.
        Formula: Target = (tau * Main) + ((1-tau) * Target)
        """
        for target_param, local_param in zip(self.target_brain.parameters(), self.brain.parameters()):
            target_param.data.copy_(self.tau * local_param.data + (1.0 - self.tau) * target_param.data)

    def save(self, filepath: str):
        """Saves the brain to disk."""
        torch.save({
            'brain_state': self.brain.state_dict(),
            'target_brain_state': self.target_brain.state_dict(),
            'optimizer_state': self.optimizer.state_dict(),
            'epsilon': self.epsilon
        }, filepath)
        print(f"💾 Red Team Brain saved to {filepath}")

    def load(self, filepath: str) -> bool:
        """Loads the brain from disk."""
        if not os.path.exists(filepath):
            print(f"⚠️ Model not found: {filepath}")
            return False
            
        checkpoint = torch.load(filepath, map_location=self.device)
        self.brain.load_state_dict(checkpoint['brain_state'])
        self.target_brain.load_state_dict(checkpoint['target_brain_state'])
        self.optimizer.load_state_dict(checkpoint['optimizer_state'])
        self.epsilon = checkpoint['epsilon']
        print(f"✅ Red Team Brain loaded from {filepath}")
        return True
