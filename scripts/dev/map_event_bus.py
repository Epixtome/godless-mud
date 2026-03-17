import os
import ast
from collections import defaultdict

def map_events(search_directory, output_file):
    print(f"Scanning {search_directory} for Event Engine hooks...")
    
    dispatches = defaultdict(list)
    subscriptions = defaultdict(list)

    for root, _, files in os.walk(search_directory):
        for file in files:
            if not file.endswith('.py'):
                continue
                
            path = os.path.join(root, file)
            short_path = os.path.relpath(path, start=os.path.dirname(search_directory))
            
            with open(path, 'r', encoding='utf-8') as f:
                try:
                    tree = ast.parse(f.read(), filename=path)
                except SyntaxError:
                    continue

            for node in ast.walk(tree):
                # Find dispatches: event_engine.dispatch("event_name", ...)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'dispatch':
                        if node.args and isinstance(node.args[0], ast.Constant):
                            event_name = node.args[0].value
                            dispatches[event_name].append(f"{short_path} (Line {node.lineno})")
                            
                # Find subscriptions: event_engine.subscribe("event_name", ...)
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                    if node.func.attr == 'subscribe':
                        if node.args and isinstance(node.args[0], ast.Constant):
                            event_name = node.args[0].value
                            subscriptions[event_name].append(f"{short_path} (Line {node.lineno})")

    # Generate the Markdown Report
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# Godless: Event Bus Topology\n")
        f.write("> Auto-generated Living Artifact mapping Pub/Sub architecture.\n\n")
        
        all_events = sorted(set(list(dispatches.keys()) + list(subscriptions.keys())))
        
        for event in all_events:
            f.write(f"## Event: `{event}`\n")
            f.write("**Dispatched By (Triggers):**\n")
            if event in dispatches:
                for loc in set(dispatches[event]):
                    f.write(f"- {loc}\n")
            else:
                f.write("- *(No direct dispatches found - possibly dynamic)*\n")
                
            f.write("\n**Subscribed By (Listeners):**\n")
            if event in subscriptions:
                for loc in set(subscriptions[event]):
                    f.write(f"- {loc}\n")
            else:
                f.write("- *(No listeners found)*\n")
            f.write("\n---\n")
            
    print(f"Event mapping complete! Artifact saved to {output_file}")

if __name__ == "__main__":
    # Target the logic directory, output to documentation
    map_events("logic", "documentation/system_events.md")