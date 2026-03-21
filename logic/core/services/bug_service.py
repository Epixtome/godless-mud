import json
import os
from datetime import datetime

class BugService:
    _instance = None
    TICKET_FILE = "data/bugs.json"

    def __init__(self):
        self.tickets = {}
        self.load_tickets()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def load_tickets(self):
        """Loads tickets from JSON database."""
        if os.path.exists(self.TICKET_FILE):
            try:
                with open(self.TICKET_FILE, 'r') as f:
                    data = json.load(f)
                    # Convert keys back to int if they are strings (JSON keys are always strings)
                    self.tickets = {int(k): v for k, v in data.items()}
            except (json.JSONDecodeError, ValueError):
                self.tickets = {}
        else:
            self.tickets = {}

    def save_tickets(self):
        """Persists all tickets to Disk."""
        try:
            with open(self.TICKET_FILE, 'w') as f:
                json.dump(self.tickets, f, indent=4)
        except Exception as e:
            # Fallback for critical failure
            print(f"FAILED TO SAVE TICKETS: {e}")

    def next_id(self):
        """Generates the next sequential ID."""
        if not self.tickets:
            return 1
        return max(self.tickets.keys()) + 1

    def create_ticket(self, player, description):
        """Creates a new bug ticket with full spatial context."""
        tid = self.next_id()
        context = f"{getattr(player.room, 'name', 'Unknown Room')} ({player.room.id})" if player.room else "Unknown"
        self.tickets[tid] = {
            "id": tid,
            "player": player.name,
            "description": description,
            "context": context,
            "state": "open",
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "updates": []
        }
        self.save_tickets()
        return tid

    def append_to_ticket(self, tid, text):
        """Adds an update to an existing ticket."""
        if tid not in self.tickets:
            return False, "Ticket not found."
        
        update = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "text": text
        }
        self.tickets[tid]["updates"].append(update)
        self.save_tickets()
        return True, "Update added."

    def list_tickets(self, show_closed=False):
        """Returns a list of tickets, sorted by ID."""
        t_list = sorted(self.tickets.values(), key=lambda x: x["id"])
        if not show_closed:
            return [t for t in t_list if t["state"] == "open"]
        return t_list

    def get_ticket(self, tid):
        """Retrieves a single ticket by ID."""
        return self.tickets.get(tid)

    def close_ticket(self, tid):
        """Marks a ticket as closed."""
        if tid in self.tickets:
            self.tickets[tid]["state"] = "closed"
            self.save_tickets()
            return True
        return False

    def delete_ticket(self, tid):
        """Permanently removes a ticket."""
        if tid in self.tickets:
            del self.tickets[tid]
            self.save_tickets()
            return True
        return False
