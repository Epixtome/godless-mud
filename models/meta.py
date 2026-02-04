class Blessing:
    def __init__(self, b_id, name, tier, base_power, scaling, requirements, identity_tags, charges, description, cost=0, deity_id=None, required_class=None):
        self.id = b_id
        self.name = name
        self.tier = tier
        self.base_power = base_power
        self.scaling = scaling          # {"str": 1.5}
        self.requirements = requirements # {"str": 12}
        self.identity_tags = identity_tags # ["paladin"]
        self.charges = charges
        self.description = description
        self.cost = cost
        self.deity_id = deity_id
        self.required_class = required_class

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
    def __init__(self, c_id, name, description, requirements, bonuses, playstyle=""):
        self.id = c_id
        self.name = name
        self.description = description
        self.requirements = requirements # {'tags': {'light': 3}}
        self.bonuses = bonuses # {'str': 2}
        self.playstyle = playstyle

class Deity:
    def __init__(self, d_id, name, kingdom, stat):
        self.id = d_id
        self.name = name
        self.kingdom = kingdom
        self.stat = stat

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
