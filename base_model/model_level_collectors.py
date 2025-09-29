
def model_level_accomplished_goals(model):
    """
    Returns the total number of accomplished goals in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    accomplished_goals = [len(agent.accomplished_goals) for agent in model.agents]
    return sum(accomplished_goals)


def model_level_remaining_goals(model):
    """
    Returns the total number of remaining goals in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    remaining_goals = [len(agent.remaining_goals) for agent in model.agents]
    return sum(remaining_goals)


def model_level_resource_conflicts(model):
    """
    Returns the total number of resource conflicts in the simulation.
    A resource conflict occurs when an agent cannot accomplish their goal 
    due to another agent holding a resource that the first agent owns (is sovereign over)
    AND the related consent instance is in VIOLATED state.
    """
    resource_conflicts = [agent.num_resource_conflicts for agent in model.agents]
    return sum(resource_conflicts)

# Collector functions for norm states, model level
def model_level_AU_activations(model):
    """
    Returns model level AU activation counts for reporting.
    """
    return sum(agent.norm_state_counter["AU"]["ever_active"] for agent in model.agents)

def model_level_AU_vioaltions(model):
    """
    Returns model level AU violation counts for reporting.
    """
    return sum(agent.norm_state_counter["AU"]["violated"] for agent in model.agents)

def model_level_AU_expirations(model):
    """
    Returns model level AU expiration counts for reporting.
    """
    return sum(agent.norm_state_counter["AU"]["expired"] for agent in model.agents)

def model_level_AU_fulfilments(model):
    """
    Returns model level AU fulfilments counts for reporting.
    """
    return sum(agent.norm_state_counter["AU"]["fulfilled"] for agent in model.agents)

def model_level_CO_activations(model):
    """
    Returns model level CO activations counts for reporting.
    """
    return sum(agent.norm_state_counter["CO"]["ever_active"] for agent in model.agents)

def model_level_CO_violations(model):
    """
    Returns model level CO violations counts for reporting.
    """
    return sum(agent.norm_state_counter["CO"]["violated"] for agent in model.agents)

def model_level_CO_fulfilments(model):
    """
    Returns model level CO fulfilments counts for reporting.
    """
    return sum(agent.norm_state_counter["CO"]["fulfilled"] for agent in model.agents)



# I could create all the consent count functions compactly but in a less readable manner:
for state in ["ACTIVE", "FULFILLED", "VIOLATED", "UNREALIZED", "DEFERRED"]:
    globals()[f"model_level_{state.lower()}_consents"] = lambda model, s=state: sum(1 for CI in model.living_consents if CI.state==s)

def model_level_total_consents(model):
    """
    Returns the total number of active consent instances in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    return len(model.living_consents)

'''
def model_level_active_consents(model):
    """
    Returns the total number of active consent instances in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    active_consents = [CI for CI in model.living_consents if CI.state == "ACTIVE"]
    return len(active_consents)

def model_level_fulfilled_consents(model):
    """
    Returns the total number of active consent instances in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    fulfilled_consents = [CI for CI in model.living_consents if CI.state == "FULFILLED"]
    return len(fulfilled_consents)

def model_level_violated_consents(model):
    """
    Returns the total number of active consent instances in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    violated_consents = [CI for CI in model.living_consents if CI.state == "VIOLATED"]
    return len(violated_consents)

def model_level_unrealized_consents(model):
    """
    Returns the total number of active consent instances in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    unrealized_consents = [CI for CI in model.living_consents if CI.state == "UNREALIZED"]
    return len(unrealized_consents)

def model_level_deferred_consents(model):
    """
    Returns the total number of active consent instances in the simulation.
    Used in NoConsentModel's data collector, inherited by ConsentModel as well.
    """
    deferred_consents = [CI for CI in model.living_consents if CI.state == "DEFERRED"]
    return len(deferred_consents)
'''
