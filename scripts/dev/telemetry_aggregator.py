import json
import os
from collections import Counter, defaultdict
from datetime import datetime

class TelemetryAggregator:
    def __init__(self, log_path="logs/telemetry.jsonl"):
        self.log_path = log_path
        self.stats = {
            "skill_usage": Counter(),
            "damage_per_skill": defaultdict(list),
            "resource_deltas": defaultdict(lambda: Counter()),
            "errors": [],
            "bug_reports": [],
            "status_effects": Counter(),
            "movement_heatmap": Counter()
        }

    def process(self):
        if not os.path.exists(self.log_path):
            return "No telemetry log found."

        with open(self.log_path, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    event = json.loads(line)
                    self._parse_event(event)
                except json.JSONDecodeError:
                    continue

        return self._generate_report()

    def _parse_event(self, event):
        e_type = event.get("type")
        data = event.get("data", {})
        entity = event.get("entity", "Unknown")

        if e_type == "SKILL_EXECUTE":
            skill = data.get("skill")
            result = data.get("result", "SUCCESS")
            if "FAILED" in result:
                self.stats["errors"].append(f"{entity} failed {skill}: {result}")
            else:
                self.stats["skill_usage"][skill] += 1

        elif e_type == "COMBAT_DETAIL":
            source = data.get("source", "Auto-Attack")
            dmg = data.get("final", 0)
            self.stats["damage_per_skill"][source].append(dmg)

        elif e_type == "RESOURCE_DELTA":
            res = data.get("resource")
            amt = data.get("amount", 0)
            self.stats["resource_deltas"][res][entity] += amt

        elif e_type == "STATUS_CHANGE":
            effect = data.get("effect_id")
            action = data.get("action")
            if action == "applied":
                self.stats["status_effects"][effect] += 1

        elif e_type == "BUG_REPORT":
            self.stats["bug_reports"].append({
                "time": event.get("time"),
                "entity": entity,
                "msg": data.get("note"),
                "coords": data.get("coords")
            })

    def _generate_report(self):
        report = [f"## Telemetry Summary - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
        
        # 1. Skill Performance
        report.append("\n### Skill Performance")
        for skill, count in self.stats["skill_usage"].most_common(5):
            dmgs = self.stats["damage_per_skill"].get(skill, [0])
            avg_dmg = sum(dmgs) / len(dmgs) if dmgs else 0
            report.append(f"- **{skill}**: {count} casts | Avg Dmg: {avg_dmg:.1f}")

        # 2. Bug Reports
        if self.stats["bug_reports"]:
            report.append("\n### Active Bug Reports")
            for bug in self.stats["bug_reports"][-5:]:
                report.append(f"- [{bug['time']}] {bug['entity']} @ {bug['coords']}: *{bug['msg']}*")

        # 3. Failures & Anomalies
        if self.stats["errors"]:
            report.append("\n### Recent Failures")
            for err in self.stats["errors"][-5:]:
                report.append(f"- {err}")

        # 4. Status Frequency
        report.append("\n### Top Status Effects")
        for eff, count in self.stats["status_effects"].most_common(5):
            report.append(f"- {eff.title()}: {count} occurrences")

        return "\n".join(report)

if __name__ == "__main__":
    aggregator = TelemetryAggregator()
    print(aggregator.process())
