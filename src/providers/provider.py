#!/usr/bin/python3
# ------------------------------------------------------------------------------

import time
import stat
import os
import io

from time import time


class Provider:
    def __init__(self, pd):
        self.pd = pd
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.fh = {}
        self.next_fh = 0

    def lstat(self, path):

        now = int(time())

        if path == '/':
            return {
                'st_atime': now,
                'st_gid': self.gid,
                'st_mode': stat.S_IFDIR | 0o755,
                'st_nlink': 2,
                'st_size': 0,
                'st_uid': self.uid
            }

        metadata = self.pd.get_metadata(path)

        if metadata is None:
            return None

        return {
            'st_atime': now,
            'st_ctime': metadata.get('created') or now,
            'st_gid': self.gid,
            'st_mode': stat.S_IFREG | 0o644,
            'st_mtime': metadata.get('modified') or now,
            'st_nlink': 1,
            'st_size': metadata.get('size'),
            'st_uid': self.uid
        }

    def listdir(self):
        return self.pd.list_files_names()

    def open(self, path):
        fh_id = self.next_fh
        self.next_fh += 1
        self.fh[fh_id] = self.pd.open(path)

        return fh_id

    def read(self, fh, path, length, offset):
        return self.pd.read(self.fh[fh], path, length, offset)

    def unlink(self, path):
        return self.pd.delete(path)

    def create(self, path):
        fh_id = self.next_fh
        self.next_fh += 1
        
        ret = self.pd.put("".encode(), path, True)

        if isinstance(ret, int):
            self.fh[fh_id] = ret 
        else:
            self.fh[fh_id] = io.BytesIO()

        if ret is False:
            return False

        return fh_id

    def write(self, path, buf, offset, fh):
        if fh not in self.fh:
            return False

        self.pd.write(path, buf, offset, self.fh[fh])

        return len(buf)

    def rename(self, old, new):
        ret = self.pd.move(old, new)
        return ret
 