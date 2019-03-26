from src.exceptions.exceptions import InsufficientSpaceException
import configparser
import os

class CloudManagement:

    def __init__(self):
        self.clouds = []
        config = configparser.ConfigParser()
        config.read(os.path.join(os.path.abspath(os.path.dirname(__file__)), '../../config/CONFIGURATION.INI'))
        for cloud in config.sections():
            name = str(cloud).lower()
            download_speed = int(config[cloud]['DOWNLOAD_SPEED'])
            total_space = int(config[cloud]['TOTAL_SPACE'])
            used_space = int(config[cloud]['USED_SPACE'])
            self.clouds.append({"name": name, "speed": download_speed, "total": total_space, "used": used_space})
        self.clouds.sort(key = lambda x: x['speed'])
        print(self.clouds)

    def __iter__(self):
        for cloud in self.clouds:
            yield cloud

    def __getitem__(self, cloud_id):
          return self.clouds[cloud_id]
    
    def __len__(self):
        return len(self.clouds)

    def __repr__(self):
        return 'clouds: ' + self.clouds.__repr__()

    def choose_cloud_for_insertion(self, file_length):
        for cloud_id in range(0, len(self.clouds)):
            cloud = self.clouds[cloud_id]
            if (cloud['used'] < cloud['total']) and \
                (cloud['used'] + file_length < cloud['total']):
                return (cloud_id, cloud['name'])
        return None

    def inc_dec_used_space(self, cloud_id, diff):
        cloud = self.clouds[cloud_id]
        print("***** total: " + str(cloud['total']) + " used: " + str(cloud['used']) + "+" + str(diff) + " ******")
        if cloud['used'] + diff > cloud['total']:
            raise InsufficientSpaceException
        self.clouds[cloud_id]['used'] += diff

    def get_cloud_id_by_name(self, cloud_name):
        print(cloud_name)
        for cloud_id in range(0, len(self.clouds)):
            cloud = self.clouds[cloud_id]
            if cloud['name'] == cloud_name:
                return cloud_id
        return None