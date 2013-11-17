#!/usr/bin/env python3

import sys
import csv
import json

if __name__ == '__main__':
    infile = open(sys.argv[1])
    outcsv = csv.writer(open(sys.argv[2], 'w'))
    
    cols = None    

    for line in infile:
        line = line.strip()
        if len(line) == 0:
            break

        d = json.loads(line)
        
        if cols is None:
            cols = list(d.keys())
            print(cols)
            outcsv.writerow(cols)

        outcsv.writerow([d[k] for k in cols])

