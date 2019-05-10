#!usr/bin/python3

import threading
import time
import signal
import os

from datetime import datetime, timedelta
from src.metadata.metadata import Metadata
from src.exceptions.exceptions import ProgramKilled, InsufficientSpaceException

MIGRATION_SPEED = 10 #MB/s
TEMP_DIR = "temp/"

if not os.path.isdir(TEMP_DIR):
    print("Creating directory %s" % TEMP_DIR)
    os.mkdir(TEMP_DIR)


class Migration(threading.Thread):
    def __init__(self, metadata, providers, migration_data):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        # self.interval = interval
        self.metadata = metadata
        self.providers = providers
        self.migration_data = migration_data
        self.duration = None

    def stop(self):
        self.stopped.set()
        self.join()

    def perform_migration(self, file_name, from_cloud, to_cloud):

        path = '/' + file_name
        file = self.metadata[file_name]
        # 1- Open fh na frm
        fhr = self.providers[from_cloud].open(path)
        # 2- Read com o fh na frm
        bytes_read = self.providers[from_cloud].read(fhr, path, file['length'], 0)

        if bytes_read is None:
            raise Exception
        # 3- Create na cloud to

        fhw = self.providers[to_cloud].create(path)

        if fhw is False:
            raise Exception
        # 4- write na cloud to

        try:
            n_bytes_written = self.providers[to_cloud].write(path, bytes_read, 0, fhw)
        except Exception as e:
            print(e)

        if n_bytes_written is False:
            raise Exception
        # 5- del da cloud frm

        result = self.providers[from_cloud].unlink(path)

        if result is False:
            raise Exception

    def save_to_temp_dir(self, file_name, from_cloud):
        path = '/' + file_name
        file = self.metadata[file_name]

        fhr = self.providers[from_cloud].open(path)

        bytes_read = self.providers[from_cloud].read(fhr, path, file['length'], 0)

        if bytes_read is None:
            raise Exception

        with open(TEMP_DIR + file_name, 'wb') as writer:
            writer.write(bytes_read)

        result = self.providers[from_cloud].unlink(path)

        if result is False:
            raise Exception

        self.metadata.del_file(file_name)

    def get_from_temp_dir(self, file_name, to_cloud):

        path = '/' + file_name

        with open(TEMP_DIR + file_name, 'rb') as reader:
            bytes_read = reader.read()

        if self.metadata.test_if_fits(len(bytes_read), to_cloud) == False:
            raise InsufficientSpaceException

        fhw = self.providers[to_cloud].create(path)
        self.metadata.add_file_to_cloud(file_name, 0, to_cloud)

        if fhw is False:
            raise Exception

        try:
            n_bytes_written = self.providers[to_cloud].write(path, bytes_read, 0, fhw)
        except Exception as e:
            print(e)

        if n_bytes_written is False:
            raise Exception

        self.metadata.inc_dec_file_length(file_name, n_bytes_written)
        os.remove(TEMP_DIR + file_name)

    def migrate(self):
        print("STARTING MIGRATION")
        # migration_data = self.metadata.migration_data()
        print(self.migration_data)

        bytes_moved = 0

        for (file_name, frm, _, length) in self.migration_data:
            bytes_moved += length
            from_cloud = self.metadata.clouds[frm]['name']
            self.save_to_temp_dir(file_name, from_cloud)

        for (file_name, frm, to, _) in self.migration_data:
            to_cloud = self.metadata.clouds[to]['name']

            try:
                self.get_from_temp_dir(file_name, to_cloud)
            except InsufficientSpaceException:
                from_cloud = self.metadata.clouds[frm]['name']
                try:
                    self.get_from_temp_dir(file_name, from_cloud)
                except InsufficientSpaceException:
                    length = os.path.getsize(TEMP_DIR + file_name)
                    (cloud_id, cloud_name) = self.metadata.choose_cloud_for_insertion(length)
                    self.get_from_temp_dir(file_name, cloud_name)

        return bytes_moved

    def run(self):
        # while not self.stopped.wait(self.interval.total_seconds()):
        
        ti = time.time()
        self.metadata.acquire_lock()

        bytes_moved = self.migrate()
        self.duration = bytes_moved / (MIGRATION_SPEED * (10**6))
        print(self.duration)

        self.metadata.release_lock()
        tf = time.time()
        diff = tf - ti
        time_to_wait = self.duration - diff
        print(time_to_wait)
        if (time_to_wait > 0):
            time.sleep(time_to_wait)
        


