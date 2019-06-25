import threading
import numpy as np
import re

from datetime import datetime, timedelta
from src.metadata.cloud_managment import CloudManagement
from src.exceptions.exceptions import InsufficientSpaceException
from multiprocessing import Process, Manager, Queue
from collections import Counter

CUT_TIME_SECONDS = 60
RECORDED_READS = 250


class Metadata():

    def __init__(self):
        self.manager = Manager()
        self.files = self.manager.dict()
        self.last_reads = Queue(RECORDED_READS)
        self.clouds = CloudManagement()
        self.lock = threading.RLock()

    # def reset(self):
    #    for file in self.files.keys():
    #        self.files[file]['accesses'] = 0

    # def __init__(self, *args, **kwargs):
    #     self.files = dict(*args, **kwargs)
    #     self.clouds = CloudManagement()
    #     self.lock = threading.RLock()

    def __getitem__(self, key):
        return self.files.get(key, None)

    def __len__(self):
        return len(self.files)

    def __repr__(self):
        return "metadata = " + self.files.__repr__()

    def acquire_lock(self):
        self.lock.acquire()

    def release_lock(self):
        self.lock.release()

    def reset_files(self):
        new_fileset = self.calculate_accesses()
        for filename, file in self.files.items():
            if filename in new_fileset:
                self.files[filename]['accesses'] = new_fileset[filename]

    def add_read(self, file):
        if(file in self.files):
            self.files[file]['accesses'] += 1

            if(self.last_reads.full()):
                self.last_reads.get()
            self.last_reads.put(file)

    def add_file(self, file_name, file_length):
        cloud_id, cloud_name = self.choose_cloud_for_insertion(file_length)

        self.files[file_name] = self.manager.dict({
            'cloud': cloud_name,
            'length': file_length,
            'accesses': 0})
        self.clouds.inc_dec_used_space(cloud_id, file_length)

    def del_file(self, file_name):
        file = self.files.pop(file_name)
        cloud_id = self.clouds.get_cloud_id_by_name(file['cloud'])
        self.clouds.inc_dec_used_space(cloud_id, -file['length'])

    def rename_file(self, old, new):
        file = self.files.pop(old)
        self.files[new] = file

    def add_file_to_cloud(self, file_name, file_length, cloud_name):
        if file_name not in self.files:
            self.files[file_name] = self.manager.dict({
                'cloud': cloud_name,
                'length': file_length,
                'accesses': 0})
            cloud_id = self.clouds.get_cloud_id_by_name(cloud_name)
            self.clouds.inc_dec_used_space(cloud_id, file_length)

    def get_last_reads(self, file):
        if(file in self.files):
            return file['accesses']
        else:
            return None

    def get_all_file_names(self):
        return list(self.files.keys())

    def get_file_cloud_name(self, file_name):
        if file_name in self.files:
            return self.files[file_name]['cloud']
        else:
            return None

    def get_files_cloud(self):
        res = {}
        for file_name, file_info in self.files.items():
            cloud_name = file_info['cloud']
            cloud_id = self.clouds.get_cloud_id_by_name(cloud_name)
            res[file_name] = cloud_id

        return res

    def calculate_accesses(self):
        self.acesses = {}
        access_list = []

        while not self.last_reads.empty():
            access_list.append(self.last_reads.get())

        for item in access_list:
            self.last_reads.put(item)

        return dict(Counter(access_list))

    def get_files_accesses(self):
        res = {}
        for file_name, file_info in self.files.items():
            res[file_name] = file_info['accesses']

        return res

    def test_if_fits(self, length, cloud):
        cloud_id = self.clouds.get_cloud_id_by_name(cloud)
        return self.clouds.test_if_fits(length, cloud_id)

    def inc_dec_file_length(self, file_name, diff):
        file = self.files[file_name]
        cloud_id = self.clouds.get_cloud_id_by_name(file['cloud'])
        self.clouds.inc_dec_used_space(cloud_id, diff)
        file['length'] += diff

    def choose_cloud_for_insertion(self, file_length):
        return self.clouds.choose_cloud_for_insertion(file_length)

    def cloud_outliers(self, cloud_name, limit):
        
        new_limit = limit

        cloud_files_info = [(file_name, file['accesses'])
                            for file_name, file in self.files.items()
                            if file['cloud'] == cloud_name]
        sorted(cloud_files_info, key=lambda x: x[1])

        upper_outliers = []
        lower_outliers = [file_name for (file_name, file_accesses) in cloud_files_info if file_accesses <= limit]
        del cloud_files_info[0:len(lower_outliers)]
        
        accesses = [x[1] for x in cloud_files_info]

        if accesses != []:
            q1, q3 = np.percentile(accesses, [25, 75])
            avg = np.mean(accesses)
            iqr = q3 - q1
            lower_bound = q1 - (1.5 * iqr) 
            upper_bound = q3 + (1.5 * iqr) 

            new_lower_outliers = [x[0] for x in cloud_files_info
                                                if x[1] < lower_bound]
            lower_outliers += new_lower_outliers
            upper_outliers = [x[0] for x in cloud_files_info
                              if x[1] > upper_bound]

            #remove outliers from clouds_info to calcule normal files
            del cloud_files_info[0:len(new_lower_outliers)]
            cloud_files_info = cloud_files_info[:(len(cloud_files_info) - len(upper_outliers))]

            if len(cloud_files_info) > 0:
                new_limit = max([x[1] for x in cloud_files_info])
            else:
                new_limit = limit
            
        return (lower_outliers, upper_outliers, new_limit)


    def migration_data(self):
        self.reset_files()
        clouds_migration_data = []

        limit = -1
        for cloud_id in range(0, len(self.clouds)):
            (lower_outliers, upper_outliers, new_limit) = self.cloud_outliers(
                self.clouds[cloud_id]["name"], limit)
            limit = new_limit
            if cloud_id != 0 and lower_outliers != []:
                for file_name in lower_outliers:
                    clouds_migration_data.append((file_name, cloud_id,
                                                  cloud_id - 1,
                                                  self.files[file_name]['length']))
            if cloud_id < len(self.clouds) - 1 and upper_outliers != []:
                for file_name in upper_outliers:
                    clouds_migration_data.append((file_name, cloud_id,
                                                  cloud_id + 1,
                                                  self.files[file_name]['length']))

        return clouds_migration_data

    def migration_data_rl(self, positions):
        clouds_migration_data = []
        self.reset_files()
       
        for file_name, file_info in self.files.items():
            id = int(re.findall('\d+', file_name)[0])
            pos = positions[id]
            if pos == 0 and file_info['cloud'] == 'local2':
                clouds_migration_data.append((file_name, 1, 0,
                                             self.files[file_name]['length']))
            elif pos == 1 and file_info['cloud'] == 'local1':
                clouds_migration_data.append((file_name, 0, 1,
                                             self.files[file_name]['length']))
        return clouds_migration_data

    def migrate(self, name, frm, to):
        file = self.files[name]
        to_cloud = self.clouds[to]
        # from_cloud = self.clouds[frm]
        if(to_cloud['used'] + file['length'] > to_cloud['total']):
            raise InsufficientSpaceException
        else:
            self.clouds.inc_dec_used_space(to, file['length'])
            self.clouds.inc_dec_used_space(frm, -file['length'])
            file['cloud'] = to_cloud['name']
