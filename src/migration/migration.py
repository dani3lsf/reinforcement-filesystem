#!usr/bin/python3

from datetime import datetime, timedelta
from src.metadata.metadata import Metadata, File
from src.exceptions.exceptions import ProgramKilled, InsufficientSpaceException

import threading, time, signal

class Migration(threading.Thread):
    def __init__(self, interval, metadata, providers):
        threading.Thread.__init__(self)
        self.daemon = False
        self.stopped = threading.Event()
        self.interval = interval
        self.metadata = metadata
        self.providers = providers

    def stop(self):
        self.stopped.set()
        self.join()

    def perform_migration(self, file_name, from_cloud, to_cloud):
        path = '/' + file_name
        file = self.metadata[file_name]
        # 1- Open fh na frm
        fhr = self.providers[from_cloud].open(path)
        # 2- Read com o fh na frm
        bytes_read = self.providers[from_cloud].read(fhr, path, file.length, 0)
        if bytes_read is None:
            raise Exception
        # 3- Create na cloud to
        fhw = self.providers[to_cloud].create(path)
        if fhw is False:
            raise Exception
        # 4- write na cloud to
        n_bytes_written = self.providers[to_cloud].write(path, bytes_read, 0, fhw)
        if n_bytes_written is False:
            raise Exception
        # 5- del da cloud frm
        result = self.providers[from_cloud].unlink(path)
        if result is False:
            raise Exception

    def migrate(self):
        migration_generator = self.metadata.migration_data()
        for (cloud_id, lower_outliers, upper_outliers) in migration_generator:
            # if there is a better 
            print((cloud_id, lower_outliers, upper_outliers))
            if(cloud_id < len(self.providers) - 1 and upper_outliers != []):
                from_cloud = self.metadata.clouds[cloud_id]['name']
                to_cloud = self.metadata.clouds[cloud_id + 1]['name']
                for file_name in upper_outliers:
                    print(file_name)
                    try:
                        self.metadata.migrate(name=file_name, frm=cloud_id, to=cloud_id + 1)
                        print("Migrating " + file_name + "from " + from_cloud + "to " + to_cloud)
                        self.perform_migration(file_name, from_cloud, to_cloud)
                        print("Migration succeded")
                    except InsufficientSpaceException:
                        print("Migration not succeded")
                        pass
                    except Exception:
                        print("Migration not succeded")
                        self.metadata.migrate(name=file_name, frm=cloud_id + 1, to=cloud_id)

            # if there is a worse cloud
            if(cloud_id > 0 and lower_outliers != []):
                from_cloud = self.metadata.clouds[cloud_id]['name']
                to_cloud = self.metadata.clouds[cloud_id - 1]['name']
                for file_name in lower_outliers:
                    try:
                        self.metadata.migrate(name=file_name, frm=cloud_id, to=cloud_id - 1)
                        print("Migrating " + file_name + "from " + from_cloud + "to " + to_cloud)
                        self.perform_migration(file_name, from_cloud, to_cloud)
                        print("Migration succeded")
                    except InsufficientSpaceException:
                        print("Migration not succeded")
                        pass
                    except Exception:
                        print("Migration not succeded")
                        self.metadata.migrate(name=file_name, frm=cloud_id + 1, to=cloud_id)
        
    def run(self):
        while not self.stopped.wait(self.interval.total_seconds()):
            self.metadata.acquire_lock()
            self.migrate()
            self.metadata.release_lock()





