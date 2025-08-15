class Atom:
    """
    Atom can be epistemic or temporal. 
    A class definition will be convinient to create various attributes to either.

    Atom naming convention:
    <agent_id>_<resource_id>_<valid_tick_count>
    """
    def __init__(self, name=None, truth=None, agent_id=None, resource_id=None, valid_from=None, valid_to=None):
        self.name = name
        self.truth = truth
        self.agent_id = agent_id
        self.resource_id = resource_id
        self.valid_from = valid_from
        self.valid_to = valid_to