#!/usr/bin/python3
# ------------------------------------------------------------------------------

import httplib2
import os
import io
import mimetypes

from time import mktime
from datetime import datetime
from googleapiclient import discovery, http
from oauth2client import client
from oauth2client import tools
from oauth2client.file import Storage

SCOPES = 'https://www.googleapis.com/auth/drive'
CLIENT_SECRET_FILE = 'config/client_secrets.json'
APPLICATION_NAME = 'Google Drive Fuse Filesystem'


class GoogleDrive:
    class __GoogleDrive:
        def __init__(self):
            self.credentials = self.get_credentials()
            self.http = self.credentials.authorize(httplib2.Http())
            self.service = discovery.build('drive', 'v3', http=self.http, cache_discovery=False)
            self.items = {}

        @staticmethod
        def get_credentials():
            home_dir = os.path.expanduser('~')
            credential_dir = os.path.join(home_dir, '.credentials')
            if not os.path.exists(credential_dir):
                os.makedirs(credential_dir)
            credential_path = os.path.join(credential_dir,
                                           'drive-fs.json')

            store = Storage(credential_path)
            credentials = store.get()
            if not credentials or credentials.invalid:
                flow = client.flow_from_clientsecrets(CLIENT_SECRET_FILE, SCOPES)
                flow.user_agent = APPLICATION_NAME
                flags = tools.argparser.parse_args(args=[])
                credentials = tools.run_flow(flow, store, flags)

            return credentials

    instance = None

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __init__(self):
        if not GoogleDrive.instance:
            GoogleDrive.instance = GoogleDrive.__GoogleDrive()
            super().__init__()

    def list_files_names(self):
        results = self.service.files().list(fields="nextPageToken,files(id, name, size, modifiedTime, createdTime)").execute()

        for item in results.get('files', []):
            date_format = '%Y-%m-%dT%H:%M:%S.%fZ'
            created_str = str(item['createdTime'])
            modified_str = str(item['modifiedTime'])
            created = mktime(datetime.strptime(created_str, date_format).timetuple())
            modified = mktime(datetime.strptime(modified_str, date_format).timetuple())
            self.items[item['name']] = (item['id'], int(item.get('size') or '0'), created, modified)

        return self.items.keys()

    def get_metadata(self, path):
        if path[1:] not in self.items:
            return None
        else:
            ret = {
                'size': self.items[path[1:]][1],
                'created': self.items[path[1:]][2],
                'modified': self.items[path[1:]][3],
            }
        return ret


    def open(self, path, delay=False):
        request = self.service.files().get_media(fileId=self.items[path[1:]][0])
        fh = io.BytesIO()
        try:
            downloader = http.MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
        except Exception:
            pass


        return fh

    def read(self, fh, path, length, offset):
        fh.seek(offset)
        return fh.read(length)

    def delete(self, path):
        try:
            self.service.files().delete(fileId=self.items[path[1:]][0]).execute()
            del self.items[path[1:]]
        except Exception:
            return False

    def put(self, bytes, path, overwrite=True, delay=False):
        mime = mimetypes.guess_type(path)[0]
        if mime is None:
            mime = 'application/octet-stream'

        fh = io.BytesIO(bytes)
        media = http.MediaIoBaseUpload(fh, mimetype=mime)
        file_metadata = {'name': path[1:]}

        try:
            ret = self.service.files().create(body=file_metadata, media_body=media).execute()
            self.items[ret['name']] = (ret['id'], 0, None, None)
        except Exception:
            return False

    def write(self, path, buf, offset, fh):
        fh.seek(offset)
        fh.write(buf)

        mime = mimetypes.guess_type(path[1:])[0]
        if mime is None:
            mime = 'application/octet-stream'

        media = http.MediaIoBaseUpload(fh, mimetype=mime, resumable=True)
        file_metadata = {'name': path[1:]}
        self.service.files().update(fileId=self.items[path[1:]][0], body=file_metadata, media_body=media).execute()
        tmp = list(self.items[path[1:]])
        tmp[1] += len(buf)
        self.items[path[1:]] = tuple(tmp)

    def move(self, from_path, to_path):
        file_metadata = {'name': to_path[1:]}
        self.service.files().update(fileId=self.items[from_path[1:]][0], body=file_metadata).execute()
        self.items[to_path[1:]] = self.items.pop(from_path[1:])

    def release(self, fh):
        return 0

