#!/usr/bin/env python3

from typing import Dict, Tuple, Generator, Match, Iterator
import heapq

from tabulate import tabulate
from mvt.reducer import Reducer
from mvt.cached_property import cached_property
import os

class displayMKL(object):

    def __init__(self, l_):
        # ([ ('DGETRF', (0, '3072'), (1, '3072'), (3, '3072'), (5, '0'), 0.37601),
        #    ... ]
        self.l_ = l_

    @cached_property
    def r0_(self):
        # { ('DGESVD', (0, 'S'), (1, 'S') ) : (2, 0.0198),
        #    ... }
        return Reducer(self.l_)

    @cached_property
    def r1_(self):
        # { ('DGESVD' : (9, 4.234),
        #    ... }
        return Reducer(self.r0_, {k: (0, ) for k, *_ in self.r0_})

    @cached_property
    def total_time(self):
        return sum(time for _, time in self.r1_.values())

    @cached_property
    def total_count(self):
        return sum(count for count,_ in self.r1_.values())

    def nlongest(self, n):
        return heapq.nlargest(n, self.l_, key=lambda x: x[-1])



class displayBLAS(displayMKL):

    @cached_property
    def d_index_keep(self):
        """
        For each LAPCAK/BLAS call, return a index argument who are not pointer.
        """
        d_index_keep = {}
        for name, *l_argv in self.r0_:
            if name not in d_index_keep:
                d_index_keep[name] = tuple(idx for idx, _ in l_argv)
        return d_index_keep


    @cached_property
    def d_mkl_name(self):
        """Return for each LAPAK/BLAS the name of the arguments.

        For performance raison and readability raison, we will return 
            - only the BLAS call used by the program,
            - only the arguments who are not pointer     

        We will try to parse MKL header file to get meanings full argmuments name,
        if not we will return the index of the arguments

        Without MKL_ROOT:
            'DGETRI': tuple('id:0', 'id:2', 'id:5', 'id:6')
        With MKL_ROOT:

        """ 
        import re
        # Default dict
        d_index_keep = self.d_index_keep   
        d_mkl_name = { name: tuple(map(lambda i: f'id:{i}',l_index)) for name, l_index in d_index_keep.items() }


        mkl_path = os.getenv("MKLROOT")
        if not mkl_path:
            return d_mkl_name

        # We will parse header file and get the argument name for each BLASK call we do

        """
        BLAS header look like:
        void zlarot_( const MKL_INT* lrows, const MKL_INT* lleft,
              const MKL_INT* lright, const MKL_INT* nl,
              const MKL_Complex16* c, const MKL_Complex16* s,
              MKL_Complex16* a, const MKL_INT* lda, MKL_Complex16* xleft,
              MKL_Complex16* xright );
        """
        regex = r"(?P<name>%s)\s*\((?P<arg>.*?)\);" % '|'.join(map(re.escape,d_mkl_name))
        prog = re.compile(regex, re.MULTILINE | re.DOTALL)


        for path in (f"{mkl_path}/include/mkl_lapack.h", f"{mkl_path}/include/mkl_blas.h"):
            with open(path, 'r') as f:
                for match in prog.finditer(f.read()):
                    name, argv = match.groups()
                    l_argv_name = argv.split(',')

                    def parse_index_name(i):
                        """The i-th argument name will be the last of the line"""
                        return l_argv_name[i].split().pop()

                    d_mkl_name[name] = tuple(map(parse_index_name,d_index_keep[name]))

        return d_mkl_name

    def translate_argv(self, name, argv):
        return [ (name, v) for name, (_, v) in zip(self.d_mkl_name[name],argv)]

    def display_raw(self, n):
        headers = ['Name', 'Argv','Time (s)', '%']
        top_l = self.nlongest(n)
        top = [ (name, self.translate_argv(name,argv), time, (100*time/self.total_time)) for name, *argv, time in top_l]
        
        time_partial = sum(time for *_, time in top_l)
        top.append( ('other', ' ', self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) ) 

        print ('')
        print (f'Top {n} function by execution time')
        print (tabulate(top, headers))


    def peeling_data(self,r,n):
        time_partial = r.partial_time(n)
        count_partial = r.partial_count(n)

        if self.total_count - count_partial:
            return self.total_count - count_partial, self.total_time-time_partial, 100* (1 - (time_partial/self.total_time)) 
        else:
            return  0, 0., 0.

    def display_merge_argv(self, n):
        headers = ['Name', 'Argv','Count (#)','Time (s)', '%']
        top = [ (name, self.translate_argv(name,argv), count, time, (100*time/self.total_time)) for (name, *argv), (count, time) in self.r0_.longuest(n) ]
        top.append( ('other', '',  *self.peeling_data(self.r0_,n) ) )

        print ('')
        print (f'Top {n} function by execution time (accumulated by arguments)')
        print (tabulate(top, headers))

    def display_merge_name(self, n):
        headers = ['Name','Count (#)','Time (s)', '%']
        top = [ (name, count, time, (100*time/self.total_time)) for (name, ), (count, time) in self.r1_.longuest(n) ]
        top.append( ('other',  *self.peeling_data(self.r1_,n) ) )

        print ('')
        print (f'Top {n} function by execution time (accumulated by names)')
        print (tabulate(top, headers))
    
class displayFFT(displayMKL):

    def display_raw(self, n):
        top_one_collumn = [ (*argv, time, (100*time/self.total_time)) for *argv, time in self.nlongest(n)]
        headers = ['precision','domain','direction','placement','dimensions','Time (s)', '%']
        print ('')
        print (f'Top {n} FFT call by execution time')
        print (tabulate(top_one_collumn, headers))

    def display_merge_argv(self, n):
        headers = ['precision','domain','direction','placement','dimensions', 'Count (#)','Time (s)', '%']
        top = ( (*argv, count, time, (100*time/self.total_time)) for argv, (count, time) in self.r0_.longuest(n) )
        print ('')
        print (f'Top {n} FFT call  by execution time (accumulated)')
        print (tabulate(top, headers))
