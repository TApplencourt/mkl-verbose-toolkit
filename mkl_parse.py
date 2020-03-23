#!/usr/bin/env python3

from tabulate import tabulate
from mvt.display import displayBLAS, displayFFT
from mvt.parse import parse_iter
import greenlet
from tqdm import tqdm

def mkl(it_,count):
    db = displayBLAS(line for (type_, line) in it_ if type_ is "lapack")
 
    return (db.total_count, 
            db.total_time,
            db.display_merge_name(count),
            db.display_merge_argv(count),
            db.display_raw(count) )

def fft(it_,count):
    db = displayFFT(line for (type_, line) in it_ if type_ is "fft")
    return (db.total_count,
            db.total_time,
            db.display_merge_argv(count),
            db.display_raw(count) )

def max_and_sum_greenlet(it,count):
    STOP = object()
    consumers = None

    def send(val):
        for g in consumers:
            g.switch(val)

    def produce():
        for elem in parse_iter(tqdm(it)):
            send(elem)
        send(STOP)

    def consume():
        g_produce = greenlet.getcurrent().parent
        while True:
            val = g_produce.switch()
            if val is STOP:
                return
            yield val

    sum_result = []
    max_result = []
    gmax = greenlet.greenlet(lambda: max_result.append(fft(consume(),count)))
    gmax.switch()
    gsum = greenlet.greenlet(lambda: sum_result.append(mkl(consume(),count)))
    gsum.switch()
    consumers = (gsum, gmax)
    produce()

    return sum_result[0], max_result[0]

def parse_and_display(f,count):

    (db_total_count, db_total_time, db_display_merge_name, db_display_merge_argv,  db_display_raw), (df_total_count, df_total_time, df_display_merge_argv, df_display_raw) = max_and_sum_greenlet(f, count) 

    print ('~= SUMMARY ~=')

    headers = ['','Count (#)','Time (s)']
    top =  [ ('BLAS / LAPACK', db_total_count, db_total_time),
             ('FFT', df_total_count, df_total_time) ]
    print (tabulate(top, headers))
    print ('')

    if db_total_count:
        print ('~= BLAS / LAPACK ~=')
        print (db_display_merge_name)
        print (db_display_merge_argv)
        print (db_display_raw)

    print ('')
    if df_total_count:
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
