# Quick Start Guide - Red Team Linux Agent

Get up and running with the Red Team Linux Agent in 5 minutes!

## Prerequisites

- Python 3.8+
- NVIDIA GPU with CUDA support (recommended)
- 3GB+ VRAM

## Installation

```bash
cd "d:/github/DRL Agents/RedTeam_Linux_Agent"
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
pip install gymnasium numpy
```

## Quick Training (10 Episodes)

```bash
python train_red_team.py --episodes 10
```

**Expected output:**

```
🚩 Initializing Red Team Linux Operation...
🚀 Red Team Brain initialized on: cuda
   GPU Model: NVIDIA GeForce RTX 2070
   ⚡ TF32 Math: ENABLED (MAX Speed Mode)
   🧠 Network Size: 8192 neurons (MAX)
...
✅ Operation Complete. Agent is ready for deployment.
```

## Run Trained Agent

```bash
python run_agent.py
```

## Full Training (500 Episodes)

```bash
python train_red_team.py --episodes 500
```

**Training features:**

- Auto-saves best model to `checkpoints/redteam_best.pth`
- Checkpoint every 50 episodes
- Resume with `--resume <episode_number>`

## Deploy Best Model

```bash
python run_agent.py --model checkpoints/redteam_best.pth
```

## Next Steps

- Read [TRAINING_RECOMMENDATIONS.md](TRAINING_RECOMMENDATIONS.md) for optimal training
- Check [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md) for advanced deployment
- See [TECHNICAL_ARCHITECTURE.md](TECHNICAL_ARCHITECTURE.md) for system details

## Troubleshooting

**No CUDA detected:**

- Verify NVIDIA drivers installed
- Check PyTorch CUDA version matches your CUDA toolkit

**Out of memory:**

- Reduce batch size in `agent/dqn_brain.py` (line 140)
- Default is 4096, try 2048 or 1024

**Training too slow:**

- Ensure GPU is being used (check "cuda" in output)
- Enable TF32 (should be automatic on RTX 2070)
