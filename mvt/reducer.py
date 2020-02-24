from typing import Tuple, Iterator, List, Iterable, Mapping
from functools import lru_cache
import heapq

Sum, Count = float, int

class Reducer(dict):

    def __init__(self, iter_, dict_index = {}):
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
            idx_master_key = 0
            l_index =  dict_index.get(elems[idx_master_key], range(len(elems))) 
            return tuple(elems[i] for i in l_index)

        def parse(iter_: Iterable) ->  Iterator[Tuple[Sum, Count] ]:
            '''
            Generate the key, the count, and the Sum of the current line
            '''
            if isinstance(iter_, Mapping):
                for elems, (count, sum_) in iter_.items():
                    yield filter_e(elems), count, sum_
            elif isinstance(iter_,Iterable):
                for *elems, sum_ in iter_:
                    yield filter_e(elems), 1, sum_

        default_count, default_sum_ = (0,0)

        for trimed_elem, count, sum_ in parse(iter_):        
            cur_count, cur_sum = self.get(trimed_elem, (default_count,default_sum_)) 
            self[trimed_elem] = (cur_count + count, cur_sum + sum_)

    def __hash__(self):
        return hash(frozenset(self))

    @lru_cache()
    def longuest(self,n) -> List[Tuple]:
        return heapq.nlargest(n, self.items(), key=lambda x: x[1][1])

    @lru_cache()
    def partial_time(self,n):
        top = self.longuest(n)   
        return sum(time for _, (_, time) in top)

    @lru_cache()
    def partial_count(self,n):
        top = self.longuest(n)        
        return sum(count for _, (count, _) in top)


