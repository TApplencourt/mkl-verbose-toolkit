#!/usr/bin/env python
import sys
import re
import os
from collections import defaultdict, Counter
from itertools import chain, islice
from tabulate import tabulate

#  _
# |_) _. ._ _ o ._   _    |   _   _
# |  (_| | _> | | | (_|   |_ (_) (_|
#                    _|           _|
def parse_file(f,thr_time = 1.e-9):

    d_time = {'ns':1.e-9,
              'us':1.e-6,
              'ms':1.e-3,
              's': 1}

    d_argv = defaultdict(list)
    d_index_keep = {}
    tot_time = 0

    regex = r"^MKL_VERBOSE (?!Intel)(?P<name>\w+?)\((?P<args>.*)\) (?P<time>\S+?)(?P<exp>[a-z]+)"
    prog_mkl = re.compile(regex)

    regex = r"^MKL_VERBOSE FFT.+?\|(.*?)\|"
    prog_fft = re.compile(regex)

    fft_c = Counter()
    for line in f:

        # BLAS / LAPCACK
        mkl = prog_mkl.search(line)
        if mkl:
        
            name, argv, t, exp = mkl.groups()

            # Time
            t2 =  float(t)*d_time[exp]
            tot_time += t2

            # Update d_argv
            if t2 >= thr_time:
                l = [ (i, int(s) ) for i,s in enumerate(argv.split(',')) if s.isdigit() or (s.startswith('-') and s[1:].isdigit()) ] 
                l_idx, l_val = zip(*l)
                if name not in d_index_keep or (len(l_idx) < len(d_index_keep[name])):
                    d_index_keep[name] = l_idx

                d_argv[name].append(l_val+ (t2,) )

        # FFT
        fft = prog_fft.search(line)
        if fft:
            data = fft.group(1).strip()
            fft_c.update([data])

    return d_argv, d_index_keep, tot_time, fft_c

#  _                                                      
# |_) _. ._ _  _    |\/| |/ |    |_|  _   _.  _|  _  ._ _ 
# |  (_| | _> (/_   |  | |\ |_   | | (/_ (_| (_| (/_ | _> 
#                                                         
def get_label_for_argv(d_index_keep):
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

    # Default values
    for name in set(d_index_keep) - set(d_mkl_name):
          d_mkl_name[name] = [ f'No{i}' for i in d_index_keep[name] ]

    return d_mkl_name

#  _
# | \ o  _ ._  |  _.
# |_/ | _> |_) | (_| \/
#          |         /

def table_accumulation(l_fct, d_agreg):
    table_accu = []
    for fct_name in l_fct:
        n, t = d_agreg[fct_name]
        table_accu.append( [fct_name, n, t, f"{t/tot_time:.0%}"] )
    return tabulate(table_accu,headers=["Name fct","n","Time (s)","Tot_time (%)"])


def table_min_max(l_fct, d_argv, d_mkl_name):

    table_mm = []
    for name_fct in l_fct:
        l_argv = zip(*d_argv[name_fct])
        l_name = d_mkl_name[name_fct]

        for name_argv, argv in zip(l_name,l_argv):
            table_mm.append( [name_fct, name_argv, min(argv),max(argv) ] )

    return tabulate(table_mm,headers=["Name fct","Name_argv","Min", "Max" ])

def table_accumulation_argv(d_argv, d_mkl_name, thr):
    '''
    For sake of memory we store only a buffer of Thr value
    containt the count and total time of a specific argument for a specific function
    '''
    d_buffer = {}
    for name, l_argv in d_argv.items():

        d = defaultdict(list)
        for *argv,time in l_argv:
            d[tuple(argv)].append(time)

        # Create a tempory dictionary with the cumulative time and number of occurance,
        # Then update the buffer and truncate it to keep the Thr greasted time
        d_buffer.update( ( (name,k),(sum(v), len(v)) ) for k,v in d.items())
        d_buffer = dict(sorted(d_buffer.items(), key=lambda k: k[1][0], reverse = True)[:thr])

    table = [ [n, list(zip(d_mkl_name[n],argv)), c, t, f"{t/tot_time:.0%}"] for (n,argv),(t,c) in d_buffer.items() ]

    partial_time = sum(t for t,_ in d_buffer.values())
    table.append(["Misc", "", "", tot_time - partial_time, f"{1-(partial_time/tot_time):.0%}"])

    return tabulate(table, headers=["Name fct","Argv", "Count","Time (s)", "Time (%)"])

def table_fft(c):
    return tabulate(c.items(), headers=["fft", "count"])

if __name__ == '__main__':
    import argparse

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

    thr = 5
    d_argv, d_index_keep, tot_time, fft = parse_file(f)
    if d_index_keep:
        d_mkl_name = get_label_for_argv(d_index_keep)

        # Table accumulation
        i_agreg = ( (name, ( len(k), sum(i[-1] for i in k) )) for name,k in d_argv.items())
        d_agreg = dict(sorted(i_agreg, key=lambda x: x[1][-1],reverse=True))

        l_fct = list(islice(d_agreg, thr))
        print ("--Group by function--")
        print (table_accumulation(l_fct,d_agreg))
        print ("")
        # Table min / max
        print ("--Min Max arguments of function--") 
        print (table_min_max(l_fct, d_argv, d_mkl_name))
        print ("")

        # Table accu by argv
        print ("--Group by arguments--")
        print (table_accumulation_argv(d_argv, d_mkl_name,thr))
        print ("")

    # fft
    if fft:
        print ("--FFT information--")
        print (table_fft(fft))
        print ("")
