# Red Team Linux Agent 🚩

This is a specialized AI agent designed for **Linux Penetration Testing**.
It is separate from the Web Security Agent to maximize efficiency and focus.

## Capabilities

The agent is trained to perform the following Kill Chain on Linux systems:

1.  **Reconnaissance**: `nmap`, `enum4linux`, `gobuster`
2.  **Initial Access**: `hydra` (SSH Brute Force), `exploit_buffer_overflow`
3.  **Execution**: Reverse Shells (`bash`, `python`)
4.  **Privilege Escalation**: `sudo -l`, `SUID`, `Dirty Cow`
5.  **Persistence**: SSH Key Injection

## Project Structure

- `agent/`: Contains the Deep Q-Network (Brain).
- `env/`: Contains the `LinuxSecEnv` (Simulation).
- `train_red_team.py`: The training loop.

## How to Run

```bash
python train_red_team.py
```

## Strategy

The agent uses Reinforcement Learning to learn the optimal path to Root.

- It learns that running `sudo -l` before getting a user shell is useless.
- It learns that `nmap` should be the first step.
- It learns to chain `Exploit -> Reverse Shell -> PrivEsc -> Root Flag`.
