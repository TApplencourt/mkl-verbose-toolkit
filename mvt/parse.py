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
        except (AttributeError, KeyError, ValueError):
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
         
        name, arguments = name_argument[:-1].split('(')

        if name != 'FFT':
            # Parse MKL argument, do not store pointer arguments. 
            l_arguments =  [ (i,arg) for i,arg in enumerate(arguments.split(',')) if not arg.startswith('0x') ]
            yield "lapack", [ name, *l_arguments, time ] 
        else:
            # TODO handle other argument. tlim?
            d = re.match("(?P<precision>[sd])(?P<domain>[cr])(?P<direction>[fb])(?P<placement>[io])(?P<dimensions>[\dx]*)",arguments).groupdict()
            l_arguments = (d_rosetta_fft[d[n]] for n in ('precision','domain','direction','placement'))
            yield "fft", [ *l_arguments, d['dimensions'],  time] 
