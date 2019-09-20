#!/usr/bin/env python3

from typing import Dict, Tuple, Generator, TextIO, Match, Iterator
import re, heapq

from tabulate import tabulate
from mvt.reducer import Reducer
from mvt.cached_property import cached_property
import os

class displayMKL():

    @cached_property
    def total_time(self):
        return sum(time for *_, time in self.l)

    @cached_property
    def total_count(self):
        return len(self.l)


class displayBLAS(displayMKL):

    def __init__(self, l):
        self.l = l
        self.r0 = Reducer(l)
        self.r1 = Reducer(self.r0, {k: (0, 1) for k, *_ in self.r0})  

    @cached_property
    def d_index_keep(self):
        """
        For each LAPCAK/BLAS call, return a index argument who are not pointer.
        """
        d_index_keep = {}
        for _, name, *l_argv, _ in self.l:
            if name not in d_index_keep:
                d_index_keep[name] = [i for i, _ in l_argv]
        return d_index_keep


    @cached_property
    def d_mkl_name(self):
        """Return for each LAPCAK/BLAS the name of the arguments.

        For performance raison and readability raison, we will return 
            - only the BLAS call used by the program,
            - only the arguments who are not pointer     

        We will try to parse MKL header file to get meanings full argmuments name,
        if not we will return the index of the arguments

        Without MKL_ROOT:
            'DGETRI': ['id:0', 'id:2', 'id:5', 'id:6']
        With MKL_ROOT:

        """ 

        # Default dict
        d_index_keep = self.d_index_keep   
        d_mkl_name = { name: list(map(lambda i: f'id:{i}',l_index)) for name, l_index in d_index_keep.items()}


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

                    d_mkl_name[name] = list(map(parse_index_name,d_index_keep[name]))

        return d_mkl_name

    def translate_argv(self, name, argv):
        return [ (name, v) for name, (_, v) in zip(self.d_mkl_name[name],argv)]

    def display_raw(self, n):
        headers = ['Name', 'Argv','Time (s)', '%']
        top_l = heapq.nlargest(n, self.l, key=lambda x: x[-1])
        top = [ (name, self.translate_argv(name,argv), time, (100*time/self.total_time)) for _, name, *argv, time in top_l]
        
        time_partial = sum(time for *_, time in top_l)
        top.append( ('other', ' ', self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) ) 

        print ('')
        print (f'Top {n} function by execution time')
        print (tabulate(top, headers))

    def display_merge_argv(self, n):
        headers = ['Name', 'Argv','Count (#)','Time (s)', '%']
        top = [ (name, self.translate_argv(name,argv), count, time, (100*time/self.total_time)) for (_, name, *argv), (count, time) in self.r0.longuest(n) ]
        time_partial = sum(time for *_, time, _ in top)
        count_partial = sum(count for *_, count, _, _ in top)

        top.append( ('other', '', self.total_count - count_partial, self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) )

        print ('')
        print (f'Top {n} function by execution time (accumulated by arguments)')
        print (tabulate(top, headers))

    def display_merge_name(self, n):
        headers = ['Name','Count (#)','Time (s)', '%']
        top = [ (name, count, time, (100*time/self.total_time)) for (_, name), (count, time, ) in self.r1.longuest(n) ]

        time_partial = sum(time for *_, time, _ in top)
        count_partial = sum(count for *_, count, _, _ in top)

        if self.total_count - count_partial:
            top.append( ('other',  self.total_count - count_partial, self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) )
        else:
            top.append( ('other', 0, 0, 0)) 

        print ('')
        print (f'Top {n} function by execution time (accumulated by names)')
        print (tabulate(top, headers))
    
class displayFFT(displayMKL):

    def __init__(self, l):
        self.l = l
        self.r0 = Reducer(l)

    def display_raw(self, n):
        top = heapq.nlargest(n, self.l, key=lambda x: x[-1])
        top_one_collumn = [ (*argv, time, (100*time/self.total_time)) for _, *argv, time in top]
        headers = ['precision','domain','direction','placement','dimensions','Time (s)', '%']
        print ('')
        print (f'Top {n} FFT call by execution time')
        print (tabulate(top_one_collumn, headers))

    def display_merge_argv(self, n):
        headers = ['precision','domain','direction','placement','dimensions', 'Count (#)','Time (s)', '%']
        top = ( (*argv, count, time, (100*time/self.total_time)) for (_, *argv), (count, time) in self.r0.longuest(n) )
        print ('')
        print (f'Top {n} FFT call  by execution time (accumulated)')
        print (tabulate(top, headers))

def regex_iter(f: TextIO) -> Iterator[ Tuple[Match,Match] ]:
   regex = r"^MKL_VERBOSE (?!Intel)(?P<name>\w+?)\((?P<args>.*)\) (?P<time>\S+?)(?P<exp>[a-z]+)"
   re_mkl = re.compile(regex, re.MULTILINE)

   regex = r"(?P<precision>[sd])(?P<domain>[cr])(?P<direction>[fb])(?P<placement>[io])(?P<dimensions>[\dx]*)"
   re_fft = re.compile(regex)

   d_rosetta_time = {'ns':1.e-9, 'us':1.e-6, 'ms':1.e-3, 's': 1}
   
   for line in f:
        for match in re_mkl.finditer(line):
    
            d_match = match.groupdict()
            t = float(d_match['time']) * d_rosetta_time[d_match['exp']]
            #if t < 1E-6:
            #    continue

            if d_match['name'] != 'FFT':
                yield "lapack", parse_lapack(d_match,t)
            else:
                d_match.update(re_fft.search(d_match['args']).groupdict())
                yield "fft", parse_fft(d_match,t)

d_rosetta_fft = {'s': "Single",
                'd': "Double",
                'c': "Complex",
                'r': "Real",
                'f': "Forward",
                'b': "Backward",
                'i': "in-place",
                'o': "out-of-place"}

def parse_fft(d_match: Dict, t):
    i = (d_rosetta_fft[d_match[name]] for name in ('precision','domain','direction','placement'))
    return tuple(['fft', *i, d_match['dimensions'], t])

def parse_lapack(d_match: Dict, t):

    def parse_lapack_argv(l_args):
        return ( (i,arg) for i, arg in enumerate(l_args.split(',')) if not arg.startswith('0x') )

    return tuple(['lapack',d_match['name'], *parse_lapack_argv(d_match['args']), t ])


def parse_file(f):

    l_fft = []
    l_lapack = []
    for (type_, line) in regex_iter(f):

        if type_ is "lapack":
            l_lapack.append(line)
        elif type_ is "fft":
            l_fft.append(line)

    db = displayBLAS(l_lapack)
    df = displayFFT(l_fft)

    print ('~= SUMMARY ~=')

    headers = ['','Count (#)','Time (s)']
    top =  [ ('BLAS / LAPACK', db.total_count, db.total_time),
             ('FFT', df.total_count, df.total_time) ]
    print (tabulate(top, headers))
    print ('')

    if l_lapack:
        print ('~= BLAS / LAPACK ~=')
        db.display_merge_name(10)
        db.display_merge_argv(10)
        db.display_raw(10)

    print ('')
    if l_fft:
        print ('~= FFT ~=')
        df.display_merge_argv(10)
        df.display_raw(10)

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Generate a summary for "MKL_verbosed" log files. $MKLROOT will be used to match MKL arguments name with respective values.')
    parser.add_argument('filename', nargs='?', help='If filename is not provided, std.in will be used')
    args = parser.parse_args()
    if args.filename:
        f = open(args.filename, 'r')
    elif not sys.stdin.isatty():
        f = sys.stdin
    else:
        parser.print_help()
        sys.exit()

    parse_file(f)
