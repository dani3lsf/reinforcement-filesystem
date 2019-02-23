#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import random
import os
import numpy as np

parser = argparse.ArgumentParser()
parser.add_argument('-n', '--number_of_files', type=int, help='Number of files to be generated and read afterwards',
                    default=20)
parser.add_argument('-s', '--size', type=int, help='Size for each file (MB)', default=5)
parser.add_argument('-d', '--distribution', choices=['sequential', 'random', 'zipfian'],
                    help='Distribution used to read files', default='sequential')
args = vars(parser.parse_args())
file_list = []

# Create directory for dummy files
os.mkdir('files')

# Write files with random size
it = 0

while it < args.get('number_of_files'):
    # size = random.uniform(1.0, args.get('size'))
    filename = 'files/dummy' + str(it)
    f = open(filename, 'wb')
    f.seek(int(args.get('size')*1e6) - 1)
    f.write(b'\0')
    file_list.append(filename)
    it += 1

# Read files with distribution
if args.get('distribution') == 'sequential':
    while True:
        for file in file_list:
            with open(file, 'r') as f:
                print("Reading file... " + file)
                f.read()
elif args.get('distribution') == 'random':
    while True:
        next_file = random.randint(0, len(file_list) - 1)
        with open(next_file, 'r') as f:
            print("Reading file... " + next_file)
            f.read()
else:  # args.get('distribution') == 'zipfian'
    a = 1.7  # TODO: não sei se manter este valor
    wgs = np.random.zipf(a, size=len(file_list))
    print(wgs)
    while True:
        next_file = random.choices(file_list, weights=wgs)[0]
        with open(next_file, 'r') as f:
            print("Reading file... " + next_file)
            f.read()
