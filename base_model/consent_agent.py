from base_agent import BaseChefAgent
from atom import Atom
from norm import Authorization
from action import Action

class ConsentChefAgent(BaseChefAgent):
    """
    ConsentChefAgent can comply with consent.
    Hence it implements/overrides related functions so that it can update truth values, etc.
    """
    def __init__(self, model, cell, goals=..., sovereigned_resources=...):
        super().__init__(model, cell, goals, sovereigned_resources)

        # maybe some lists to keep track of the related propositions.

    def negotiate(self, other:"ConsentChefAgent", res):
        # Post condition of the action
        p = Atom(name=f"Agent{self.unique_id}--use_{res.type}--", agent_id=self.unique_id)
        # Let giver agent g dont negotiatie at all for now
        # TODO: Implement negotiation strategies
        # TODO: What are c_det and c_exp going to be?
        # c_exp might be time related. Or we can add need atoms. If the owner need the resource back, expiretaion condition becomes true.
        agreement = True
        if agreement:
            c_det = []
            c_exp = []
            return [Authorization(model=self.model, g=other.unique_id, r=self.unique_id, c=tuple(c_det, c_exp), t=Action(p=p, r=res))]
        return []
    
