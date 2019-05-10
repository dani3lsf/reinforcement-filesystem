#!usr/bin/python3

import threading
import time
import signal
import os

from datetime import datetime, timedelta
from src.metadata.metadata import Metadata
from src.exceptions.exceptions import ProgramKilled, InsufficientSpaceException


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

    def stop(self):
        self.stopped.set()
        self.join()

    def perform_migration(self, file_name, from_cloud, to_cloud):

        path = '/' + file_name
        file = self.metadata[file_name]
        # print("Migration 1" + from_cloud + "  " + to_cloud)
        # 1- Open fh na frm
        fhr = self.providers[from_cloud].open(path)
        # print("Migration 2")
        # 2- Read com o fh na frm
        bytes_read = self.providers[from_cloud].read(fhr, path, file['length'], 0)
        # print("Migration 3")

        if bytes_read is None:
            raise Exception
        # 3- Create na cloud to
        # print("Migration 4")

        fhw = self.providers[to_cloud].create(path)
        # print("Migration 5")

        if fhw is False:
            raise Exception
        # 4- write na cloud to
        # print("Migration 6")

        try:
            n_bytes_written = self.providers[to_cloud].write(path, bytes_read, 0, fhw)
        except Exception as e:
            print(e)

        # print("Migration 7")

        if n_bytes_written is False:
            raise Exception
        # 5- del da cloud frm
        # print("Migration 8")

        result = self.providers[from_cloud].unlink(path)
        # print("Migration 9")

        if result is False:
            raise Exception
        # print("Migration 10")

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
        # print("STARTING MIGRATION")
        # migration_data = self.metadata.migration_data()
        print("MIGRATION_DATA")
        print(self.migration_data)

        for (file_name, frm, _) in self.migration_data:
            from_cloud = self.metadata.clouds[frm]['name']
            self.save_to_temp_dir(file_name, from_cloud)

        for (file_name, frm, to) in self.migration_data:
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

        # for (cloud_id, lower_outliers, _) in migration_data:
        #     # if there is a better 
        #     print("DENTRO")
        #     print((cloud_id, lower_outliers))

        #     # if there is a worse cloud
        #     if(cloud_id > 0 and lower_outliers != []):
        #         from_cloud = self.metadata.clouds[cloud_id]['name']
        #         to_cloud = self.metadata.clouds[cloud_id - 1]['name']
        #         for file_name in lower_outliers:
        #             try:
        #                 self.metadata.migrate(name=file_name, frm=cloud_id, to=cloud_id - 1)
        #                 print("Migrating " + file_name + "from " + from_cloud + "to " + to_cloud)
        #                 self.perform_migration(file_name, from_cloud, to_cloud)
        #                 print("Migration succeded")
        #             except InsufficientSpaceException:
        #                 print("Migration not succeded due to insufficient space")
        #                 pass
        #             except Exception as e:
        #                 print(e)
        #                 print("Migration not succeded due to error")
        #                 self.metadata.migrate(name=file_name, frm=cloud_id + 1, to=cloud_id)


        # for (cloud_id, _, upper_outliers) in migration_data:
        #     # if there is a better 
        #     print("DENTRO")
        #     print((cloud_id, upper_outliers))

        #     if(cloud_id < len(self.providers) - 1 and upper_outliers != []):
        #         from_cloud = self.metadata.clouds[cloud_id]['name']
        #         to_cloud = self.metadata.clouds[cloud_id + 1]['name']
        #         print("OUTLIERS")
        #         print(upper_outliers)
        #         for file_name in upper_outliers:
        #             print(file_name)
        #             try:
        #                 self.metadata.migrate(name=file_name, frm=cloud_id, to=cloud_id + 1)
        #                 print("Migrating " + file_name + "from " + from_cloud + "to " + to_cloud)
        #                 self.perform_migration(file_name, from_cloud, to_cloud)
        #                 print("Migration succeded")
        #             except InsufficientSpaceException:
        #                 print("Migration not succeded due to insufficient space")
        #                 pass
        #             except Exception as e:
        #                 print(e)
        #                 print("Migration not succeded. Cause unknown")
        #                 self.metadata.migrate(name=file_name, frm=cloud_id + 1, to=cloud_id)

    def run(self):
        # while not self.stopped.wait(self.interval.total_seconds()):
        # print("ETAPA1")
        self.metadata.acquire_lock()
        # print("ETAPA2")
        self.migrate()
        # print("ETAPA3")
        self.metadata.release_lock()
        # print("ETAPA4")
