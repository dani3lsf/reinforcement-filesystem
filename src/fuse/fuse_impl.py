#!/usr/bin/python3
# ------------------------------------------------------------------------------

from __future__ import with_statement
from datetime import datetime
from src.exceptions.exceptions import InsufficientSpaceException

import errno
import os
import re
import time

from fuse import FuseOSError, Operations

def init_metadata(metadata, providers):
    metadata.acquire_lock()
    for (provider_name, provider_impl) in providers.items():
        file_names = list(provider_impl.listdir())
        for file_name in file_names:
            path = '/' + file_name
            file_length = provider_impl.lstat(path)['st_size']
            metadata.add_file_to_cloud(file_name, file_length, provider_name)
    metadata.release_lock()
    return metadata


class ProviderFS(Operations):
    def __init__(self, providers, metadata):
        print("0")
        self.providers = providers
        self.default_provider = list(providers.values())[1]
        self.metadata = init_metadata(metadata, providers)
        # utilizado quando se altera exteriormente o fh do
        # ficheiro que o Fuse pensa ser o atual
        self.fh_updated = {}

    def getattr(self, path, fh=None):
        print("1" + " " + path)

        self.metadata.acquire_lock()
        # path[1:] porque o path é antecedido por um '/'
        cloud_name = self.metadata.get_file_cloud_name(path[1:])
        print(cloud_name)
        
        if cloud_name:
            result = self.providers[cloud_name].lstat(path)
        else:
            result = self.default_provider.lstat(path)

        self.metadata.release_lock()

        if result is None:
            raise FuseOSError(errno.ENOENT)

        return result

    def readdir(self, path, fh):
        print("2" + " " + path)

        self.metadata.acquire_lock()
        ret_list = ['.', '..'] + self.metadata.get_all_file_names()
        self.metadata.release_lock()
        return ret_list

        #return ['.', '..'] + list(self.provider.listdir())

    def unlink(self, path):
        print("3" + " " + path)
        self.metadata.acquire_lock()
        cloud_name = self.metadata.get_file_cloud_name(path[1:])
        result = self.providers[cloud_name].unlink(path)
        if result is False:
            self.metadata.release_lock()
            raise FuseOSError(errno.ENOENT)
        else:
            self.metadata.del_file(path[1:])

        self.metadata.release_lock()

        return result

    def rename(self, old, new):
        print("4 " + old + " " + new)
        self.metadata.acquire_lock()
        cloud_name = self.metadata.get_file_cloud_name(old[1:])
        ret = self.providers[cloud_name].rename(old, new)
        if ret is False:
            self.metadata.release_lock()
            raise FuseOSError(errno.EPERM)
        else:
            self.metadata.rename_file(old[1:], new[1:])
        self.metadata.release_lock()

    def open(self, path, flags):
        print("5" + " " + path)
        if flags & os.O_APPEND:
            raise FuseOSError(errno.EOPNOTSUPP)

        self.metadata.acquire_lock()
        self.metadata.add_read(path[1:], datetime.now())
        cloud_name = self.metadata.get_file_cloud_name(path[1:])
        fh = self.providers[cloud_name].open(path)
        self.metadata.release_lock()
        return fh

    def create(self, path, mode, fi=None):
        print("6" + " " + path)
        self.metadata.acquire_lock()
        cloud_info = self.metadata.choose_cloud_for_insertion(0)
        if cloud_info is None:
            self.metadata.release_lock()
            raise FuseOSError(errno.EPERM)
        else:
            (cloud_id, cloud_name) = cloud_info
            fh = self.providers[cloud_name].create(path)
            if fh is False:
                self.metadata.release_lock()
                raise FuseOSError(errno.EPERM)
            else:
                self.metadata.add_file_to_cloud(path[1:], 0, cloud_name)
                self.metadata.release_lock()
                return fh

    def read(self, path, length, offset, fh):
        #print("7" + " " + path)
        self.metadata.acquire_lock()
        cloud_name = self.metadata.get_file_cloud_name(path[1:])
        bytes_read = self.providers[cloud_name].read(fh, path, length, offset)
        if bytes_read is None:
            self.metadata.release_lock()
            raise FuseOSError(errno.EROFS)
        self.metadata.release_lock()
        return bytes_read

    def write(self, path, buf, offset, fh):
        print("8" + " " + path)
        self.metadata.acquire_lock()
        fh = self.fh_updated.get(fh, fh)
        file = self.metadata[path[1:]]
        file_length = file.length
        new_length = len(buf) + offset

        try:
            self.metadata.inc_dec_file_length(path[1:], new_length - file_length)
            cloud_name = self.metadata.get_file_cloud_name(path[1:])
            ret = self.providers[cloud_name].write(path, buf, offset, fh)
   
            if ret is False:
                self.metadata.release_lock()
                raise FuseOSError(errno.EIO)

            return ret
        except InsufficientSpaceException:
            try:
                fhr = self.open(path, 32768)
                buf_init = self.read(path, offset, 0, fhr)
                self.unlink(path)
                cloud_info = self.metadata.choose_cloud_for_insertion(new_length)

                if cloud_info is None:
                    raise FuseOSError(errno.EIO)

                (cloud_id, to_cloud) = cloud_info
                fhw = self.providers[to_cloud].create(path)

                if fhw is False:
                    raise FuseOSError(errno.EPERM)

                self.fh_updated[fh] = fhw
                self.metadata.add_file_to_cloud(path[1:], 0, to_cloud)

                if offset != 0:
                    self.write(path, buf_init, 0, fhw)

                ret = self.write(path, buf, offset, fhw)
                
                return ret
            finally:
                self.metadata.release_lock()
        finally:
            self.metadata.release_lock()

    def release(self, path, fh):
        if fh in self.fh_updated:
            del self.fh_updated[fh]