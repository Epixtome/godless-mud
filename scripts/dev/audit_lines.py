import os

def find_long_files(directory, limit=300):
    violations = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        lines = f.readlines()
                        if len(lines) > limit:
                            violations.append((path, len(lines)))
                except Exception as e:
                    print(f"Error reading {path}: {e}")
    return violations

if __name__ == "__main__":
    v = find_long_files('logic')
    v.sort(key=lambda x: x[1], reverse=True)
    for path, count in v:
        print(f"{count}: {path}")
