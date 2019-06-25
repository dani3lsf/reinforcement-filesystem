#!/usr/bin/python3
# ------------------------------------------------------------------------------

# szr4:
# python3 ../../analiser.py results_heuristic_szr4/heuristica\ 1.csv results_heuristic2_szr4/heuristica\ 2.csv results_rl_szr4/rl.csv -o szr4.pdf -d -1 sequencial 0 zipfian 1 random 2 sequencial 3 zipfian 4 random 5 sequencial 6 zipfian 7 random 8 sequencial 9 zipfian 10 random 11

#12distA
# python3 ../../analiser.py results_heuristic_12distA/heuristica\ 1.csv results_heuristic2_12distA/heuristica\ 2.csv results_rl_12distA/rl.csv -o distA12 -d

import argparse
import csv
import regex as re
import matplotlib.pyplot as plt
import matplotlib.backends.backend_pdf
from adjustText import adjust_text

OUTPUT_FILE = None
DIVISIONS = None
DIVISIONS_AND_CAPTION = None

def proc_file(f):
    csv_reader = csv.DictReader(f)
    res = {}
    its = []
    lat = []
    thrp = []
    lat_m = []
    thrp_m = []
    nmf = []
    line_count = 0
    for row in csv_reader:
        its.append(float(row["Iteration"]))
        lat.append(float(row["Latency"]))
        thrp.append(float(row["Throughtput"]))
        lat_m.append(float(row["Latency w/ Migration"]))
        thrp_m.append(float(row["Throughtput w/ Migration"]))
        nmf.append(float(row["Migration Number"]))
        line_count += 1

    res["its"] = its
    res["lat"] = lat
    res["thrp"] = thrp
    res["lat_m"] = lat_m
    res["thrp_m"] = thrp_m
    res["nmf"] = nmf

    return res


def proc_name(path, filenames):
    match = re.search(r'(?<=(/?))[\w ]+(?=.csv)', path)
    filename = filename_original = match[0]
    if filename in filenames:
        suffix = 2
        while(filename in filenames):
            filename = filename_original + "_" + str(suffix)
            suffix += 1

    return filename


def draw_graph(files_data):
    pdf = matplotlib.backends.backend_pdf.PdfPages(OUTPUT_FILE)
    fig = plt.figure()
    yy = [10.75, 10.30]
    yy_index = 0
    for div in DIVISIONS:
        plt.axvline(x=div,ls=':')
    for div, caption, x in DIVISIONS_AND_CAPTIONS:
        plt.axvline(x=div,ls=':')
        plt.text(x, yy[yy_index % 2], caption, ha='center', va='center', color='black',
                    bbox=dict(boxstyle='round,pad=0.1', fc='yellow', alpha=0.7))
        yy_index += 1
        
    plt.xlabel('Iterações')
    plt.ylabel('Latência (s/read)')
    plt.title("Latência por iteração s/ migração")
    handles = []
    colors = ['blue', 'orange', 'green']

    i = 0
    texts = []
    for file_name, file_data in files_data.items():
        color_offset_idx = i % 3
        plot, = plt.plot(file_data["its"], file_data["lat"], label=file_name, color=colors[color_offset_idx])
        for it in range(0,len(file_data["its"])):
            texts.append(plt.text(file_data["its"][it],
                                  file_data["lat"][it],
                                  '{}'.format(int(file_data["nmf"][it])),
                                    ha='center', va='center',
                                    color='black',
                                    bbox=dict(boxstyle='round,pad=0.1', fc=colors[color_offset_idx], alpha=0.3)))
        handles.append(plot)
        i += 1
    adjust_text(texts)

    plt.legend(handles=handles, loc='lower right')
    plt.ylim(bottom=0)
    plt.ylim(top=11)
    pdf.savefig(fig)

    fig = plt.figure()
    yy = [10.75, 10.30]
    yy_index = 0
    for div in DIVISIONS:
        plt.axvline(x=div,ls=':')
    for div, caption, x in DIVISIONS_AND_CAPTIONS:
        plt.axvline(x=div,ls=':')
        plt.text(x, yy[yy_index % 2], caption, ha='center', va='center', color='black',
                    bbox=dict(boxstyle='round,pad=0.1', fc='yellow', alpha=0.7))
        yy_index += 1
    plt.xlabel('Iterações')
    plt.ylabel('Latência (s/read)')
    plt.title("Latência por iteração c/ migração")
    handles = []
    texts = []
    for file_name, file_data in files_data.items():
        color_offset_idx = i % 3
        plot, = plt.plot(file_data["its"], file_data["lat_m"], label=file_name, color=colors[color_offset_idx])
        for it in range(0,len(file_data["its"])):
            texts.append(plt.text(file_data["its"][it],
                                  file_data["lat_m"][it],
                                  '{}'.format(int(file_data["nmf"][it])),
                                    ha='center', va='center',
                                    color='black',
                                    bbox=dict(boxstyle='round,pad=0.1', fc=colors[color_offset_idx], alpha=0.3)))
        handles.append(plot)
        i += 1
    adjust_text(texts)

    plt.legend(handles=handles, loc='lower right')
    plt.ylim(bottom=0)
    plt.ylim(top=11)
    pdf.savefig(fig)

    fig = plt.figure()
    yy = [0.57, 0.545]
    yy_index = 0
    for div in DIVISIONS:
        plt.axvline(x=div,ls=':')
    for div, caption, x in DIVISIONS_AND_CAPTIONS:
        plt.axvline(x=div,ls=':')
        plt.text(x, yy[yy_index % 2], caption, ha='center', va='center', color='black',
                    bbox=dict(boxstyle='round,pad=0.1', fc='yellow', alpha=0.7))
        yy_index += 1
    plt.xlabel('Iterações')
    plt.ylabel('Débito (reads/s)')
    plt.title("Débito por iteração s/ migração")
    handles = []
    texts = []
    for file_name, file_data in files_data.items():
        color_offset_idx = i % 3
        plot, = plt.plot(file_data["its"], file_data["thrp"], label=file_name, color=colors[color_offset_idx])
        for it in range(0,len(file_data["its"])):
            texts.append(plt.text(file_data["its"][it],
                                  file_data["thrp"][it],
                                  '{}'.format(int(file_data["nmf"][it])),
                                    ha='center', va='center',
                                    color='black',
                                    bbox=dict(boxstyle='round,pad=0.1', fc=colors[color_offset_idx], alpha=0.3)))
        handles.append(plot)
        i += 1
    adjust_text(texts)

    plt.legend(handles=handles, loc='lower right')
    plt.ylim(bottom=0)
    plt.ylim(top=0.6)
    pdf.savefig(fig)

    fig = plt.figure()
    yy = [0.57, 0.545]
    yy_index = 0
    for div in DIVISIONS:
        plt.axvline(x=div,ls=':')
    for div, caption, x in DIVISIONS_AND_CAPTIONS:
        plt.axvline(x=div,ls=':')
        plt.text(x, yy[yy_index % 2], caption, ha='center', va='center', color='black',
                    bbox=dict(boxstyle='round,pad=0.1', fc='yellow', alpha=0.7))
        yy_index += 1

    plt.xlabel('Iterações')
    plt.ylabel('Débito (reads/s)')
    plt.title("Débito por iteração c/ migração")
    handles = []
    texts = []
    for file_name, file_data in files_data.items():
        color_offset_idx = i % 3
        plot, = plt.plot(file_data["its"], file_data["thrp_m"], label=file_name, color=colors[color_offset_idx])
        for it in range(0,len(file_data["its"])):
            texts.append(plt.text(file_data["its"][it],
                                  file_data["thrp_m"][it],
                                  '{}'.format(int(file_data["nmf"][it])),
                                    ha='center', va='center',
                                    color='black',
                                    bbox=dict(boxstyle='round,pad=0.1', fc=colors[color_offset_idx], alpha=0.3)))
        handles.append(plot)
        i += 1
    adjust_text(texts)

    plt.legend(handles=handles, loc='lower right')
    plt.ylim(bottom=0)
    plt.ylim(top=0.6)
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
    parser.add_argument('-o', '--output_file', help="Output File",
                        type=str, default="output.pdf")
    parser.add_argument('-d','--divisions', nargs='+', type=str, default=[])
    args = vars(parser.parse_args())
    OUTPUT_FILE = args.get('output_file')

    DIVISIONS = []
    DIVISIONS_AND_CAPTIONS = []
    item_idx = 0
    divs = args.get('divisions')
    if(divs != None):
        while(item_idx < len(divs)):
            if (item_idx + 1 != len(divs)) and not (divs[item_idx + 1]).isnumeric():
                DIVISIONS_AND_CAPTIONS.append((int(divs[item_idx]), divs[item_idx + 1],
                (int(divs[item_idx]) + int(divs[item_idx + 2])) / 2 ))
                item_idx += 2
            else:
                DIVISIONS.append(int(divs[item_idx]))
                item_idx += 1
    
    main(args.get('files'))
