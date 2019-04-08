#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import random
import time
import os
import shutil
import numpy as np


parser = argparse.ArgumentParser()
parser.add_argument('-f', '--filee', type=int, default=1)
args = vars(parser.parse_args())

while True:
    if os.path.exists('mops/mp1/fich' + str(args.get('filee')) + '.txt'):
        with open('mops/mp1/fich' + str(args.get('filee')) + '.txt') as f:
            f.read()
            print("Reading " + str(args.get('filee')))
    else:
        with open('mops/mp2/fich' + str(args.get('filee')) + '.txt') as f:
            f.read()
            print("Reading " + str(args.get('filee')))
