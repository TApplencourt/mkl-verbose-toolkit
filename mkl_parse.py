#!/usr/bin/env python
import sys
import re
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

    regex = r"^MKL_VERBOSE (?!Intel)(?P<name>\S+?)\((?P<args>.*)\)\s(?P<time>\S+?)(?P<exp>[a-z]+)"
    prog_mkl = re.compile(regex)

    regex = r"^MKL_VERBOSE FFT.+?\|(.*?)\|"
    prog_fft = re.compile(regex)

    fft_c = Counter()
    for line in f:

        mkl = prog_mkl.search(line)
        if mkl:
        
            name, argv, t, exp = mkl.groups()
            t2 =  float(t)*d_time[exp]
            tot_time += t2

            if t2 >= thr_time:
                l2, l3 = [], []
                for i,s in enumerate(argv.split(',')):
                    if s.isdigit() or (s.startswith('-') and s[1:].isdigit()):
                        l2.append(int(s))
                        l3.append(i)

                if name not in d_index_keep or (len(l3) < len(d_index_keep[name])):
                    d_index_keep[name] = l3

                d_argv[name].append(l2+ [t2])

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
    d_mkl_name = {}    
    # Parse mkl header
    l_path = ["/soft/compilers/intel/mkl/include/mkl_lapack.h", "/soft/compilers/intel/mkl/include/mkl_blas.h"]

    d_mkl = dict()
    regex = r"(?P<name>%s)\s*\((?P<arg>.*?)\);" % '|'.join(map(re.escape,d_index_keep))
    prog = re.compile(regex, re.MULTILINE | re.DOTALL)
    for path in l_path:
        with open(path, 'r') as f:
            data = f.read() 
            for match in prog.finditer(data):
                name, argv = match.groups()
                l_name = [arg.split('*').pop().strip() for arg in argv.split(',') ]

                l_idx = d_index_keep[name]
                d_mkl_name[name] = [l_name[i] for i in l_idx] 
 
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
        l_argv = d_argv[name_fct]
        l_name = d_mkl_name[name_fct]

        for i, name_argv in enumerate(l_name):
            c = Counter(argv[i] for argv in l_argv)
            n = sum(c.values())
            table_mm.append( [name_fct, name_argv, min(c.values()), max(c.values()) ] )

    return tabulate(table_mm,headers=["Name fct","Name_argv","Min", "Max" ])
    
def table_accumulation_argv(d_argv, d_mkl_name, thr):
    d4 = defaultdict(float)
    d4_b = defaultdict(int)

    for name, l_argv in d_argv.items():
        for *argv,time in l_argv:
            key = (name,tuple(argv))
            d4[key] += time
            d4_b[key] += 1

    i_table = ([n, list(zip(d_mkl_name[n],argv)), d4_b[(n,argv)], t, f"{t/tot_time:.0%}"] for (n,argv),t in d4.items())
    table = sorted(i_table, key = lambda ele: ele[-2], reverse = True)[:thr]

    partial_time = sum(i[-2] for i in table)
    table = table + [["Misc", "", "", tot_time - partial_time, f"{1-(partial_time/tot_time):.0%}"]]

    return tabulate(table, headers=["Name fct","Argv", "Count","Time (s)", "Time (%)"])

def table_fft(c):
    return tabulate(c.items(), headers=["fft", "count"])

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Generate a summary for "MKL_verbosed" log files')
    parser.add_argument('filename', nargs='?', help='If filename not provided, std.in will be used')
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
