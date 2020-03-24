from typing import Tuple, Iterator, List, Iterable, Mapping
from functools import lru_cache
import heapq
from typing import NamedTuple

Sum, Count = float, int

class Stock(NamedTuple):
    count: int
    sum_: str

class Reducer(dict):

    def __init__(self, iter_, dict_index = {}, n = 10):
        # Save the count and sum

        '''
        >>> Reducer([('a','b',1.),
        ...          ('a','b',4.), 
        ...          ('a','c',3.)])
        {('a', 'b'): (2, 5.0), ('a', 'c'): (1, 3.0)}

        >>> Reducer([('a','b',1.), ('a','c',3.)], 
        ...         {'a':(0,)})
        {('a',): (2, 4.0)}
        '''

        def filter_e(elems: Iterable) -> Tuple:
            '''
            Filter the list of elements by the indexes stored in dict_index
            '''
            l_index =  dict_index.get(elems[0], range(len(elems))) 
            return tuple(elems[i] for i in l_index)

        def parse(iter_: Iterable) ->  Iterator[Tuple[Sum, Count] ]:
            '''
            Generate the key, the count, and the Sum of the current line
            '''
            if isinstance(iter_, Mapping):
                for elems, (count, sum_) in iter_.items():
                    yield filter_e(elems), Stock(count, sum_), elems
            elif isinstance(iter_,Iterable):
                for *elems, sum_ in iter_:
                    yield filter_e(elems), Stock(1, sum_), elems

        self.max_values = []

        for key, stock, elems in parse(iter_):        
            cur_s = self[key]
            self[key] = Stock(cur_s.count + stock.count, cur_s.sum_ + stock.sum_)
           
            # Take a working list of the top n
            f = heapq.heappush if len(self.max_values) < n else heapq.heapreplace
            f(self.max_values, (stock.sum_, (*elems, stock.sum_) ) )

    def __missing__(self, key):
        return Stock(0,0.)

    def __hash__(self):
        return hash(frozenset(self))
    
    @property
    def n_largest(self):
        return [ v for _,v in reversed(self.max_values) ]

    @lru_cache()
    def longuest(self,n) -> List[Tuple]:
        return heapq.nlargest(n, self.items(), key=lambda x: x[1].sum_)

    @lru_cache()
    def partial_time(self,n):
        top = self.longuest(n)   
        return sum(time for _, (_, time) in top)

    @lru_cache()
    def partial_count(self,n):
        top = self.longuest(n)        
        return sum(count for _, (count, _) in top)
