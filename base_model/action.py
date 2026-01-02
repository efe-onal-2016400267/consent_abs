class Action:
    """
    An action t consists of a list of truth values for certain atoms and a list of affected (used) resources.
    t = <p, r>  where p is the list of subgoal atom, also the antecedent of a commitment, and r are the affected resources
    truth
    """
    def __init__(self, p=None, r=None):
        self.p = p
        self.r = r
