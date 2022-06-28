#!/usr/bin/env python3

from tabulate import tabulate
from mvt.display import cuBLASApothecary
from mvt.open import open_compressed
from tqdm import tqdm

def parse_iter_blask(f, time_thr = 1e-6):
    import re
    m = f.read()
    regex = i= re.compile(r"^I!.*? (\w+)\(.*?called:$(.*?)^i! Time: .*?(\S+) seconds$", re.MULTILINE | re.DOTALL)


    for match in tqdm(regex.finditer(m),unit=" call"):
        name,args, secondes = match.groups()
        
        if float(secondes) < time_thr:
            continue

        aa = []
        for a in args.splitlines():
            if 'POINTER' in a or not a:
                continue
            l = a.split()
            val = [i.split('=')[-1] for i in l if i.startswith('val=')][-1]
            aa.append(tuple([l[1][:-1],val]))

        yield "cublas", [name, *aa, float(secondes)]


def parse_and_display(f,count):
    it = parse_iter_blask(f)
    db = cuBLASApothecary( (line for (type_, line) in it), n=count)

    db_total_stock = db.total_stock
    db_display_merge_name = db.display_merge_name(count)
    db_display_merge_argv = db.display_merge_argv(count)
    db_display_raw =    db.display_raw()
 
    print ('~= SUMMARY ~=')

    headers = ['','Count (#)','Time (s)']
    top =  [ ('cuBLAS', db_total_stock.count, db_total_stock.time), ]
    print (tabulate(top, headers))
    print ('')

    if db_total_stock.count:
        print ('~= cuBlas')
        print (db_display_merge_name)
        print (db_display_merge_argv)
        print (db_display_raw)

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Generate a summary for "MKL_verbosed" log files. $MKLROOT will be used to match MKL arguments name with respective values.')
    parser.add_argument('filename', nargs='?', help='If filename is not provided, std.in will be used')
    parser.add_argument("-n", "--num_routines", metavar="#",
                        help="The number of routines to print out", type=int, default=10)

    args = parser.parse_args()
    if args.filename:
        f = open_compressed(args.filename, 'rt')
    elif not sys.stdin.isatty():
        f = sys.stdin 
    else:
        parser.print_help()
        sys.exit()

    parse_and_display(f, args.num_routines)
