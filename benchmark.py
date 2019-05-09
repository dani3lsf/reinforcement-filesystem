#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import random
import time
import os
import shutil
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument('-n', '--number_of_files', type=int, help='Number of files to be generated and read afterwards',
                    default=20)
parser.add_argument('-s', '--size', type=int, help='Size for each file (MB)', default=5)
parser.add_argument('-d', '--distribution', choices=['sequential', 'random', 'zipfian'],
                    help='Distribution used to read files', default='zipfian')
parser.add_argument('-r', '--runtime', type=int, help='Runtime in minutes', default=5)
parser.add_argument('-b', help="If files need to be written", action='store_true')
args = vars(parser.parse_args())

file_list = []
folder_name = 'Original'

# If files need to be written
if args.get("b") == True:
    # If directory doesn't exist create it
    if not os.path.isdir(folder_name):
        print("Creating directory %s" % folder_name)
        os.mkdir(folder_name)
    else:  # If directory exists remove its contents
        print("Emptying directory %s" % folder_name)
        for filename in os.listdir(folder_name):
            file_path = os.path.join(folder_name, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)
    
    # Write files with random size
    it = 0

    while it < args.get('number_of_files'):
        # size = random.uniform(1.0, args.get('size'))

        filename = folder_name + '/dummy' + str(it)
        print(filename)
        f = open(filename, 'wb')
        f.seek(int(args.get('size')*1e6) - 1)
        print(args.get('size'))
        f.write(b'\0')

        print("Creating file... %s" % filename)
        file_list.append(filename)
        it += 1
else:
    if not os.path.isdir(folder_name):
        raise Exception("Directory doesn't exist")
    else:
        file_list = [folder_name + '/dummy' + str(it) for it in range(0,args.get('number_of_files')) ]



# Calculates time for end of test
end_time = time.time() + 60 * args.get('runtime')
print(time.time())
print(end_time)

# Initiate variable for number of reads
number_of_reads = 0

# Read files with distribution
if args.get('distribution') == 'sequential':
    print("oi")
    while time.time() < end_time:

        for file in file_list:
            if time.time() < end_time:
                with open(file, 'r') as f:
                    print("Reading file... %s" % file)
                    f.read()
                    number_of_reads += 1
elif args.get('distribution') == 'random':
    while time.time() < end_time:
        next_file = random.randint(0, len(file_list) - 1)
        file = folder_name + '/dummy' + str(next_file)
        with open(file, 'r') as f:
            print("Reading file... %s" % file)
            f.read()
            number_of_reads += 1
else:  # args.get('distribution') == 'zipfian'
    a = 1.7  # TODO: não sei se manter este valor
    wgs = np.random.zipf(a, size=len(file_list))
    while time.time() < end_time:
        next_file = random.choices(file_list, weights=wgs)[0]
        with open(next_file, 'r') as f:
            print("Reading file... %s" % next_file)
            f.read()
            number_of_reads += 1

# Calculations for latency and throughput
# Throughput = Number of files read per second
# Latency = How many seconds does it take to read a file
throughput = number_of_reads/(args.get("runtime") * 60)
latency = (args.get("runtime") * 60) / number_of_reads

print("\n")
print("READS (%s)" % args.get("distribution"))
print("=" * 79)
print("Throughtput: %.4f reads/s" % throughput)
print("Latency: %.4f s/read" % latency)
