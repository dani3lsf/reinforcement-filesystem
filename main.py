#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import signal
import os
import subprocess
import yaml
import multiprocessing as mp
import time
import threading

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


def signal_handler(signum, frame):
    raise ProgramKilled


def target_fun():
    global CONFIG, CURRENT_RUN, PROVIDERS, META

    # time.sleep(10)

    if not os.path.isdir('results/dstat'):
        os.mkdir('results')
        os.mkdir('results/dstat')

    script = './benchmark.py -b > /dev/null'

    proc = subprocess.Popen(script, shell=True)

    outs, errs = proc.communicate()
    proc.kill()

    # Runs

    for conf in CONFIG["runs"]:

        filename = "results/dstat/dstat_RUN%s.csv" % CURRENT_RUN

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

        script = 'python benchmark.py -d %s > /dev/null' % conf

        proc = subprocess.Popen(script, shell=True)

        try:
            outs, errs = proc.communicate(timeout=60*C_RUNTIME)
        except subprocess.TimeoutExpired:
            proc.kill()

        # DECISION PHASE
        print("Starting decision phase...")

        manager = mp.Manager()
        cloud_migration_data = manager.list()

        proc_decision = mp.Process(target=META.migration_data,
                                   args=(cloud_migration_data,))
        proc_decision.start()
        time.sleep(60*D_RUNTIME)
        proc_decision.terminate()

        # MIGRATION PHASE
        print("Starting migration phase...")

        migration = Migration(metadata=META,
                              providers=PROVIDERS,
                              migration_data=cloud_migration_data)
        migration.start()
        migration.join()

        # Terminate dstat when run is over
        dstat_proc.kill()

        # Reset metadata when run is over
        META.reset()

        # Increment run
        CURRENT_RUN += 1


def main(mountpoint):

    global CURRENT_RUN, CONFIG, META, PROVIDERS, C_RUNTIME, D_RUNTIME

    with open("config/runs.yml") as stream:
        CONFIG = yaml.safe_load(stream)

    C_RUNTIME = int(CONFIG["runtimes"]["collection"])
    D_RUNTIME = int(CONFIG["runtimes"]["decision"])

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

    # print("ola")

    FUSE(fuse_impl, mountpoint, foreground=True)

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

    main(args.get('mountpoint'))
