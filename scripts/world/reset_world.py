import os
import glob

# List of zones to keep (core, non-generated zones)
ZONES_TO_KEEP = ["gods_hall.json", "graveyard.json", "catacombs.json"]

def reset_generated_zones():
    """Deletes all generated zone files from the data/zones directory."""
    print("--- Resetting Generated Zones ---")
    
    zone_dir = "data/zones"
    if not os.path.exists(zone_dir):
        print(f"Directory not found: {zone_dir}")
        return 0

    files_to_delete = glob.glob(os.path.join(zone_dir, "*.json"))
    deleted_count = 0
    
    for f_path in files_to_delete:
        basename = os.path.basename(f_path)
        if basename not in ZONES_TO_KEEP:
            os.remove(f_path)
            print(f"Deleted {basename}")
            deleted_count += 1
    
    print(f"Reset complete. {deleted_count} zone files deleted.")
    return deleted_count

if __name__ == "__main__":
    print("WARNING: This will DELETE all generated zones except for core ones.")
    print(f"Kept zones: {', '.join(ZONES_TO_KEEP)}")
    confirm = input("Type 'DELETE' to confirm: ")
    
    if confirm == "DELETE":
        reset_generated_zones()
    else:
        print("Aborted.")
