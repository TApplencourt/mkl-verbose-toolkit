from typing import Dict, Tuple, TextIO, Match, Iterator
import re

d_rosetta_fft = {'s': "Single",
                'd': "Double",
                'c': "Complex",
                'r': "Real",
                'f': "Forward",
                'b': "Backward",
                'i': "in-place",
                'o': "out-of-place"}

def parse_fft(d_match: Dict, t):
    i = (d_rosetta_fft[d_match[name]] for name in ('precision','domain','direction','placement'))
    return tuple([*i, d_match['dimensions'], t])

def parse_lapack(d_match: Dict, t):

    def parse_lapack_argv(l_args):
        return ( (i,arg) for i, arg in enumerate(l_args.split(',')) if not arg.startswith('0x') )

    return tuple([d_match['name'], *parse_lapack_argv(d_match['args']), t ])


def parse_iter(f: TextIO) -> Iterator[ Tuple[Match,Match] ]:
   #regex = r"^MKL_VERBOSE (?!Intel)(?P<name>\w+?)\((?P<args>.*)\) (?P<time>\S+?)(?P<exp>[a-z]+)"
   # Some specific version of MKL doesn't have the clossing parentheses in the list of arguments, this explan the \)?  in <args>
   regex = "^MKL_VERBOSE (?!Intel)(?P<name>\w+?)\((?P<args>.*?)\)? (?P<time>\S+?)(?P<exp>[a-z]+)"
   re_mkl = re.compile(regex, re.MULTILINE)

   regex = r"(?P<precision>[sd])(?P<domain>[cr])(?P<direction>[fb])(?P<placement>[io])(?P<dimensions>[\dx]*)"
   re_fft = re.compile(regex)

   d_rosetta_time = {'ns':1.e-9, 'us':1.e-6, 'ms':1.e-3, 's': 1}
   
   for line in f:
        for match in re_mkl.finditer(line):
    
            d_match = match.groupdict()
            t = float(d_match['time']) * d_rosetta_time[d_match['exp']]
            #if t < 1E-6:
            #    continue

            if d_match['name'] != 'FFT':
                yield "lapack", parse_lapack(d_match,t)
            else:
                d_match.update(re_fft.search(d_match['args']).groupdict())
                yield "fft", parse_fft(d_match,t)



