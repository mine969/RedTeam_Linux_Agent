"""
Red Team Linux Agent Package
=============================

A specialized Deep Reinforcement Learning agent for Linux penetration testing.

Components:
- dqn_brain: Dueling Double DQN agent for tactical decision-making
- linux_env: Linux server simulation environment
- report_generator: Penetration testing report generation
"""

__version__ = "2.0.0"
__author__ = "Mine"

from .agent.dqn_brain import RedTeamAgent, RedTeamBrain, ExperienceMemory
from .env.linux_env import LinuxSecEnv
from .utils.report_generator import ReportGenerator

__all__ = [
    'RedTeamAgent',
    'RedTeamBrain',
    'ExperienceMemory',
    'LinuxSecEnv',
    'ReportGenerator'
]
