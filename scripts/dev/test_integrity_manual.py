
import logging
from utilities import integrity

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("GodlessMUD")

print("Running Integrity Check...")
result = integrity.check_file_structure()
print(f"Result: {'PASS' if result else 'FAIL'}")
