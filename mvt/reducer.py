from typing import Dict, Tuple, Generator, TextIO, Match, Iterator, List, Iterable, Mapping
import heapq

Weight, Count = float, int

class Reducer(dict):

    def __init__(self, iter_, dict_index = {}):
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

        def parse(iter_: Iterable) ->  Iterator[Tuple[Weight, Count] ]:
            '''
            Generate the key, the count, and the weight of the current line
            '''
            if isinstance(iter_, Mapping):
                for elems, (count, weight) in iter_.items():
                    yield filter_e(elems), count, weight
            elif isinstance(iter_,Iterable):
                for *elems, weight in iter_:
                    yield filter_e(elems), 1, weight

        default_count, default_weigh = (0,0)

        for trimed_elem, count, weight in parse(iter_):        
            cur_count, cur_weight = self.get(trimed_elem, (default_count,default_weigh)) 
            self[trimed_elem] = (cur_count + count, cur_weight + weight)

    def longuest(self,n) -> List[Tuple]:
        return heapq.nlargest(n, self.items(), key=lambda x: x[1][1])


