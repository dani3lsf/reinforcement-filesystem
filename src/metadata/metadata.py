import threading
import numpy as np
from datetime import datetime, timedelta
from src.metadata.file import File
from src.metadata.cloud_managment import CloudManagement
from src.exceptions.exceptions import InsufficientSpaceException

CUT_TIME_SECONDS = 60

class Metadata():

    def __init__(self, *args, **kwargs):
        self.files = dict(*args, **kwargs)
        self.clouds = CloudManagement()
        self.lock = threading.RLock()

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

    def add_read(self, file, time):
        if(file in self.files):
            self.files[file].accesses.append(time)

    def add_file(self, file_name, file_length):
        cloud_id, cloud_name = self.choose_cloud_for_insertion(file_length)
        self.files[file_name] = File(file_name, cloud_name, file_length)
        self.clouds.inc_dec_used_space(cloud_id, file_length)

    def del_file(self, file_name):
        file = self.files.pop(file_name)
        cloud_id = self.clouds.get_cloud_id_by_name(file.provider)
        self.clouds.inc_dec_used_space(cloud_id, -file.length)

    def rename_file(self, old, new):
        file = self.files.pop(old)
        file.name = new
        self.files[new] = file


    def add_file_to_cloud(self, file_name, file_length, cloud_name):
        if file_name not in self.files:
            self.files[file_name] = File(file_name, cloud_name, file_length)
            cloud_id = self.clouds.get_cloud_id_by_name(cloud_name)
            self.clouds.inc_dec_used_space(cloud_id, file_length)

    def get_last_reads(self, file):
        if(file in self.files):
            self.update_file_reads(file)
            return len(self.files.get(file).accesses)
        else:
            return None

    def get_all_file_names(self):
        return list(self.files.keys())

    def get_file_cloud_name(self, file_name):
        if file_name in self.files:
            return self.files[file_name].provider
        else:
            return None

    def inc_dec_file_length(self, file_name, diff):
        file = self.files[file_name]
        cloud_id = self.clouds.get_cloud_id_by_name(file.provider)
        self.clouds.inc_dec_used_space(cloud_id, diff)
        file.length += diff

    def update_file_reads(self, file):
        if(file in self.files):
            now = datetime.now()
            f = self.files.get(file)
            #isto
            accesses = [ocorr for ocorr in f.accesses if (now - ocorr < timedelta(seconds = CUT_TIME_SECONDS))]
            f.accesses = accesses
            # ou isto (otimizacao para listas muito grandes)
            # i = 0
            # for ocorr in f.accesses:
            #     if now - ocorr >= timedelta(seconds = 60*1):
            #         i+=1
            #     else: break
            # f.accesses = f.accesses[i:]
            
    def update_all(self):
        for file in self.files:
            self.update_file_reads(file)
    
    def choose_cloud_for_insertion(self, file_length):
        return self.clouds.choose_cloud_for_insertion(file_length)

    def cloud_outliers(self, cloud_name):
        cloud_files_info = [(file.name, len(file.accesses)) for file in self.files.values() if file.provider == cloud_name]
        sorted(cloud_files_info, key = lambda x: x[1])
        accesses = [x[1] for x in cloud_files_info]
        lower_outliers = []
        upper_outliers = []
        if accesses != []:
            q1, q3= np.percentile(accesses,[25,75])
            iqr = q3 - q1
            lower_bound = q1 -(1.5 * iqr) 
            upper_bound = q3 +(1.5 * iqr)
            lower_outliers = [x[0] for x in cloud_files_info if x[1] < lower_bound]
            upper_outliers = [x[0] for x in cloud_files_info if x[1] > upper_bound]
        return (lower_outliers, upper_outliers)

    def migration_data(self):
        self.update_all()
        for cloud_id in range(0, len(self.clouds)):
            (lower_outliers, upper_outliers) = self.cloud_outliers(self.clouds[cloud_id]["name"])
            yield (cloud_id, lower_outliers, upper_outliers)

    def migrate(self, name, frm, to):
        file = self.files[name]
        to_cloud = self.clouds[to]
        from_cloud = self.clouds[frm]
        if(to_cloud['used'] + file.length > to_cloud['total']):
            raise InsufficientSpaceException
        else:
            self.clouds.inc_dec_used_space(to, file.length)
            self.clouds.inc_dec_used_space(frm, -file.length)
            file.provider = to_cloud['name']