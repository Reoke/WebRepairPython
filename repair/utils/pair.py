class Pair:

    def __init__(self, first, second):
        self.first = first
        self.second = second

    def __eq__(self, other):
        return isinstance(other, Pair) and self.first == other.first and self.second == other.second

    def __hash__(self):
        return hash((self.first, self.second))

