#!/usr/bin/env python
import sys
import re, mmap
from collections import defaultdict
from collections import Counter
from itertools import chain

# Parse mkl header
l_path = ["/soft/compilers/intel/mkl/include/mkl_lapack.h", "/soft/compilers/intel/mkl/include/mkl_blas.h"]

d_mkl = dict()
regex = r"(?P<name>\S+)\((?P<arg>.*?)\);"

for path in l_path:
    with open(path, 'r') as f:
     data = f.read() 
     for match in re.finditer(regex, data, re.MULTILINE | re.DOTALL):
         name, argv = match.groups()
         #argv = const char* job, const MKL_INT* n, double* a, const MKL_INT* lda,

         # Do the parsing to to random space
         l = []
         for i,arg in enumerate(argv.split(',')):
             regex2= r"const\s+MKL_INT\s*\*\s*(\S+)"
             m = re.search(regex2, arg.strip())
             if m:
                 l.append( (i,m.group(1) ) )
         d_mkl[name] = list(zip(*l)) 

# End parsing mkl
def convtoseonc(i,p):
    d = {'ns':10**(-9),
         'us':10**(-6),
         'ms':10**(-3),
         's': 1}
 
    return float(i)*d[p]

d_argv = defaultdict(list) #defaultdict(dict)
d = defaultdict(list)
regex = r"^MKL_VERBOSE (?!Intel)(?P<name>\S+?)\((?P<args>.*)\)\s(?P<time>\S+?)(?P<exp>[a-z]+)"

thr_time = 1.e-9

d_mkl_name = {}

with open(sys.argv[1], 'r') as f:
    for line in f:

      m = re.search(regex, line, re.MULTILINE)
      if not m:
          continue

      name, argv, t,exp = re.search(regex, line, re.MULTILINE).groups()
      t2 = convtoseonc(t,exp)
      if t2 >= thr_time:
        l = argv.split(',')

        l2 = []
        l3 = []
        for idx,n in zip(*d_mkl[name]):
            if 'x' not in l[idx]:
                l2.append(int(l[idx]))
                l3.append(n)

        d_mkl_name[name]=l3
        d_argv[name].append(l2+ [t2])


# Print agreagate function
d_agreg = {name: ( len(k), sum(i[-1] for i in k) ) for name,k in d_argv.items()}

d4 = defaultdict(float)
d4_b = defaultdict(int)

for name, l_argv in d_argv.items():
    for *argv,time in l_argv:
        d4[(name,tuple(argv)) ] += time
        d4_b[(name, tuple(argv))] += 1

from collections import Counter

d_count_argv_imp = defaultdict(dict)
for name_fct,l_argv in d_argv.items():
    l_name = d_mkl_name[name_fct]
    for i, name in enumerate(l_name):
        d_count_argv_imp[name_fct][name]= Counter(argv[i] for argv in l_argv)

thr = 5

from tabulate import tabulate
tot_time = sum(i[-1] for i in d_agreg.values())

# Display table 2
table2 = []
for name_fct, (count, time) in d_agreg.items():
    table2.append([name_fct,count, time, "{:.0%}".format(time/tot_time) ])

table2 = sorted(table2, key=lambda ele: ele[-2], reverse=True)[:thr]
print (tabulate(table2,headers=["Name fct","n","tot_time","tot_time %"]))



table = [ ["Name fct","Name_argv","Min", "Max" ] ]
for name_fct, *_ in table2:
    for name_argv, c in d_count_argv_imp[name_fct].items():
        n = sum(c.values())

        table.append( [name_fct, name_argv, min(c.values()), max(c.values()) ] )

print (tabulate(table,headers="firstrow"))

table = sorted(([n, list(zip(d_mkl_name[n],argv)), d4_b[(n,argv)], v] for (n,argv),v in d4.items()), key = lambda ele: ele[-1], reverse = True)

partial_time = sum(i[-1] for i in table[:thr])
table_f = table[:thr] + [["Misc", "", "", tot_time - partial_time]]

print (tabulate( ([f, a, c, "{:.3}".format(v), "{:.0%}".format(v/tot_time) ] for f,a,c,v in table_f),headers=["Name fct","Argv", "Count","time (s)", "time (%)"]))
