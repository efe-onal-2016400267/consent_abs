class Action:
    """
    An action t consists of a list of truth values for certain atoms and a list of affected (used) resources.
    t = <truth_list, resources>
    """
    def __init__(self, truth_list=None, resources=None):
        self.truth_list = truth_list
        self.resources = resources
