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
        print(path)
        print(ret)
        return ret
        # if path[1:] not in self.items:
        #     return None
        # else:
        #     return {
        #         'size': self.items[path[1:]][1],
        #         'created': self.items[path[1:]][2],
        #         'modified': self.items[path[1:]][3],
        #         }

    def open(self, path):
        fh = self.api_client.files_download(path)[1].raw.read()
        #print(fh)
        b = io.BytesIO(fh)
        print("TYPE" + str(type(b)))
        return b

    def read(self, fh, path, length, offset):
        fh.seek(offset)
        print("OIOI")
        print(len(fh.read(length)))
        return fh.read(length)

    # def open(self, path):
    #     request = self.service.files().get_media(fileId=self.items[path[1:]][0])
    #     fh = io.BytesIO()
    #     try:
    #         downloader = http.MediaIoBaseDownload(fh, request)
    #         done = False
    #         while done is False:
    #             status, done = downloader.next_chunk()
    #     except Exception:
    #         pass

    #     return fh

    # def open(self, path):
    #     return None

    # def read(self, fh, path, length, offset):
    #     print("REAGIND2"+ str(offset))
    #     fh = self.api_client.files_download(path)[1].raw
    #     print("OIOI")
    #     print(len(fh.read(length)))
    #     return fh.read(length)

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

    # def write(self, path, buf, offset, fh, overwrite=True):
    #     mode = (dropbox.files.WriteMode.overwrite
    #             if overwrite
    #             else dropbox.files.WriteMode.add)

    #     try:
    #         ret = self.api_client.files_upload(f=buf, path=path, mode=mode, mute=True)
    #         # TODO: resolução manha
    #         tmp = list(self.items[getattr(ret, 'name')])
    #         tmp[1] = getattr(ret, 'size')
    #         self.items[getattr(ret, 'name')] = tuple(tmp)
    #     except dropbox.exceptions.ApiError:
    #         return False

    # def write(self, path, buf, offset, fh,overwrite=True):
    #     print("Comprimento: " + str(len(buf)))
    #     print("OFFSET:" + str(offset))
    #     result = self.api_client.files_upload_session_start(buf)
    #     print(result)
    #     result = result.session_id
    #     print(result)
    #     offset = len(buf)
    #     mode = (dropbox.files.WriteMode.overwrite
    #             if overwrite
    #             else dropbox.files.WriteMode.add)
       
    #     cursor = dropbox.files.UploadSessionCursor(result, offset)

    #     print("CUROSR OK")
    #     commitinfo = dropbox.files.CommitInfo(path,mode=mode)
    #     print("COMMINT OK")
    #     result = self.api_client.files_upload_session_finish("".encode(), cursor, commitinfo)
    #     print("Write efetuado")

    def write(self, path, buf, offset, fh,overwrite=True):
        mode = (dropbox.files.WriteMode.overwrite
                 if overwrite
                 else dropbox.files.WriteMode.add)

        CHUNK_SIZE = 64000
        FILE_SIZE = len(buf)

        if FILE_SIZE <= CHUNK_SIZE:
             print("TUDOOOO")
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
                print("UPLOAD")
        print("Write efetuado")





    #     try:
    #         self.chunked_upload(,)
    #         # Check for the beginning of the file.
    #         if fh in self.openfh:
    #             if self.openfh[fh]['f'] == False:
    #                 # Check if the write request exceeds the maximum buffer size.
    #                 if len(buf) >= self.write_cache or len(buf) < 4096:
    #                     result = self.chunked_upload(buf, "", 0)
    #                     self.openfh[fh]['f'] = {'upload_id':result['upload_id'], 'offset':result['offset'], 'buf':''}
    #                 else:
    #                     self.openfh[fh]['f'] = {'upload_id':'', 'offset':0, 'buf':buf}
    #                 return len(buf)
    #             else:
    #                 if len(buf)+len(self.openfh[fh]['f']['buf']) >= self.write_cache or len(buf) < 4096:
    #                     result = self.chunked_upload(self.openfh[fh]['f']['buf']+buf, self.openfh[fh]['f']['upload_id'], self.openfh[fh]['f']['offset'])
    #                     self.openfh[fh]['f'] = {'upload_id':result['upload_id'], 'offset':result['offset'], 'buf':''}
    #                 else:
    #                     self.openfh[fh]['f'].update({'buf':self.openfh[fh]['f']['buf']+buf})
    #                 return len(buf)
    #         else:
    #             raise FuseOSError(EIO)
    #     except Exception:
    #         raise FuseOSError(EIO)


    # """Upload chunk of data to Dropbox.
    
    # Args:
    #     data: Bytes to upload.
    #     upload_id: A unique identifier for the upload session. 
    #     offset: The amount of data that has been uploaded so far.
    # """
    # def chunked_upload(self, data, upload_id, offset=0):
    #     if upload_id == "":
    #       result = self.api_client.files_upload_session_start(data)
    #     else:
    #       cursor = dropbox.files.UploadSessionCursor(upload_id, offset)
    #       result = self.api_client.files_upload_session_append_v2(data, cursor)

    #     result = self.gen_dict(result)
    #     result.update({'offset': offset+len(data), 'upload_id': result['session_id']})

    #     return result

    # """Commit chunked upload to Dropbox.
    
    # Args:
    #     path: Path.
    #     upload_id: A unique identifier for the upload session. 
    #     offset: The amount of data that has been uploaded so far.
    #     overwrite: Overwrite file or not.
    # """
    # def commit_chunked_upload(self, path, upload_id, offset, overwrite=True):
    #     mode = (dropbox.files.WriteMode.overwrite
    #             if overwrite
    #             else dropbox.files.WriteMode.add)
    #     cursor = dropbox.files.UploadSessionCursor(upload_id, offset)
    #     commitinfo = dropbox.files.CommitInfo(path,mode=mode)
    #     result = self.api_client.files_upload_session_finish("".encode(), cursor, commitinfo)
    #     result = self.gen_dict(result)

    #     return result

    def move(self, from_path, to_path):
        try:
            self.api_client.files_move(from_path, to_path)
            self.items[to_path[1:]] = self.items.pop(from_path[1:])
        except dropbox.exceptions.ApiError:
            return False
