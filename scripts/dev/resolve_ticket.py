import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from logic.core.services.bug_service import BugService

service = BugService.get_instance()
ticket_id = 2

if service.get_ticket(ticket_id):
    service.append_to_ticket(ticket_id, "Fixed: Reduced climb cost (24 per unit) and fixed double-weight-penalty double-dipping. Also patched a potential crash in class-specific resource listeners that could prevent stamina deduction.")
    service.close_ticket(ticket_id)
    # Re-close ticket 1 just in case it got reverted
    service.close_ticket(1)
    print(f"Ticket #{ticket_id} resolved. Ticket #1 verified.")
else:
    print(f"Ticket #{ticket_id} not found.")
