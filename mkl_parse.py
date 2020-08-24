#!/usr/bin/env python3

from tabulate import tabulate
from mvt.display import BLASApothecary, FFTApothecary
from mvt.parse import parse_iter
import greenlet
from tqdm import tqdm

def mkl(it,count):
    db = BLASApothecary( (line for (type_, line) in it if type_ is "lapack"), n=count)
 
    return (db.total_stock, 
            db.display_merge_name(count),
            db.display_merge_argv(count),
            db.display_raw() )

def fft(it,count):
    db = FFTApothecary( (line for (type_, line) in it if type_ is "fft"), n=count)
    return (db.total_stock,
            db.display_merge_argv(count),
            db.display_raw() )

def mkl_greenlet(it,count):
    # https://morestina.net/blog/1378/parallel-iteration-in-python

    STOP = object()

    def consume():
        g_produce = greenlet.getcurrent().parent
        while True:
            val = g_produce.switch()
            if val is STOP:
                return
            yield val

    mkl_result, fft_result = [], []
    gmkl = greenlet.greenlet(run = lambda: mkl_result.append(mkl(consume(),count)))
    gfft = greenlet.greenlet(run = lambda: fft_result.append(fft(consume(),count)))
    
    consumers = (gmkl, gfft)

    # Start the greenlet
    for g in consumers:
        g.switch()

    # Switch betwen the FFT and BLAS
    for elem in parse_iter(tqdm(it,unit=" line")):
        for g in consumers:
            g.switch(elem)

    # Signal the greenlet to stop
    for g in consumers:
        g.switch(STOP)

    return mkl_result[0], fft_result[0]

def parse_and_display(f,count):

    (db_total_stock, db_display_merge_name, db_display_merge_argv,  db_display_raw), (df_total_stock, df_display_merge_argv, df_display_raw) = mkl_greenlet(f, count) 

    print ('~= SUMMARY ~=')

    headers = ['','Count (#)','Time (s)']
    top =  [ ('BLAS / LAPACK', db_total_stock.count, db_total_stock.time),
             ('FFT', df_total_stock.count, df_total_stock.time) ]
    print (tabulate(top, headers))
    print ('')

    if db_total_stock.count:
        print ('~= BLAS / LAPACK ~=')
        print (db_display_merge_name)
        print (db_display_merge_argv)
        print (db_display_raw)

    print ('')
    if df_total_stock.count:
        print ('~= FFT ~=')
        print (df_display_merge_argv)
        print (df_display_raw)

if __name__ == '__main__':
    import argparse
    import sys

    parser = argparse.ArgumentParser(description='Generate a summary for "MKL_verbosed" log files. $MKLROOT will be used to match MKL arguments name with respective values.')
    parser.add_argument('filename', nargs='?', help='If filename is not provided, std.in will be used')
    parser.add_argument("-n", "--num_routines", metavar="#",
                        help="The number of routines to print out", type=int, default=10)

    args = parser.parse_args()
    if args.filename:
        f = open(args.filename, 'r')
    elif not sys.stdin.isatty():
        f = sys.stdin
    else:
        parser.print_help()
        sys.exit()

    parse_and_display(f, args.num_routines)
