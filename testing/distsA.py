#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import signal
import os
import random
import subprocess
import yaml
import time
import threading
import json
import shutil
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import multiprocessing as mp
import re

from src.fuse.fuse_impl import ProviderFS
from src.providers.provider import Provider
from src.providers.local import Local
from src.metadata.metadata import Metadata
from src.exceptions.exceptions import ProgramKilled, InsufficientSpaceException
from src.migration.migration import Migration
from fuse import FUSE
from src.reinforcement.reinforcement import *    
    
CONFIG = None

with open("config/runs.yml") as stream:
        CONFIG = yaml.safe_load(stream)

random.seed(12345678)   
#previous_zp = False
dists = ["sequential","random","zipfian"]
for conf in CONFIG["runs"]:
    (dist, seed, ch) = re.split(r':', conf)
    if seed:
        seed = int(seed)
    else:
        seed = -1

    if dist == "zipfian" and ch:
        ch = True
    else:
        ch = False

    if dist == "any":
        dist = random.choice(dists)
        print(dist)