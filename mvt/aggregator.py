from typing import Tuple, Iterator, List, Iterable, Mapping
from functools import lru_cache
import heapq
from typing import NamedTuple
from operator import itemgetter

Sum, Count = float, int

class Stock(NamedTuple):
    count: int
    time: str

    def __add__(self, other):
        return Stock(self.count + other.count, self.time + other.time)

class Aggregator(dict):

    # Act as a default dict
    def __missing__(self, key):
        return Stock(0,0.)

    def __init__(self, iter_, l_index = None, n = 10):
        # Save the count and sum

        '''
        >>> Aggregator([('a','b',1.),
        ...             ('a','b',4.), 
        ...             ('a','c',3.)])
        {('a', 'b'): (2, 5.0), ('a', 'c'): (1, 3.0)}

        >>> Aggregator([('a','b',1.),
        ...             ('a','b',4.), 
        ...             ('a','c',3.)],
                        l_index=[0]}
        {('a',): (3, 8.0) }
        '''

        def parse(iter_: Iterable) ->  Iterator[Tuple[Sum, Count] ]:
            '''
            Generate the key, the count, and the Sum of the current line
            '''

            if isinstance(iter_, Aggregator):
                for elems, stock in iter_.items():
                    yield elems, stock
            elif isinstance(iter_,Iterable):
                for *elems, time in iter_:
                    yield elems, Stock(1, time)

        self.longuest_not_aggregated = []

        for elems, stock in parse(iter_):

            key =  tuple(elems[i] for i in l_index) if l_index else tuple(elems)
            self[key] += stock
            # Take a working list of the top n
            f = heapq.heappush if len(self.longuest_not_aggregated) < n else heapq.heapreplace
            f(self.longuest_not_aggregated, (stock.time, *elems ) )

        # By construction 'longuest_not_aggregated' containt the 'N' larger items. They are not sorted.
        # To sort  in a diminishing sequence them we can use `heappop` and then reversee the list,
        # But for simplicity we use sorted + reverse
        self.longuest_not_aggregated = sorted(self.longuest_not_aggregated, reverse=True)

    # So this can be 'hashable' and sended by greenlet
    def __hash__(self):
        return hash(frozenset(self))

    @lru_cache()
    def longuest(self,n) -> List[Tuple]:
        return heapq.nlargest(n, self.items(), key=lambda x: x[1].time)

    @lru_cache()
    def partial_stock(self,n):
        return sum(map(itemgetter(1),self.longuest(n)), Stock(0,0.))

