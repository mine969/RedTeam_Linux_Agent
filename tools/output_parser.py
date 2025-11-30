"""
Output Parser - Parses tool outputs into structured observations

Extracts useful information from:
- Nmap scan results
- Hydra brute force results
- SSH command outputs
"""

import re
from typing import Dict, List, Optional
import logging

class OutputParser:
    """Parse pentesting tool outputs into structured data"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def parse_nmap_output(self, output: str) -> Dict:
        """
        Parse nmap output to extract ports and services
        
        Args:
            output: Raw nmap output
            
        Returns:
            Dictionary with parsed information
        """
        parsed = {
            "open_ports": [],
            "services": {},
            "os_guess": None,
            "total_ports_scanned": 0
        }
        
        # Extract open ports
        # Pattern: 22/tcp   open  ssh     OpenSSH 7.6p1
        port_pattern = r'(\d+)/(tcp|udp)\s+open\s+(\S+)\s*(.*)?'
        
        for match in re.finditer(port_pattern, output):
            port = int(match.group(1))
            protocol = match.group(2)
            service = match.group(3)
            version = match.group(4).strip() if match.group(4) else ""
            
            parsed["open_ports"].append(port)
            parsed["services"][port] = {
                "protocol": protocol,
                "service": service,
                "version": version
            }
        
        # Extract OS information
        os_pattern = r'OS details:\s*(.+)'
        os_match = re.search(os_pattern, output)
        if os_match:
            parsed["os_guess"] = os_match.group(1).strip()
        
        # Count scanned ports
        scanned_pattern = r'Nmap scan report for.*?(\d+)\s+ports?\s+scanned'
        scanned_match = re.search(scanned_pattern, output, re.DOTALL)
        if scanned_match:
            parsed["total_ports_scanned"] = int(scanned_match.group(1))
        
        self.logger.info(f"Parsed nmap: {len(parsed['open_ports'])} open ports found")
        return parsed
    
    def parse_hydra_output(self, output: str) -> Dict:
        """
        Parse Hydra output to extract credentials
        
        Args:
            output: Raw Hydra output
            
        Returns:
            Dictionary with found credentials
        """
        parsed = {
            "credentials_found": [],
            "attempts": 0,
            "success": False
        }
        
        # Pattern: [22][ssh] host: 172.20.0.10   login: admin   password: password123
        cred_pattern = r'login:\s*(\S+)\s+password:\s*(\S+)'
        
        for match in re.finditer(cred_pattern, output):
            username = match.group(1)
            password = match.group(2)
            parsed["credentials_found"].append({
                "username": username,
                "password": password
            })
            parsed["success"] = True
        
        # Extract attempt count
        attempt_pattern = r'(\d+)\s+passwords?\s+tested'
        attempt_match = re.search(attempt_pattern, output)
        if attempt_match:
            parsed["attempts"] = int(attempt_match.group(1))
        
        self.logger.info(f"Parsed Hydra: {len(parsed['credentials_found'])} credentials found")
        return parsed
    
    def parse_ssh_output(self, output: str, command: str) -> Dict:
        """
        Parse SSH command output
        
        Args:
            output: Command output
            command: Original command
            
        Returns:
            Dictionary with parsed information
        """
        parsed = {
            "command": command,
            "output": output,
            "indicators": {}
        }
        
        # Detect privilege level
        if "uid=0(root)" in output:
            parsed["indicators"]["privilege"] = "root"
        elif "uid=" in output:
            parsed["indicators"]["privilege"] = "user"
        
        # Detect sudo capabilities
        if "NOPASSWD" in output:
            parsed["indicators"]["sudo_nopasswd"] = True
            # Extract sudo commands
            sudo_pattern = r'\(ALL\)\s+NOPASSWD:\s*(.+)'
            sudo_match = re.search(sudo_pattern, output)
            if sudo_match:
                parsed["indicators"]["sudo_commands"] = sudo_match.group(1).strip()
        
        # Detect SUID binaries
        if command.startswith("find") and "-perm" in command:
            suid_binaries = [line.strip() for line in output.split('\n') if line.strip()]
            parsed["indicators"]["suid_binaries"] = suid_binaries
        
        # Detect interesting files
        if "flag" in output.lower() or "ctf{" in output.lower():
            parsed["indicators"]["flag_found"] = True
        
        return parsed
    
    def extract_numerical_features(self, parsed_data: Dict) -> List[float]:
        """
        Convert parsed data into numerical features for RL agent
        
        Args:
            parsed_data: Parsed tool output
            
        Returns:
            List of numerical features
        """
        features = []
        
        # Feature 1: Number of open ports (normalized)
        open_ports = len(parsed_data.get("open_ports", []))
        features.append(min(open_ports / 10.0, 1.0))
        
        # Feature 2: SSH service available
        services = parsed_data.get("services", {})
        ssh_available = any(s.get("service") == "ssh" for s in services.values())
        features.append(1.0 if ssh_available else 0.0)
        
        # Feature 3: HTTP service available
        http_available = any(s.get("service") in ["http", "https"] for s in services.values())
        features.append(1.0 if http_available else 0.0)
        
        # Feature 4: Credentials found
        creds_found = len(parsed_data.get("credentials_found", []))
        features.append(1.0 if creds_found > 0 else 0.0)
        
        # Feature 5: Privilege level (0=none, 0.5=user, 1.0=root)
        privilege = parsed_data.get("indicators", {}).get("privilege", "none")
        priv_map = {"none": 0.0, "user": 0.5, "root": 1.0}
        features.append(priv_map.get(privilege, 0.0))
        
        return features
    
    def summarize_output(self, output: str, max_length: int = 200) -> str:
        """
        Create a concise summary of tool output
        
        Args:
            output: Full output
            max_length: Maximum summary length
            
        Returns:
            Summarized output
        """
        if len(output) <= max_length:
            return output
        
        # Extract key lines
        lines = output.split('\n')
        important_lines = []
        
        keywords = ["open", "found", "success", "password", "root", "admin", "flag", "error", "failed"]
        
        for line in lines:
            if any(keyword in line.lower() for keyword in keywords):
                important_lines.append(line.strip())
        
        summary = '\n'.join(important_lines[:5])  # Top 5 important lines
        
        if len(summary) > max_length:
            summary = summary[:max_length] + "..."
        
        return summary if summary else output[:max_length] + "..."
