import json
import os

log_file = "logs/telemetry.jsonl"
if os.path.exists(log_file):
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        recent = lines[-200:]
        
        print(f"--- Reviewing Tapes (Last {len(recent)} events) ---")
        for line in recent:
            try:
                event = json.loads(line)
                etype = event.get("type")
                etime = event.get("time")
                edata = event.get("data", {})
                
                if etype == "COMMAND_EXECUTE":
                    print(f"[{etime}] >> COMMAND: {edata.get('command')} {edata.get('args')}")
                elif etype == "ITEM_TRANSFER":
                    print(f"[{etime}] !! TRANSFER: {edata.get('item')} from {edata.get('from')} to {edata.get('to')}")
                elif etype == "ITEM_EQUIP":
                    print(f"[{etime}] ++ EQUIP: {edata.get('item')} in {edata.get('slot')}")
                elif etype == "ITEM_UNEQUIP":
                    print(f"[{etime}] -- UNEQUIP: {edata.get('item')} from {edata.get('slot')}")
                elif etype == "RESOURCE_DELTA":
                    if edata.get('resource') == 'stamina':
                        print(f"[{etime}] .. STAMINA: {edata.get('amount')} (Current: {edata.get('current_value')}) via {edata.get('source')}")
                elif etype == "STAT_SNAPSHOT":
                    print(f"[{etime}] ** SNAPSHOT: Weight Class: {edata.get('weight_class')}")
            except:
                continue
else:
    print("Log file not found.")
