#!/usr/bin/python3
# ------------------------------------------------------------------------------

import configparser
import os
import dropbox
import io


from time import mktime
from dropbox import files
from datetime import datetime


class Dropbox:

    class __Dropbox:
        def __init__(self):

            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../config/CONFIGURATION.INI'))

            self.access_token = config.get('DROPBOX', 'ACCESS_TOKEN')
            self.api_client = dropbox.Dropbox(self.access_token, timeout=None)
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
        ret = None
        if path[1:] in self.items:
            ret = {
                'size': self.items[path[1:]][1],
                'created': self.items[path[1:]][2],
                'modified': self.items[path[1:]][3],
                }
        return ret

    def open(self, path):
        fh = self.api_client.files_download(path)[1].raw.read()
        b = io.BytesIO(fh)
        return b

    def read(self, fh, path, length, offset):
        fh.seek(offset)
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

    def write(self, path, buf, offset, fh,overwrite=True):
        mode = (dropbox.files.WriteMode.overwrite
                 if overwrite
                 else dropbox.files.WriteMode.add)

        CHUNK_SIZE = 64000
        FILE_SIZE = len(buf)

        if FILE_SIZE <= CHUNK_SIZE:
             ret = self.api_client.files_upload(f=buf, path=path, mode=mode, mute=True)

        else:

            upload_session_start_result = self.api_client.files_upload_session_start(buf[offset: offset + CHUNK_SIZE])
            cursor = dropbox.files.UploadSessionCursor(session_id=upload_session_start_result.session_id, offset = offset)
            commit = dropbox.files.CommitInfo(path,mode=mode)
            cursor.offset = cursor.offset + CHUNK_SIZE

            while cursor.offset < FILE_SIZE:
                if (( FILE_SIZE - cursor.offset) <= CHUNK_SIZE):
                    ret= self.api_client.files_upload_session_finish(buf[cursor.offset: cursor.offset + CHUNK_SIZE],
                                                    cursor,
                                                    commit)
                else:
                    self.api_client.files_upload_session_append(buf[cursor.offset: cursor.offset + CHUNK_SIZE],
                                                    cursor.session_id,
                                                    cursor.offset)
                    cursor.offset = cursor.offset + CHUNK_SIZE

    def move(self, from_path, to_path):
        try:
            self.api_client.files_move(from_path, to_path)
            self.items[to_path[1:]] = self.items.pop(from_path[1:])
        except dropbox.exceptions.ApiError:
            return False
