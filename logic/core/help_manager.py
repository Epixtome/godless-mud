
"""
logic/core/help_manager.py
Dynamic Lazy-Loading Help System.
Minimizes memory usage by only loading help entry bodies on-demand.
"""
import json
import os
import logging
from utilities.colors import Colors

logger = logging.getLogger("GodlessMUD")

class HelpManager:
    _instance = None
    _index = {} # keyword -> shard_filename
    _shard_dir = "data/help/"

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(HelpManager, cls).__new__(cls)
            cls._instance.initialize_index()
        return cls._instance

    def initialize_index(self):
        """Builds a map of keywords to shards."""
        self._index = {}
        if not os.path.exists(self._shard_dir):
            logger.error(f"HelpManager: Shard directory {self._shard_dir} missing.")
            return

        for filename in os.listdir(self._shard_dir):
            if not filename.endswith(".json"): continue
            
            try:
                with open(os.path.join(self._shard_dir, filename), 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for entry in data.get('help', []):
                        for keyword in entry.get('keywords', []):
                            self._index[keyword.lower()] = filename
            except Exception as e:
                logger.error(f"HelpManager: Error indexing {filename}: {e}")
        
        logger.info(f"HelpManager: Indexed {len(self._index)} keywords across shards.")

    def get_entry(self, keyword):
        """Lazy-loads an entry from its shard."""
        keyword = keyword.lower()
        shard_file = self._index.get(keyword)
        if not shard_file:
            return None

        try:
            with open(os.path.join(self._shard_dir, shard_file), 'r', encoding='utf-8') as f:
                data = json.load(f)
                for entry in data.get('help', []):
                    if keyword in [k.lower() for k in entry.get('keywords', [])]:
                        return entry
        except Exception as e:
            logger.error(f"HelpManager: Error reading shard {shard_file}: {e}")
        
        return None

    def find_fuzzy_matches(self, search_term):
        """Returns a list of matching entries (lazy-loaded)."""
        search_term = search_term.lower()
        matches = []
        
        # We search the index keys first (fast)
        matching_keywords = [k for k in self._index.keys() if search_term in k]
        
        # Then gather unique entries
        processed_titles = set()
        for kw in matching_keywords:
            entry = self.get_entry(kw)
            if entry and entry['title'] not in processed_titles:
                matches.append(entry)
                processed_titles.add(entry['title'])
        
        return matches

# Singleton shortcut
help_system = HelpManager()
