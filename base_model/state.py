class EnvState:
    """
    The environment state is represented as a set of propositional atoms.
    The atoms will only exist in name, so the name should be self explanatory with agent ids and resource ids.
    TODO: Open world vs. Closed world.
    """
    def __init__(self):
        self.atoms = set()

    def set_true(self, atom):
        """
        This function sets the atom to True by adding it to the atoms list.
        """
        self.atoms.add(atom)

    def set_false(self, atom):
        """
        This function sets the atom to False by removing it from the atoms list.
        """
        self.atoms.discard(atom)

    def is_true(self, atom):
        """
        Return the truth value of an atom.
        """
        return atom in self.atoms
    

    