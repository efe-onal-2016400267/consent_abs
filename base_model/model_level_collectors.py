
def model_level_accomplished_goals(model):
    """
    Returns the total number of accomplished goals in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    accomplished_goals = [agent.num_accomplished_goals for agent in model.agents]
    return sum(accomplished_goals)


def model_level_remaining_goals(model):
    """
    Returns the total number of remaining goals in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    remaining_goals = [agent.num_remaining_goals for agent in model.agents]
    return sum(remaining_goals)