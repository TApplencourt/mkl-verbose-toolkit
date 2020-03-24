#!/usr/bin/env python3

from tabulate import tabulate
from mvt.reducer import Reducer
from mvt.cached_property import cached_property
import os

class MKLApothecary(object):

    def __init__(self, l_, n = 10):
        # ([ ('DGETRF', (0, '3072'), (1, '3072'), (3, '3072'), (5, '0'), 0.37601),
        #    ... ]
        self.l_ = l_
        self.n = n

    @cached_property
    def functions_arguments(self):
        # { ('DGESVD', (0, 'S'), (1, 'S') ) : (2, 0.0198),
        #    ... }
        return Reducer(self.l_, n=self.n)

    @cached_property
    def functions(self):
        # { ('DGESVD' : (9, 4.234),
        #    ... }
        return Reducer(self.functions_arguments, dict_index={k: (0, ) for k, *_ in self.functions_arguments})

    @cached_property
    def total_time(self):
        return sum(time for _, time in self.functions.values())

    @cached_property
    def total_count(self):
        return sum(count for count,_ in self.functions.values())

    @cached_property
    def nlongest_unique_function(self):
        return self.functions_arguments.n_largest


class BLASApothecary(MKLApothecary):

    @cached_property
    def d_index_keep(self):
        """
        For each LAPCAK/BLAS call, return a index argument who are not pointer.
        """
        d_index_keep = {}
        for name, *l_argv in self.functions_arguments:
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
        d_mkl_name = { name: tuple(map(lambda i: f'id:{i}',l_index)) for name, l_index in self.d_index_keep.items() }


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
              MKL_Complex16* xright ) NOTHROW;
        """
        regex = r"\b(?P<name>%s)\s*\((?P<arg>.*?)\)" % '|'.join(map(re.escape,d_mkl_name))
        prog = re.compile(regex, re.MULTILINE | re.DOTALL)

        for path in (f"{mkl_path}/include/mkl_lapack.h", f"{mkl_path}/include/mkl_blas.h"):
            with open(path, 'r') as f:
                for match in prog.finditer(f.read()):
                    name, argv = match.groups()
                    l_argv_name = argv.split(',')
                    def parse_index_name(i):
                        """The i-th argument name will be the last of the line"""
                        a = l_argv_name[i].split().pop()
                        return a[1:] if a.startswith('*') else a

                    d_mkl_name[name] = tuple(map(parse_index_name,self.d_index_keep[name]))

        return d_mkl_name

    def translate_argv(self, name, argv):
        return [ (name, v) for name, (_, v) in zip(self.d_mkl_name[name],argv)]

    def display_raw(self):
        headers = ['Name', 'Argv','Time (s)', '%']
        top = [ (name, self.translate_argv(name,argv), time, (100*time/self.total_time)) for name, *argv, time in self.nlongest_unique_function]
        
        time_partial = sum(time for *_, time in self.nlongest_unique_function)
        top.append( ('other', ' ', self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) ) 
        return f"\nTop {self.n} functions by execution time\n" + tabulate(top, headers)

    def peeling_data(self,r,n):
        time_partial = r.partial_time(n)
        count_partial = r.partial_count(n)

        if self.total_count - count_partial:
            return self.total_count - count_partial, self.total_time-time_partial, 100* (1 - (time_partial/self.total_time)) 
        else:
            return  0, 0., 0.

    def display_merge_argv(self, n):
        headers = ['Name', 'Argv','Count (#)','Time (s)', '%']
        top = [ (name, self.translate_argv(name,argv), count, time, (100*time/self.total_time)) for (name, *argv), (count, time) in self.functions_arguments.longuest(n) ]
        top.append( ('other', '',  *self.peeling_data(self.functions_arguments,n) ) )
        return f"\nTop {n} functions by execution time (accumulated by arguments)\n" + tabulate(top, headers)
    
    def display_merge_name(self, n):
        headers = ['Name','Count (#)','Time (s)', '%']
        top = [ (name, count, time, (100*time/self.total_time)) for (name, ), (count, time) in self.functions.longuest(n) ]
        top.append( ('other',  *self.peeling_data(self.functions,n) ) )
        return f"\nTop {n} functions by execution time (accumulated by names)\n" + tabulate(top, headers)
    
class FFTApothecary(MKLApothecary):

    def display_raw(self):
        top = [ (*argv, time, (100*time/self.total_time)) for *argv, time in self.nlongest_unique_function]
        headers = ['precision','domain','direction','placement','dimensions','Time (s)', '%']
        return f"\nTop {self.n} FFT calls by execution time\n" + tabulate(top, headers)

    def display_merge_argv(self, n):
        headers = ['precision','domain','direction','placement','dimensions', 'Count (#)','Time (s)', '%']
        top = ( (*argv, count, time, (100*time/self.total_time)) for argv, (count, time) in self.functions_arguments.longuest(n) )
        return f"\nTop {n} FFT calls by execution time (accumulated)\n" + tabulate(top, headers)

