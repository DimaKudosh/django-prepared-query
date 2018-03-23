from weakref import WeakKeyDictionary
from collections import defaultdict


class StatementsPool(defaultdict):
    pass


class StatementsPool(WeakKeyDictionary):
    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            if item:
                self[item] = []
            return super().__getitem__(item)


statements_pool = StatementsPool()
