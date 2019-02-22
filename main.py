#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse

from src.fuse.fuse_impl import Passthrough
from src.providers.dropbox import Dropbox
# from src.providers.onedrive import OneDrive
from fuse import FUSE


def main(mountpoint):
    # Número de provedores
    providers_number = 1

    # Provedor Dropbox
    dropbox = Dropbox()

    # Provedor OneDrive
    # one_drive = OneDrive()

    # Fuse Implementation
    fuse_impl = Passthrough(dropbox)

    FUSE(fuse_impl, mountpoint, foreground=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mountpoint', help='Directory on which the filesystem will be mounted')
    args = vars(parser.parse_args())

    main(args.get('mountpoint'))
