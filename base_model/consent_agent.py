from base_agent import BaseChefAgent

class ConsentChefAgent(BaseChefAgent):
    """
    ConsentChefAgent can comply with consent.
    Hence it implements/overrides related functions so that it can update truth values, etc.
    """
    def __init__(self, model, cell, goals=..., sovereigned_resources=...):
        super().__init__(model, cell, goals, sovereigned_resources)

    