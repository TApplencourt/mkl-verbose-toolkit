from typing import Dict, Tuple, TextIO, Match, Iterator
import re
import logging

def stringtosecond(s: str) -> float:
    # Bottle neck of the code
    # This is a "seconde"
    if s[-2].isdigit():
        return float(s[:-1])
    elif s[-2:] == 'ns':
        return float(s[:-2]) * 1.e-9
    elif s[-2:] == 'us':
        return float(s[:-2]) * 1.e-6
    elif s[-2:] == 'ms':
        return float(s[:-2]) * 1.e-3
    else:
        raise ValueError


def tokenizer_mkl_arg(argument):
    '''
    >>> list(tokenizer_mkl_arg("SGEMM(N,N,3072,3072,62,0x7ffe51792158,0x3193990,3072,0x32539a0,64,0x7ffe51792170,0x7fddd45a7080,3072)"))
    [(0, 'N'), (1, 'N'), (2, '3072'), (3, '3072'), (4, '62'), (7, '3072'), (9, '64'), (12, '3072')]
    >>> list(tokenizer_mkl_arg("PDPOTRF(l,1024,(nil),1,1,0x7fff5c591294,0,nb={1024,1024},myid={8,0},process_grid={32,1})"))
    [(0, 'l'), (1, '1024'), (2, 'nil'), (3, '1'), (4, '1'), (6, '0')]
    '''
    inside_tuple = False
    count = 0
    old = 0
    active = False

    # Super ugly, to refractor. Gramar and have fun?
    for i, char in enumerate(argument):

        if char in ",)" and not inside_tuple and active:
            arg = argument[old:i] 
            if argument[old:old+2] != '0x' and not arg.startswith('{'):
                yield count, arg
            count += 1
            active = False
        
        if char in '(=,' and not inside_tuple:
            old = i+1
            active = True
        elif char == '{':
            inside_tuple = True
        elif char == '}':
            inside_tuple = False

def parse_iter(f: TextIO, time_thr = 1e-6 ) -> Iterator[ Tuple[Match,Match] ]:

   d_rosetta_fft = {'s': "Single",
                'd': "Double",
                'c': "Complex",
                'r': "Real",
                'f': "Forward",
                'b': "Backward",
                'i': "in-place",
                'o': "out-of-place"}

   for i,line in enumerate(f):
        if not line.startswith("MKL_VERBOSE"):
            continue
        
        try:
             _, name_argument, time, *_ = line.split()
        except ValueError:
            logging.error(f'Cannot parse line {i}: {line.strip()}. Not a valide MKL_VERBOSE line')
            continue


        if name_argument == 'Intel(R)':
            continue

        try:
            time = stringtosecond(time)
        except (IndexError, AttributeError, KeyError, ValueError):
            logging.error(f'Cannot parse line {i}: {line.strip()}.')
            continue

        if time < time_thr:
            continue

        # Name arguments should be on the form NAME(arguments1,arguments2,...)
        try:
            assert (name_argument.count('(') == name_argument.count(')') )
        except AssertionError:
            logging.error(f'Cannot parse line {i}: {line.strip()}. Missing a closing parenthesis')
            continue
        
        name, arguments = name_argument[:-1].split('(',1)

        if name != 'FFT':
            # Parse MKL argument, do not store pointer arguments.
            """
            MKL_VERBOSE PDPOTRF(l,1024,(nil),1,1,0x7fff5c591294,0,nb={1024,1024},myid={8,0},process_grid={32,1})
            MKL_VERBOSE SGEMM(N,N,3072,3072,62,0x7ffe51792158,0x3193990,3072,0x32539a0,64,0x7ffe51792170,0x7fddd45a7080,3072)
            """
            l_arguments =  list(tokenizer_mkl_arg(arguments.strip()))
            yield "lapack", [ name, *l_arguments, time ] 
        else:
            # TODO handle other argument. tlim?
            '''
            MKL_VERBOSE FFT(scfi7x13,tLim:1,desc:0x514a0c0) 32.49us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:24 
            MKL_VERBOSE FFT(dcbo400*3951,tLim:1,desc:0x514a0c0) 32.49us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:24 
            MKL_VERBOSE FFT(dcbo400x400*3951,tLim:1,desc:0x514a0c0) 32.49us CNR:OFF Dyn:1 FastMM:1 TID:0  NThr:24 
            '''
            d = re.match("(?P<precision>[sd])(?P<domain>[cr])(?P<direction>[fb])(?P<placement>[io])(?P<dimensions>[\dx*]*)",arguments).groupdict()
            l_arguments = (d_rosetta_fft[d[n]] for n in ('precision','domain','direction','placement'))
            yield "fft", [ *l_arguments, d['dimensions'],  time] 
