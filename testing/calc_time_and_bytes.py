import argparse
import os
import glob
import pandas as pd

total_time = 0          # Hours
total_written = 0       # GB
total_read = 0          # GB
rest = 0

def get_all_subdirectories_lvl(dir, lvl):
    pattern = dir + lvl * '/*'
    return [d for d in glob.glob(pattern) if os.path.isdir(d)]

all_subdirectories = get_all_subdirectories_lvl('tests', 2)

for directory in all_subdirectories:
    test_time = 0
    test_written = 0
    test_read = 0

    csv_files = [f for f in os.listdir(directory) if f.endswith('.csv')]

    bench = directory + "/" + csv_files[0]

    if os.path.exists(bench):
        df = pd.read_csv(bench, dtype='float64', index_col=0)
        for index, row in df.iterrows():
            # total_time += colection + decision + migration
            test_time += (15 * 60 + 1 * 60 + df.at[index, 'Migration Number'] * 10)
            test_written += (100 * df.at[index, 'Migration Number'])
            test_read += (df.at[index, 'Throughtput']) * (15 * 60) * 100

        # Convert time to hours
        test_time_hours = test_time/60/60
        # Convert total written to GB
        test_written_gb = test_written/1000
        # Convert total read to GB
        test_read_gb = test_read/1000

        print(os.path.basename(os.path.normpath(directory) + "=" * 20))
        print(test_time_hours)
        print(test_written_gb)
        print(test_read_gb)

        total_time += test_time_hours
        total_written += test_written_gb
        total_read += test_read_gb

    else:
        rest+=1

print(79 * "=")
print("TOTAL TIME: " + "{0:.3f}".format(total_time) + " hours")
print("TOTAL WRITTEN GB: " + "{0:.3f}".format(total_written) + " GB")
print("TOTAL READ GB: " + "{0:.3f}".format(total_read) + " GB")
print(rest)
