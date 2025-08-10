class Atom:
    """
    Atom can be epistemic or temporal. 
    A class definition will be convinient to create various attributes to either.

    Atom naming convention:
    <agent_id>_<resource_id>_<valid_tick_count>
    """
    def __init__(self, name, truth, agent, resource, valid_from, valid_to):
        self.name = name
        self.truth = truth # TODO: If existence in set is enough then truth might not be needed.
        self.agent = agent # TODO: Might be depricated if naming is enough
        self.resource = resource # TODO: Might be depricated if naming is enough 
        self.valid_from = valid_from
        self.valid_to = valid_to # If none, then no time constraint on the atom

        # TODO: We need to count ticks somehow or maybe if I can use ticks directly I can just compare to valid_to.
        # But then valid_to must be passed during Atom initation.