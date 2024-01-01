from bisect import insort, bisect

class PriorityQueue:

    def __init__(self, cost_function):
        self._elems = []
        self._costs = {}
        self._cost_function = cost_function

    def size(self):
        return len(self._elems)

    def pop(self):
        if self.size() <= 0:
            return None
        _, elem = self._elems.pop(0)
        cost = self._costs[elem]
        #print(f"pop: {elem}, {cost}")
        del self._costs[elem]
        return elem, cost

    def peek(self):
        if self.size() <= 0:
            return None
        _, elem = self._elems[0]
        cost = self._costs[elem]
        return elem, cost

    def add(self, elem, cost):
        if elem in self._costs:
            raise(f"trying to insert existing {elem}")
        cost_mod = self._cost_function(cost)
        self._costs[elem] = cost
        #print(f"add: {elem}, {cost}")
        insort(self._elems, (cost_mod, elem))

    def update(self, elem, cost):
        if elem not in self._costs:
            raise Exception(f"trying to update non-existing {elem}")
        old_cost = self._costs[elem]
        old_cost_mod = self._cost_function(old_cost)
        cost_mod = self._cost_function(cost)
        if cost_mod < old_cost_mod:
            # only update if improving
            idx = bisect(self._elems, (old_cost_mod, elem)) - 1
            assert self._elems[idx] == (old_cost_mod, elem)
            del self._elems[idx]
            self._costs[elem] = cost
            #print(f"update: {elem}, {cost}")
            insort(self._elems, (cost_mod, elem))
            return True
        else:
            return False
