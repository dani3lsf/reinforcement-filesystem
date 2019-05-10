#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import signal
import os
import subprocess
import yaml
import time
import threading
import pandas as pd
import multiprocessing as mp

from src.fuse.fuse_impl import ProviderFS
from src.fuse.fuse_impl2 import ProviderFS_No_Migration
from src.providers.provider import Provider
from src.providers.dropbox import Dropbox
from src.providers.local import Local
from src.providers.google_drive import GoogleDrive
from datetime import datetime, timedelta
from src.metadata.metadata import Metadata
from src.exceptions.exceptions import ProgramKilled, InsufficientSpaceException
from src.migration.migration import Migration
from fuse import FUSE

WAIT_TIME_SECONDS = 10
CURRENT_RUN = 0
CONFIG = None
PROVIDERS = None
META = None
C_RUNTIME = None
D_RUNTIME = None
NUMBER_FILES = None
FILE_SIZE = None
MOUNTPOINT = None


def calc_latency_with_migration(latency, migration_time):
    nr_reads = int((C_RUNTIME * 60)/latency)
    ret = ((C_RUNTIME * 60) + (migration_time))/nr_reads
    return ret


def calc_throughput_with_migration(throughput, migration_time):
    nr_reads = int((C_RUNTIME * 60) * throughput)
    ret = nr_reads/((C_RUNTIME * 60) + (migration_time))
    return ret


def signal_handler(signum, frame):
    raise ProgramKilled


def target_fun():
    global CONFIG, CURRENT_RUN, PROVIDERS, META
    global FILE_SIZE, NUMBER_FILES, MOUNTPOINT

    # time.sleep(10)

    if not os.path.isdir('results'):
        os.mkdir('results')
        os.mkdir('results/dstat')

    output_bench = "results/bench.csv"

    script = 'python3 benchmark.py -b -m %s -n %d -s %s > /dev/null' %\
             (MOUNTPOINT, NUMBER_FILES, FILE_SIZE)

    proc = subprocess.Popen(script, shell=True)

    outs, errs = proc.communicate()
    proc.kill()

    # Runs

    for conf in CONFIG["runs"]:

        filename = "results/dstat/dstat_run%s.csv" % CURRENT_RUN

        if not os.path.exists(filename):
            os.mknod(filename)

        command = "dstat -c -d -m -t --output %s 60" % filename

        # Initialize dstat
        # print(command)

        dstat_proc = subprocess.Popen(command, shell=True,
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)

        # COLLECTION PHASE
        print("Starting collection phase...")

        script = 'python3 benchmark.py -d %s -r %d -i %d -o %s -m %s > /dev/'\
                 'null' % (conf, C_RUNTIME, CURRENT_RUN, output_bench,
                           MOUNTPOINT)

        proc = subprocess.Popen(script, shell=True)

        outs, errs = proc.communicate()

        # DECISION PHASE
        print("Starting decision phase...")

        manager = mp.Manager()
        cloud_migration_data = manager.list()

        proc_decision = mp.Process(target=META.migration_data,
                                   args=(cloud_migration_data,))
        proc_decision.start()
        time.sleep(60*D_RUNTIME)
        proc_decision.terminate()

        mig_duration = mp.Value('i')

        # MIGRATION PHASE
        print("Starting migration phase...")

        migration = Migration(metadata=META,
                              providers=PROVIDERS,
                              migration_data=cloud_migration_data,
                              duration=mig_duration)
        migration.start()
        migration.join()

        migration_time = mig_duration.value

        # Update bench output
        df = pd.read_csv(output_bench, dtype='float64')
        df.set_index('Run')
        df.at[CURRENT_RUN, 'Latency w/ Migration'] = \
            calc_latency_with_migration(df.at[CURRENT_RUN, 'Latency'],
                                        migration_time)
        df.at[CURRENT_RUN, 'Throughtput w/ Migration'] = \
            calc_throughput_with_migration(df.at[CURRENT_RUN, 'Throughtput'],
                                           migration_time)
        df.to_csv(output_bench, index=False, header=True)

        # Terminate dstat when run is over
        dstat_proc.kill()

        # Reset metadata when run is over
        META.reset()

        # Increment run
        CURRENT_RUN += 1


def main():

    global CURRENT_RUN, CONFIG, META, PROVIDERS, C_RUNTIME, D_RUNTIME
    global FILE_SIZE, NUMBER_FILES, MOUNTPOINT

    with open("config/runs.yml") as stream:
        CONFIG = yaml.safe_load(stream)

    C_RUNTIME = int(CONFIG["runtimes"]["collection"])
    D_RUNTIME = int(CONFIG["runtimes"]["decision"])
    FILE_SIZE = int(CONFIG["files"]["size"])
    NUMBER_FILES = int(CONFIG["files"]["number"])

    # Providers
    PROVIDERS = {}

    # Local providers
    local = Local('LOCAL1')
    provider = Provider(local)
    PROVIDERS['local1'] = provider

    local = Local('LOCAL2')
    provider = Provider(local)
    PROVIDERS['local2'] = provider

    # Initializing Metadata
    META = Metadata()

    # Global Provider
    fuse_impl = ProviderFS(PROVIDERS, META)

    t = threading.Timer(10, target_fun)

    t.start()

    FUSE(fuse_impl, MOUNTPOINT, foreground=True)

    # Starting fuse
    # fuse_proc = mp.Process(target=FUSE, args=(fuse_impl, mountpoint),
    #                       kwargs={'foreground': True})
    # fuse_proc.start()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('mountpoint', help='Directory on which'
                        ' the filesystem will be mounted')
    args = vars(parser.parse_args())

    MOUNTPOINT = args.get('mountpoint')

    main()
