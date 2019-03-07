#!/usr/bin/python3
# ------------------------------------------------------------------------------

import configparser
import os
import dropbox

from time import mktime
from dropbox import files
from datetime import datetime


class Dropbox:

    class __Dropbox:
        def __init__(self):

            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../config/configuration.ini'))

            self.access_token = config.get('DROPBOX', 'ACCESS_TOKEN')
            self.api_client = dropbox.Dropbox(self.access_token)
            self.items = {}

    instance = None

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __init__(self):
        if not Dropbox.instance:
            Dropbox.instance = Dropbox.__Dropbox()
            super().__init__()

    def list_files_names(self):
        results = self.api_client.files_list_folder('')

        for item in getattr(results, 'entries'):

            if isinstance(item, dropbox.files.FileMetadata):
                date_format = '%Y-%m-%d %H:%M:%S'
                modified_str = str(getattr(item, 'client_modified'))
                modified = mktime(datetime.strptime(modified_str, date_format).timetuple())

                if 'entries' in dir(item):
                    self.items[getattr(item, 'name')] = (getattr(item, 'id'), 0, modified, modified)
                else:
                    self.items[getattr(item, 'name')] = (getattr(item, 'id'), getattr(item, 'size'), modified, modified)

        return self.items.keys()

    def get_metadata(self, path):
        if path[1:] not in self.items:
            return None
        else:
            return {
                'size': self.items[path[1:]][1],
                'created': self.items[path[1:]][2],
                'modified': self.items[path[1:]][3],
                }

    def open(self, path):
        return None

    def read(self, fh, path, length, offset):
        fh = self.api_client.files_download(path)[1].raw
        return fh.read(length)

    def delete(self, path):
        try:
            self.api_client.files_delete(path)
            del self.items[path[1:]]
        except dropbox.exceptions.ApiError:
            return False

    def put(self, bytes, path, overwrite=True):
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        try:
            ret = self.api_client.files_upload(f=bytes, path=path, mode=mode, mute=True)
            self.items[getattr(ret, 'name')] = (getattr(ret, 'id'), 0, None, None)
        except dropbox.exceptions.ApiError:
            return False

    def write(self, path, buf, offset, fh, overwrite=True):
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)

        try:
            ret = self.api_client.files_upload(f=buf, path=path, mode=mode, mute=True)
            # TODO: resolução manha
            tmp = list(self.items[getattr(ret, 'name')])
            tmp[1] = getattr(ret, 'size')
            self.items[getattr(ret, 'name')] = tuple(tmp)
        except dropbox.exceptions.ApiError:
            return False

    def move(self, from_path, to_path):
        try:
            self.api_client.files_move(from_path, to_path)
            self.items[to_path[1:]] = self.items.pop(from_path[1:])
        except dropbox.exceptions.ApiError:
            return False
