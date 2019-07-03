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
    def d_mkl_name(self):

        d_index_keep = self.d_index_keep   

        mkl_path = os.getenv("MKLROOT")

        if mkl_path:
            l_path = (f"{mkl_path}/include/mkl_lapack.h", f"{mkl_path}/include/mkl_blas.h")
            regex = r"(?P<name>%s)\s*\((?P<arg>.*?)\);" % '|'.join(map(re.escape,d_index_keep))
            prog = re.compile(regex, re.MULTILINE | re.DOTALL)
        else:
            l_path = ()

        d_mkl_name = dict()
        for path in l_path:
            with open(path, 'r') as f:
                for match in prog.finditer(f.read()):
                    name, argv = match.groups()
                    l_name = [arg.split('*').pop().strip() for arg in argv.split(',') ]
                    d_mkl_name[name] = [l_name[i] for i in d_index_keep[name] ]

        # Default values for argv not find
        for name in set(d_index_keep) - set(d_mkl_name):
              d_mkl_name[name] = [ f'id:{i}' for i in d_index_keep[name] ]

        return d_mkl_name

    @cached_property
    def d_index_keep(self):
        d = {}
        for _, name, *l_argv, time in self.l:
            if name not in d:
                d[name] = [i for i,v in l_argv]
        return d

    def translate_argv(self, name, argv):
        return [ (name, v) for name, (_, v) in zip(self.d_mkl_name[name],argv)]

    def display_raw(self, n):
        headers = ['Name', 'Argv','Time (s)', 'lapack %']
        top_l = heapq.nlargest(n, self.l, key=lambda x: x[-1])
        top = [ (name, self.translate_argv(name,argv), time, (100*time/self.total_time)) for _, name, *argv, time in top_l]
        
        time_partial = sum(time for *_, time, _ in top)
        top.append( ('other', '', self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) ) 

        print ('')
        print (f'Top {n} function by execution time')
        print (tabulate(top, headers))

    def display_merge_argv(self, n):
        headers = ['Name', 'Argv','Count (#)','Time (s)', 'lapack %']
        top = [ (name, self.translate_argv(name,argv), count, time, (100*time/self.total_time)) for (_, name, *argv), (count, time) in self.r0.longuest(n) ]
        time_partial = sum(time for *_, time, _ in top)
        count_partial = sum(count for *_, count, _, _ in top)

        top.append( ('other', '', self.total_count - count_partial, self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) )

        print ('')
        print (f'Top {n} function by execution time (accumulated by arguments)')
        print (tabulate(top, headers))

    def display_merge_name(self, n):
        headers = ['Name','Count (#)','Time (s)', 'lapack %']
        top = [ (name, count, time, (100*time/self.total_time)) for (_, name), (count, time, ) in self.r1.longuest(n) ]

        time_partial = sum(time for *_, time, _ in top)
        count_partial = sum(count for *_, count, _, _ in top)

        top.append( ('other',  self.total_count - count_partial, self.total_time-time_partial, 100 - 100*(time_partial/self.total_time)) )

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
            if t < 1E-6:
                continue

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
