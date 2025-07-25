class Resource:
    def __init__(self, name, owner=None, type=None):
        self.name = name
        self.owner = owner
        self.in_use_by = None
        self.type = type
        self.id = id(self)