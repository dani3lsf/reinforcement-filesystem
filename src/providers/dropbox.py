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

    """Create a directory.
    As dropbox automatically create parent folder in puts, this method is useless.
    
    Args:
        path (str): The path which the folder should be created.
    """
    def create(self, path):
        self.logger.info("Create path:" + path)

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
