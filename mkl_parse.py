#!/usr/bin/env python3

from tabulate import tabulate
from mvt.display import displayBLAS, displayFFT
from mvt.parse import parse_iter

def parse_and_display(f,count):

    l_fft = []
    l_lapack = []
    for (type_, line) in parse_iter(f):

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
        db.display_merge_name(count)
        db.display_merge_argv(count)
        db.display_raw(count)

    print ('')
    if l_fft:
        print ('~= FFT ~=')
        df.display_merge_argv(count)
        df.display_raw(count)

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
