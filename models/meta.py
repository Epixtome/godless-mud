class Blessing:
    def __init__(self, id, name, **kwargs):
        self.id = id
        self.name = name
        # Set defaults for core engine fields
        self.tier = kwargs.get('tier', 1)
        self.requirements = kwargs.get('requirements', {})
        self.identity_tags = kwargs.get('identity_tags', [])
        self.charges = kwargs.get('charges', 1)
        self.description = kwargs.get('description', "")
        self.scaling = kwargs.get('scaling', {})
        self.metadata = kwargs.get('metadata', {})
        
        for key, value in kwargs.items():
            setattr(self, key, value)

    def __str__(self):
        return f"{self.name} (T{self.tier})"

class Quest:
    def __init__(self, q_id, name, giver_text, log_text, objectives, rewards):
        self.id = q_id
        self.name = name
        self.giver_text = giver_text
        self.log_text = log_text
        self.objectives = objectives
        self.rewards = rewards

class Class:
    def __init__(self, id, name, **kwargs):
        self.id = id
        self.name = name
        self.description = kwargs.get('description', "")
        
        for key, value in kwargs.items():
            setattr(self, key, value)

class Deity:
    def __init__(self, d_id, name, kingdom):
        self.id = d_id
        self.name = name
        self.kingdom = kingdom

class Synergy:
    def __init__(self, s_id, name, requirements, bonuses):
        self.id = s_id
        self.name = name
        self.requirements = requirements
        self.bonuses = bonuses

class HelpEntry:
    def __init__(self, keywords, title, body, category="system"):
        self.keywords = keywords
        self.title = title
        self.body = body
        self.category = category
