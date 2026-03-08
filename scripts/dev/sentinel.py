import os
import subprocess
import json
from datetime import datetime

class Sentinel:
    def __init__(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.report_path = os.path.join(self.base_dir, "logs", "sentinel_report.md")

    def run_audit(self):
        """Runs the architectural audit."""
        audit_script = os.path.join(self.base_dir, "scripts", "dev", "audit_repo.py")
        try:
            result = subprocess.check_output(["python", audit_script], stderr=subprocess.STDOUT, text=True)
            return result
        except subprocess.CalledProcessError as e:
            return f"Audit Failed: {e.output}"

    def get_telemetry_summary(self):
        """Runs the telemetry aggregator."""
        agg_script = os.path.join(self.base_dir, "scripts", "dev", "telemetry_aggregator.py")
        try:
            result = subprocess.check_output(["python", agg_script], stderr=subprocess.STDOUT, text=True)
            return result
        except subprocess.CalledProcessError as e:
            return f"Telemetry Aggregation Failed: {e.output}"

    def check_bugs(self):
        """Summarizes recent bugs from logs/bugs.jsonl."""
        bug_file = os.path.join(self.base_dir, "logs", "bugs.jsonl")
        if not os.path.exists(bug_file):
            return "No active bugs found."
        
        bugs = []
        with open(bug_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            for line in lines[-5:]: # Last 5 bugs
                try:
                    bugs.append(json.loads(line))
                except:
                    continue
        
        if not bugs:
            return "No recent bug reports."
        
        summary = "### Recent Bugs\n"
        for b in bugs:
            summary += f"- **{b.get('entity')}**: {b.get('data', {}).get('note')} (@{b.get('data', {}).get('coords')})\n"
        return summary

    def generate_report(self):
        print("Sentinel: Running Architectural Audit...")
        audit = self.run_audit()
        
        print("Sentinel: Aggregating Telemetry...")
        telemetry = self.get_telemetry_summary()
        
        print("Sentinel: Checking Bug Reports...")
        bugs = self.check_bugs()

        report = [
            f"# Godless Sentinel Report - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "\n## 🛡️ Architectural Integrity",
            audit,
            "\n## 📊 System Performance",
            telemetry,
            "\n## 🐛 Bug Tracker",
            bugs,
            "\n---\n*Sentinel is monitoring. Adjusting dev priorities...*"
        ]

        with open(self.report_path, "w", encoding='utf-8') as f:
            f.write("\n".join(report))
        
        print(f"Sentinel: Report generated at {self.report_path}")

if __name__ == "__main__":
    sentinel = Sentinel()
    sentinel.generate_report()
