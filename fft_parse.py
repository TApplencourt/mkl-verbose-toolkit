#!/usr/bin/env python
import re
import sys
import mmap

regex =  br"^MKL_VERBOSE FFT.+?\|(.*?)\|"

from collections import Counter
with open(sys.argv[1], 'r') as f:
     data = mmap.mmap(f.fileno(), 0,flags=mmap.MAP_PRIVATE, prot=mmap.PROT_READ)
     c = Counter( match.groups()[0].decode('utf-8').strip() for match in re.finditer(regex, data, re.MULTILINE))

for i,j in c.items():
    print (i,"\t",j)
