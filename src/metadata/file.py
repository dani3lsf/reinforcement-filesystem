class File:
    def __init__(self, name, provider, length):
        self.name = name
        self.provider = provider
        self.length = length
        self.accesses = []

    def __repr__(self):
        return "{name: " + self.name + ", " + self.provider + ", " + str(self.accesses) +"}"