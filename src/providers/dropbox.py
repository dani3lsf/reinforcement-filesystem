#!/usr/bin/python3
# ------------------------------------------------------------------------------

import logging
import configparser
import dropbox
import os


class Dropbox:
    """This class represents the Dropbox client.

    Manage Dropbox interactions through the API v2.

    """

    class __Dropbox:
        """This class is a singleton to allow to only have one instance of the dropbox class.
        """

        def __init__(self):
            # Get the credential accessing token
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../config/CONFIGURATION.INI'))

            # Setup instance variables
            self.access_token = config.get('DROPBOX', 'ACCESS_TOKEN')
            self.api_client = dropbox.Dropbox(self.access_token)
            self.logger = logging.getLogger('dropbox_client')

    instance = None

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __init__(self):
        if not Dropbox.instance:
            Dropbox.instance = Dropbox.__Dropbox()
            super().__init__()

    """Generates a dictionary given an object of metadata.
    
    Args:
        file_md: Object of metadata.
    """
    def gen_dict(self, metadata):
        result = {}
        for key in dir(metadata):
            if not key.startswith('_'):
                attr = getattr(metadata, key)
                if isinstance(attr, list):
                    tmp = []
                    for item in attr:
                        tmp.append(self.gen_dict(item))
                    result[key] = tmp
                else:
                    result[key] = attr

        return result

    """Obtains the metadata of a given file or folder.
    
    Args:
        path: Path to the desired file or folder.
    """
    def get_metadata(self, path):
        if path == '/':
            path = ''
        elif not path.startswith('/'):
            path = '/' + path

        try:
            result = None
            md = self.api_client.files_list_folder(path)
            result = self.gen_dict(md)

        except dropbox.exceptions.ApiError as err:
            if err.error.is_path() and err.error.get_path()._tag == 'not_folder':
                md = self.api_client.files_get_metadata(path)
                result = self.gen_dict(md)
                result['path'] = path
            else:
                return

        if 'entries' in result:
            for file in result.get('entries'):
                file['path'] = file.get('path_display')

        return result

    """Upload a file.
    
    Args:
        data (byte[]): A byte array with the content to be uploaded.
        path (str): The path where the content should be created/modified.
        overwrite (boolean): True, the content will overwrite, False otherwise.
    """
    def put(self, data, path, overwrite=True):
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        try:
            res = self.api_client.files_upload(f=data, path=path, mode=mode, mute=True)
        except dropbox.exceptions.ApiError as err:
            self.logger.error('*** PUT ***')

        self.logger.info('uploaded as {}'.format(res.name.encode('utf8')))

    """Download a file.
    
    Args:
        path (str): The path in the provider where the content is.
    """
    def get(self, path):
        try:
            md, res = self.api_client.files_download(path)
        except dropbox.exceptions.HttpError as err:
            self.logger.error('*** GET ***')

        self.logger.info('{} bytes; md:'.format(len(res.content), md))

        return res.content

    """Remove a file.
    
    Args:
        path (str): The path in the provider which should be deleted.
    """
    def delete(self, path):
        if path == '/':
            path = ''
        elif not path.startswith('/'):
            path = '/' + path

        self.logger.info("Delete path: {}".format(path))
        try:
            self.api_client.files_delete(path)
        except dropbox.exceptions.ApiError as err:
            self.logger.error('*** DELETE *** {}'.format(err))

    """Move a file.
    
    Args:
        from_path (str): The source path in the provider where the file is.
        to_path (str): The destination path in the provider where the file should be moved.
    """
    def move(self, from_path, to_path):
        self.logger.info("Move from path {} to path {}".format(from_path, to_path))
        try:
            self.api_client.files_move(from_path, to_path)
        except dropbox.exceptions.ApiError as err:
            self.logger.error('*** DELETE *** {}'.format(err))

#============================
      # Upload chunk of data to Dropbox.
    def dbxChunkedUpload(self, data, upload_id, offset=0):
        if upload_id == "":
          result = self.api_client.files_upload_session_start(data)
        else:
          cursor = dropbox.files.UploadSessionCursor(upload_id, offset)
          result = self.api_client.files_upload_session_append_v2(data, cursor)

        result = self.dbxStruct(result)
        result.update({'offset': offset+len(data), 'upload_id': result['session_id']})

        return result

      # Commit chunked upload to Dropbox.
    def dbxCommitChunkedUpload(self, path, upload_id, offset, overwrite=True):
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        cursor = dropbox.files.UploadSessionCursor(upload_id, offset)
        commitinfo = dropbox.files.CommitInfo(path,mode=mode)
        result = self.api_client.files_upload_session_finish("".encode(), cursor, commitinfo)
        result = self.dbxStruct(result)

        return result

      # Get Dropbox filehandle.
    def dbxFilehandle(self, path, seek=False):
        result = self.api_client.files_download(path)[1].raw
        return result

    def dbxStruct(self, obj):
        structname = obj.__class__.__name__
        data = {}

        for key in dir(obj):
          if not key.startswith('_'):
            if isinstance(getattr(obj, key), list):
              tmpdata = []
              for item in getattr(obj, key):
                tmpdata.append(self.dbxStruct(item))
              data.update({key: tmpdata})
            else:
              data.update({key: getattr(obj, key)})

        if structname == 'FolderMetadata':
          data.update({'.tag': 'folder'})
        if structname == 'FileMetadata':
          data.update({'.tag': 'file'})

        return data