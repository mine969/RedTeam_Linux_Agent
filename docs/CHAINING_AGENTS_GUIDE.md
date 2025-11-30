# Chaining Agents Guide

## Overview

The three DRL agents (Web, OSINT, Linux) are designed to work together in a complete offensive security pipeline.

## Agent Chain Architecture

```
┌─────────────────┐
│  OSINT Agent    │  Reconnaissance & Attack Surface Mapping
│  (10 actions)   │  - Subdomain enumeration
└────────┬────────┘  - Port scanning
         │           - Technology fingerprinting
         ↓
┌─────────────────┐
│   Web Agent     │  Web Application Exploitation
│  (100 actions)  │  - SQL Injection
└────────┬────────┘  - XSS, CSRF, SSRF
         │           - Authentication bypass
         ↓
┌─────────────────┐
│  Linux Agent    │  System-Level Compromise
│  (20 actions)   │  - Privilege escalation
└─────────────────┘  - Persistence
                     - Data exfiltration
```

## Shared Architecture

All three agents use **identical neural network architecture** for seamless integration:

| Component        | Specification             |
| ---------------- | ------------------------- |
| Algorithm        | Dueling Double DQN        |
| Neurons          | 8192 → 4096 → 2048 → 1024 |
| Batch Size       | 4096                      |
| GPU Optimization | TF32 + CuDNN              |
| Target Updates   | Soft (tau=0.005)          |

## Integration Points

### 1. State Transfer

**OSINT → Web:**

```python
osint_findings = {
    'subdomains': ['admin.target.com', 'api.target.com'],
    'technologies': ['nginx', 'PHP', 'MySQL'],
    'open_ports': {80: 'HTTP', 443: 'HTTPS', 22: 'SSH'}
}

web_agent.initialize(
    targets=osint_findings['subdomains'],
    tech_stack=osint_findings['technologies']
)
```

**Web → Linux:**

```python
web_exploits = {
    'shell_access': True,
    'credentials': ['admin:password123'],
    'upload_path': '/var/www/uploads/shell.php'
}

linux_agent.initialize(
    access_level=1,  # User shell from web exploit
    entry_point=web_exploits['upload_path']
)
```

### 2. Reward Chaining

```python
total_reward = (
    osint_reward * 0.2 +    # Reconnaissance phase
    web_reward * 0.3 +      # Initial compromise
    linux_reward * 0.5      # Full system control
)
```

### 3. Sequential Execution

```python
# Full pipeline
def autonomous_red_team(target):
    # Phase 1: OSINT
    osint_agent = OSINTDQNAgent(state_dim=8, action_dim=10)
    osint_agent.load('models/osint_best.pth')
    osint_results = osint_agent.scan(target)

    # Phase 2: Web Exploitation
    web_agent = DQNAgent(state_dim=23, action_dim=100)
    web_agent.load('checkpoints/web_best.pth')
    web_results = web_agent.exploit(osint_results['subdomains'])

    # Phase 3: Linux Privilege Escalation
    if web_results['shell_access']:
        linux_agent = RedTeamAgent(state_dim=5, action_dim=20)
        linux_agent.load('checkpoints/redteam_best.pth')
        linux_results = linux_agent.escalate(web_results)

    return {
        'osint': osint_results,
        'web': web_results,
        'linux': linux_results
    }
```

## Example Chained Attack

### Step 1: OSINT Reconnaissance

```
Target: example.com

OSINT Agent discovers:
✓ Subdomains: admin.example.com, api.example.com
✓ Technologies: Apache 2.4.41, PHP 7.4, MySQL
✓ Open Ports: 22 (SSH), 80 (HTTP), 443 (HTTPS)
✓ Emails: admin@example.com
```

### Step 2: Web Exploitation

```
Target: admin.example.com

Web Agent exploits:
✓ SQL Injection in login form
✓ Extracted admin credentials
✓ Uploaded webshell via file upload vulnerability
✓ Established reverse shell as www-data user
```

### Step 3: Linux Privilege Escalation

```
Access: www-data shell

Linux Agent escalates:
✓ Enumerated with linpeas.sh
✓ Found SUID binary /usr/bin/vim
✓ Exploited sudo misconfiguration
✓ Achieved root access
✓ Captured flag: CTF{L1nux_R00t_M4st3r}
```

## Benefits of Chaining

1. **Complete Coverage**: From reconnaissance to root access
2. **Automated Pipeline**: No manual intervention needed
3. **Consistent Architecture**: All agents use same DQN design
4. **Transfer Learning**: Agents can share knowledge
5. **Realistic Simulation**: Mirrors real-world attack chains

## Future Enhancements

- **Parallel Execution**: Multiple targets simultaneously
- **Dynamic Strategy**: Agents adapt based on previous results
- **Knowledge Sharing**: Cross-agent experience replay
- **Meta-Agent**: Higher-level agent that coordinates the three

## Implementation Status

- ✅ All three agents upgraded to Dueling Double DQN
- ✅ Identical 8192-neuron architecture
- ✅ GPU optimization enabled
- ✅ Standardized interfaces
- ⏳ Chaining logic (coming soon)
- ⏳ Meta-coordinator agent (planned)
