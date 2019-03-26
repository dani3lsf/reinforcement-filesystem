#!/usr/bin/python3
# ------------------------------------------------------------------------------

import argparse

from src.fuse.fuse_impl import ProviderFS
from src.fuse.fuse_impl2 import ProviderFS_No_Migration
from src.providers.provider import Provider
from src.providers.dropbox import Dropbox
from src.providers.local import Local
from src.providers.google_drive import GoogleDrive
from datetime import datetime, timedelta
from src.metadata.metadata import Metadata, File
from src.exceptions.exceptions import ProgramKilled, InsufficientSpaceException
from src.migration.migration import Migration
import signal
from fuse import FUSE

WAIT_TIME_SECONDS = 10

def signal_handler(signum, frame):
    raise ProgramKilled

def main(mountpoint):

    # Número de provedores
    providers_number = 3
    providers = {}

    # # Provedor Local
    local = Local('LOCAL1')
    provider = Provider(local)
    providers['local1'] = provider

    local = Local('LOCAL2')
    provider = Provider(local)
    providers['local2'] = provider

    # Provedor Dropbox
    #dropbox = Dropbox()
    #provider = Provider(dropbox)
    #providers['dropbox'] = provider

    # Provedor GoogleDrive
    # google_drive = GoogleDrive()
    # provider = Provider(google_drive)
    # providers['google_drive'] = provider
    
    # Initializing Metadata
    meta = Metadata()

    # # Global Provider
    fuse_impl = ProviderFS(providers, meta)
    
    migration = Migration(interval=timedelta(seconds=WAIT_TIME_SECONDS), metadata=meta, providers=providers)
    migration.start()

    #fuse_impl = ProviderFS_No_Migration(provider)

    try:
        FUSE(fuse_impl, mountpoint, foreground=True)
    except ProgramKilled:
        print("Program killed: running cleanup code")
        migration.stop()


if __name__ == '__main__':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    parser = argparse.ArgumentParser()
    parser.add_argument('mountpoint', help='Directory on which the filesystem will be mounted')
    args = vars(parser.parse_args())

    main(args.get('mountpoint'))
