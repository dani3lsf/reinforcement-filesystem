#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse

from src.fuse.fuse_impl import ProviderFS
from src.providers.provider import Provider
from src.providers.dropbox import Dropbox
from src.providers.google_drive import GoogleDrive
from fuse import FUSE


def main(mountpoint):
    # Número de provedores
    providers_number = 2

    # Provedor Dropbox
    dropbox = Dropbox()

    # Provedor GoogleDrive
    google_drive = GoogleDrive()

    provider = Provider(dropbox)

    # Fuse Implementation
    fuse_impl = ProviderFS(provider)

    FUSE(fuse_impl, mountpoint, foreground=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mountpoint', help='Directory on which the filesystem will be mounted')
    args = vars(parser.parse_args())

    main(args.get('mountpoint'))
