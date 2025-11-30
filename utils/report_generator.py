
import datetime
import os

class ReportGenerator:
    """
    Generates professional Penetration Testing reports for Linux Targets.
    """
    
    def __init__(self, target_name="Linux Server"):
        self.target_name = target_name
        self.vulns_found = []
        self.actions_taken = []
        self.start_time = datetime.datetime.now()
        
    def log_action(self, action, output):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.actions_taken.append({
            "time": timestamp,
            "action": action,
            "output": output
        })
        
    def add_finding(self, finding_type, severity, description):
        self.vulns_found.append({
            "type": finding_type,
            "severity": severity,
            "description": description
        })
        
    def generate_report(self):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
        filename = f"reports/Pentest_Report_{self.target_name}_{timestamp}.md"
        
        os.makedirs("reports", exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            # Header
            f.write(f"# Penetration Test Report: {self.target_name}\n")
            f.write(f"**Date:** {datetime.datetime.now().strftime('%Y-%m-%d')}\n")
            f.write(f"**Agent:** RedTeam-Linux-v2\n")
            f.write("---\n\n")
            
            # Executive Summary
            f.write("## 1. Executive Summary\n")
            if any(v['severity'] == "CRITICAL" for v in self.vulns_found):
                f.write("**Status: COMPROMISED**\n")
                f.write("The target system was successfully compromised. Root access was achieved.\n")
            else:
                f.write("**Status: SECURE**\n")
                f.write("No critical vulnerabilities were exploited during this session.\n")
            f.write("\n")
            
            # Findings
            f.write("## 2. Vulnerabilities Identified\n")
            if not self.vulns_found:
                f.write("*No vulnerabilities found.*\n")
            else:
                for v in self.vulns_found:
                    f.write(f"### {v['type']} ({v['severity']})\n")
                    f.write(f"{v['description']}\n\n")
            
            # Attack Log
            f.write("## 3. Attack Log (Timeline)\n")
            f.write("| Time | Action | Output |\n")
            f.write("|---|---|---|\n")
            for log in self.actions_taken:
                # Truncate output for readability
                clean_output = log['output'].replace("\n", " ").strip()[:50] + "..."
                f.write(f"| {log['time']} | `{log['action']}` | {clean_output} |\n")
                
        return filename
