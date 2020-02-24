from typing import Dict, Tuple, TextIO, Match, Iterator
import re
import logging
from functools import lru_cache

@lru_cache()
def stringtosecond(s: str) -> float:
    d_rosetta_time = {'ns':1.e-9, 'us':1.e-6, 'ms':1.e-3, 's': 1}
    value, exposant = re.match(r"([\.\d]+)(.*)", s).groups() 
    return float(value)*d_rosetta_time[exposant]

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
         
        _, name_argument, time, *_ = line.split()
        if name_argument == 'Intel(R)':
            continue

        time = stringtosecond(time)
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
            l_arguments =  [ (i,arg) for i,arg in enumerate(arguments.split(',')) if not arg.startswith('0x') ]
            yield "lapack", [ name, *l_arguments, time ] 
        else:
            # TODO handle other argument. tlim?
            d = re.match("(?P<precision>[sd])(?P<domain>[cr])(?P<direction>[fb])(?P<placement>[io])(?P<dimensions>[\dx]*)",arguments).groupdict()
            l_arguments = (d_rosetta_fft[d[name]] for name in ('precision','domain','direction','placement'))
            yield "fft", [ *l_arguments, d['dimensions'],  time] 
