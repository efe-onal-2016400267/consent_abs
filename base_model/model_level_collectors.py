
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

    return sum(conflict.conflict_count for conflict in model.model_level_resource_conflict_list)

def model_level_resource_conflict_accomplished_counter_goals(model):
    """
    Returns the total number of counter goals accomplished during resource conflicts in the simulation.
    E.g. Agent1 lends egg1 to Agent2. Agent2 does not relase the resource so Agent1 cannot accomplish a goal using egg1. 
        Every goal Agent2 accomplishes after the conflict was activated will be counted as a "counter goal".
    """
    return len(model.model_level_accomplished_counter_goal_list)

# Collector functions for norm states, model level
def model_level_AU_activations_hist(model):
    """
    Returns model level AU activation counts for reporting. Historically. How many activations from the beginning.
    """
    return model.norm_state_counter["AU"]["ever_active"]

def model_level_active_AU(model):
    """
    Returns model level AU activation counts for reporting. The currently active AUs.
    """
    model_level_active_AU = 0
    for CI in model.living_consents:
        for n in CI.N:
            if n.type == "AU" and n.active and CI.state == "ACTIVE":
                model_level_active_AU = model_level_active_AU + 1
    return model_level_active_AU

def model_level_AU_vioaltions(model):
    """
    Returns model level AU violation counts for reporting.
    """
    return model.norm_state_counter["AU"]["violated"]

def model_level_AU_expirations(model):
    """
    Returns model level AU expiration counts for reporting.
    """
    return model.norm_state_counter["AU"]["expired"]

def model_level_AU_fulfilments(model):
    """
    Returns model level AU fulfilments counts for reporting.
    """
    return model.norm_state_counter["AU"]["fulfilled"]

def model_level_CO_activations_hist(model):
    """
    Returns model level CO activations counts for reporting. Historically. How many activations from the beginning.
    """
    return model.norm_state_counter["CO"]["ever_active"]

def model_level_active_CO(model):
    """
    Returns model level CO activation counts for reporting. The currently active COs.
    """
    model_level_active_CO = 0   
    for CI in model.living_consents:
        for n in CI.N:
            if n.type == "CO" and n.active and CI.state == "ACTIVE":
                model_level_active_CO = model_level_active_CO + 1
    return model_level_active_CO

def model_level_CO_violations(model):
    """
    Returns model level CO violations counts for reporting.
    """
    return model.norm_state_counter["CO"]["violated"]

def model_level_CO_fulfilments(model):
    """
    Returns model level CO fulfilments counts for reporting.
    """
    return model.norm_state_counter["CO"]["fulfilled"]



# I could create all the consent count functions compactly but in a less readable manner:
for state in ["ACTIVE", "FULFILLED", "VIOLATED", "UNREALIZED", "DEFERRED"]:
    globals()[f"model_level_{state.lower()}_consents"] = lambda model, s=state: sum(1 for CI in model.living_consents if CI.state==s)

def model_level_total_consents_activations_hist(model):
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
