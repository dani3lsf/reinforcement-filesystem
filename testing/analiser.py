#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse
import csv
import regex as re
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf

def proc_file(f):
    csv_reader = csv.DictReader(f)
    res = {}
    its = []
    lat = []
    thrp = []
    lat_m = []
    thrp_m = []
    line_count = 0
    for row in csv_reader:
        if line_count == 0:
            line_count += 1
            continue

        its.append(float(row["Iteration"]))
        lat.append(float(row["Latency"]))
        thrp.append(float(row["Throughtput"]))
        lat_m.append(float(row["Latency w/ Migration"]))
        thrp_m.append(float(row["Throughtput w/ Migration"]))
        line_count += 1
    
    res["its"] = its
    res["lat"] = lat
    res["thrp"] = thrp
    res["lat_m"] = lat_m
    res["thrp_m"] = thrp_m

    return res

def proc_name(path, filenames):
    match = re.search(r'(?<=(/?))\w+(?=.csv)', path)
    filename = filename_original = match[0]
    if filename in filenames:
        suffix = 2
        while(filename in filenames):
            filename = filename_original + "_" + str(suffix)
            suffix += 1

    return filename   

def draw_graph(files_data):
    pdf = matplotlib.backends.backend_pdf.PdfPages("output.pdf")
    
    fig = plt.figure()
    plt.xlabel('iterações')
    plt.ylabel('latência (s/read)')
    plt.title("Latência por iteração s/migração")
    handles = []
    for file_name, file_data in files_data.items():
        plot, = plt.plot(file_data["its"], file_data["lat"], label=file_name)
        handles.append(plot)
    plt.legend(handles=handles, loc='lower right')
    pdf.savefig(fig)
    
    fig = plt.figure()
    plt.xlabel('iterações')
    plt.ylabel('latência (s/read)')
    plt.title("Latência por iteração c/migração")
    handles = []
    for file_name, file_data in files_data.items():
        plot, = plt.plot(file_data["its"], file_data["lat_m"], label=file_name)
        handles.append(plot)
    plt.legend(handles=handles, loc='lower right')
    pdf.savefig(fig)
    
    fig = plt.figure()
    plt.xlabel('iterações')
    plt.ylabel('débito (read/s)')
    plt.title("Débito por iteração s/migração")
    handles = []
    for file_name, file_data in files_data.items():
        plot, = plt.plot(file_data["its"], file_data["thrp"], label=file_name)
        handles.append(plot)
    plt.legend(handles=handles, loc='lower right')
    pdf.savefig(fig)

    fig = plt.figure()
    plt.xlabel('iterações')
    plt.ylabel('débito (read/s)')
    plt.title("Débito por iteração c/migração")
    handles = []
    for file_name, file_data in files_data.items():
        plot, = plt.plot(file_data["its"], file_data["thrp_m"], label=file_name)
        handles.append(plot)
    plt.legend(handles=handles, loc='lower right')
    pdf.savefig(fig)

    pdf.close()
    

    

def main(files):

    files_data = {}
    for f in files:
        file_name = proc_name(f.name, files_data.keys())
        file_data = proc_file(f)
        files_data[file_name] = file_data
    draw_graph(files_data)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('files', type=argparse.FileType('r'), nargs='+', help="csv files to process")
    args = parser.parse_args()
    main(args.files)