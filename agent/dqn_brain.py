
import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np
import random
from collections import deque

# Reusing the Deep Brain Architecture from the Web Agent
# But adapted for the Linux Environment

class RedTeamBrain(nn.Module):
    def __init__(self, input_size, output_size):
        super(RedTeamBrain, self).__init__()
        
        # Deep Neural Network for Tactical Decision Making
        self.network = nn.Sequential(
            nn.Linear(input_size, 256),
            nn.ReLU(),
            nn.Linear(256, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU(),
            nn.Linear(128, output_size)
        )
        
    def forward(self, x):
        return self.network(x)

class RedTeamAgent:
    def __init__(self, state_dim, action_dim):
        self.state_dim = state_dim
        self.action_dim = action_dim
        
        # Hyperparameters
        self.gamma = 0.99
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.001
        self.batch_size = 32
        
        self.memory = deque(maxlen=2000)
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        self.model = RedTeamBrain(state_dim, action_dim).to(self.device)
        self.optimizer = optim.Adam(self.model.parameters(), lr=self.learning_rate)
        self.criterion = nn.MSELoss()

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_dim)
        
        state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
        with torch.no_grad():
            q_values = self.model(state_tensor)
        return np.argmax(q_values.cpu().data.numpy())

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def replay(self):
        if len(self.memory) < self.batch_size:
            return
        
        minibatch = random.sample(self.memory, self.batch_size)
        
        for state, action, reward, next_state, done in minibatch:
            target = reward
            if not done:
                next_state_tensor = torch.FloatTensor(next_state).unsqueeze(0).to(self.device)
                target = reward + self.gamma * torch.max(self.model(next_state_tensor)).item()
                
            state_tensor = torch.FloatTensor(state).unsqueeze(0).to(self.device)
            target_f = self.model(state_tensor)
            
            # Update the Q-value for the action taken
            # We need to clone to avoid in-place operation error if we were backpropping (but here we just modify data)
            # Actually, standard DQN way:
            current_prediction = self.model(state_tensor)
            target_vector = current_prediction.clone().detach()
            target_vector[0][action] = target
            
            # Train
            self.optimizer.zero_grad()
            loss = self.criterion(current_prediction, target_vector)
            loss.backward()
            self.optimizer.step()

        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay
