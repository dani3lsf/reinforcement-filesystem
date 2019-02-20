import configparser
import os
import tempfile
import logging
import onedrivesdk


class OneDrive:
    class __OneDrive:
        def __init__(self):
            config = configparser.ConfigParser()
            config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../config/CONFIGURATION.INI'))

            self.redirect_uri = 'http://localhost:8080/'
            self.client_id = config.get('ONEDRIVE', 'CLIENT_ID')
            self.client_secret = config.get('ONEDRIVE', 'CLIENT_SECRET')
            self.api_base_url = 'https://api.onedrive.com/v1.0/'
            self.scopes = ['wl.signin', 'wl.offline_access', 'onedrive.readwrite']

            if os.path.isfile("sessionO.pickle"):
                return self.loadOneDrive()
            else:
                http_provider = onedrivesdk.HttpProvider()
                auth_provider = onedrivesdk.AuthProvider(http_provider, self.client_id, self.scopes)
                client = onedrivesdk.OneDriveClient(self.api_base_url, auth_provider, http_provider)
                auth_url = client.auth_provider.get_auth_url(self.redirect_uri)
                print(auth_url)
                code = input('Code:\n')
                client.auth_provider.authenticate(code, self.redirect_uri, self.client_secret)
                auth_provider.save_session(path='sessionO.pickle')  # ISTO NAO E SEGURO
                self.client = onedrivesdk.OneDriveClient(self.api_base_url, auth_provider, http_provider)

        def loadOneDrive(self):
            http_provider = onedrivesdk.HttpProvider()
            auth_provider = onedrivesdk.AuthProvider(http_provider, self.client_id, self.scopes)
            auth_provider.load_session(path='sessionO.pickle')
            auth_provider.refresh_token()
            self.client = onedrivesdk.OneDriveClient(self.api_base_url, auth_provider, http_provider)

    instance = None

    def __getattr__(self, name):
        return getattr(self.instance, name)

    def __init__(self):
        if not OneDrive.instance:
            OneDrive.instance = OneDrive.__OneDrive()
            super().__init__()

    """
            Create a directory.
            This method is useless.
    """

    def create(self, path):
        pass

    """
        Upload a file.
    """

    def put(self, data, path):
        path = path[1::]
        with tempfile.NamedTemporaryFile() as f:
            pth = path.split("/")[::-1][0]
            fp = open(f.name, 'rb+')
            fp.write(data)
            fp.close()
            self.client.item(drive='me', id='root').children[pth].upload(f.name)
            f.close()
        return len(data)

    """
        Download a file.
    """

    def get(self, path):
        if self.check_if_exists(path):
            f = tempfile.NamedTemporaryFile()
            self.client.item(drive='me', path=path).download(f.name)
            with open(f.name, 'rb') as file:
                data = file.read()
                file.close()

            return data
        else:
            pth = path.split("/")[::-1][0]
            f = tempfile.NamedTemporaryFile()
            self.client.item(drive='me', id='root').children[pth].upload(f.name)
            with open(f.name, 'rb') as file:
                data = file.read()
                file.close()

            return data

    """
        Remove a file.
    """

    def delete(self, path):
        try:
            self.client.item(drive='me', path=path).delete()
        except Exception as e:
            print(e, 'on remove onedrive')

    def move(self, old_name, new_name):
        """
        Moves a file.
        :param old_name: Path to the file.
        :param new_name: New name.
        :return: None
        """
        renamed_item = onedrivesdk.Item()
        renamed_item.name = new_name[new_name.rfind("/") + 1::]
        xx = self.client.item(drive='me', path=old_name).get()
        self.client.item(drive='me', id=xx.id).update(renamed_item)

    def check_if_exists(self, path):
        """
        Checks if a file exists.
        :param path: Path to the file.
        :return: True if the file exists, else False.
        """
        try:
            self.client.item(drive='me', path=path).get()
            return True
        except:
            return False