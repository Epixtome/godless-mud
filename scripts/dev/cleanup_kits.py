import json

KITS_FILE = 'data/kits.json'
RETIRED_CLASSES = ['blue_mage', 'grey_mage', 'twin', 'alchemist', 'black_mage', 'priest']

def main():
    with open(KITS_FILE, 'r') as f:
        kits = json.load(f)

    # Move content of retired to active if relevant
    # We already have chemist and cleric shards.

    for retired in RETIRED_CLASSES:
        if retired in kits:
            print(f"Removing retired class: {retired}")
            del kits[retired]

    with open(KITS_FILE, 'w') as f:
        json.dump(kits, f, indent=4)
        
    print("Done!")

if __name__ == "__main__":
    main()
