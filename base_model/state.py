from atom import Atom

class EnvState:
    """
    The environment state is represented as a set of propositional atoms.
    """
    def __init__(self):
        self.atoms = {}

    def set_true(self, atom:Atom):
        """
        This function sets the atom to True by adding it to the atoms list.
        """
        # Make the atom true. Doesnt matter if it existed with value False before. Just make it True.
        atom.truth = True
        self.atoms[atom.name] = atom

    def set_false(self, atom:Atom):
        """
        This function sets the atom to False by actually making its truth value false.
        We cant just remove from the list because we might need to check the truth values at each step to check if there are temporal violations.
        """
        atom.truth = False
        if atom.name not in self.atoms.keys():
            print(f"Atom {atom.name} does not exist! But you want to make it false, I will let you, but be careful!")
        self.atoms[atom.name] = atom

    def is_true(self, atom_name):
        """
        Return the truth value of an atom.
        """
        if atom_name in self.atoms.keys():
            return self.atoms[atom_name].truth
        return False
    
    def print_state(self):
        print("Current State: \n")
        for key, atom in self.atoms.items():
            print(f"Atom: {key}, Value: {atom.truth}\n")
    

    