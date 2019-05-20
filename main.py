#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import signal
import os
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

# WAIT_TIME_SECONDS = 10
CURR_ITERATION = 0
CONFIG = None
PROVIDERS = None
META = None
C_RUNTIME = None
D_RUNTIME = None
OUTPUT_PATH = None
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
    global CONFIG, CURR_ITERATION, PROVIDERS, META
    global FILE_SIZE, NUMBER_FILES, MOUNTPOINT, OUTPUT_PATH

    # time.sleep(10)

    # Remove results folder and files if it exists
    if os.path.isdir(OUTPUT_PATH):
        shutil.rmtree(OUTPUT_PATH)

    # Create results folders and files
    os.mkdir(OUTPUT_PATH)
    os.mkdir(OUTPUT_PATH + '/dstat')

    output_bench = "%s/bench.csv" % OUTPUT_PATH

    script = 'python3 benchmark.py -b -m %s -n %d -s %s > /dev/null' %\
             (MOUNTPOINT, NUMBER_FILES, FILE_SIZE)

    proc = subprocess.Popen(script, shell=True)

    outs, errs = proc.communicate()
    proc.kill()

    # Runs
    writer = initiate_output()

    for conf in CONFIG["runs"]:

        filename = "%s/dstat/dstat_it%s.csv" % (OUTPUT_PATH, CURR_ITERATION)

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
                 'null' % (conf, C_RUNTIME, CURR_ITERATION, output_bench,
                           MOUNTPOINT)

        proc = subprocess.Popen(script, shell=True)

        outs, errs = proc.communicate()

        include_it_info_to_output(writer)

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
        df = pd.read_csv(output_bench, dtype='float64', index_col=0)
        df.at[float(CURR_ITERATION), 'Latency w/ Migration'] = \
            calc_latency_with_migration(df.at[float(CURR_ITERATION), 'Latency'],
                                        migration_time)
        df.at[float(CURR_ITERATION), 'Throughtput w/ Migration'] = \
            calc_throughput_with_migration(df.at[float(CURR_ITERATION), 'Throughtput'],
                                           migration_time)
        df.to_csv(output_bench, index=True, header=True)

        # Terminate dstat when iteration is over
        dstat_proc.kill()

        # Reset metadata when iteration is over
        META.reset()

        # Increment iteration
        CURR_ITERATION += 1

    finish_output(writer)


def initiate_output():
    output_file = OUTPUT_PATH + "/heatmap.json"
    writer = open(output_file, "w+")
    writer.write("{\n")
    return writer


def include_it_info_to_output(writer):

    files_cloud = META.get_files_cloud()
    hits = META.get_files_accesses()

    string_clouds = "\"files_cloud\": " + json.dumps(files_cloud)
    string_hits = "\"hits\": " + json.dumps(hits)

    writer.write(f"\"{CURR_ITERATION}\": " + "{\n" + string_clouds + ",\n")

    if (CURR_ITERATION == len(CONFIG["runs"]) - 1):
        writer.write(string_hits + "\n}\n")
    else:
        writer.write(string_hits + "\n},\n")


def finish_output(writer):
    output_file = OUTPUT_PATH + "/heatmap.json"
    output_graph = OUTPUT_PATH + "/heatmap.pdf"
    writer.write("}\n")
    writer.close()

    with open(output_file, "r") as reader:
        json_str = reader.read()

    run_info = json.loads(json_str)

    its_info = []
    its = list(range(len(CONFIG["runs"])))
    file_names = META.get_all_file_names()
    file_names.sort()

    for file_name in file_names:
        file_hits = [run_info[str(it)]['hits'][file_name] for it in its]
        its_info.append(file_hits)

    accesses = np.array(its_info)

    fig, ax = plt.subplots()
    im = ax.imshow(accesses, cmap='Blues')

    # We want to show all ticks...
    ax.set_yticks(np.arange(len(file_names)))
    ax.set_xticks(np.arange(len(its)))
    # ... and label them with the respective list entries
    ax.set_yticklabels(file_names)
    ax.set_xticklabels(its)

    # Loop over data dimensions and create text annotations.
    for i in range(len(its)):
        for j in range(len(file_names)):
            text = ax.text(i, j, run_info[str(i)]['files_cloud']
                           [file_names[j]], ha="center", va="center",
                           color="b")

    ax.set_title("Iteration File-Reads Heatmap")
    fig.tight_layout()
    plt.savefig(output_graph)


def main():

    global CURR_ITERATION, CONFIG, META, PROVIDERS, C_RUNTIME, D_RUNTIME
    global FILE_SIZE, NUMBER_FILES, MOUNTPOINT, OUTPUT_PATH

    with open("config/runs.yml") as stream:
        CONFIG = yaml.safe_load(stream)

    C_RUNTIME = int(CONFIG["runtimes"]["collection"])
    D_RUNTIME = int(CONFIG["runtimes"]["decision"])
    OUTPUT_PATH = CONFIG["output_path"]
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
