#!/usr/bin/python3
# ------------------------------------------------------------------------------

from __future__ import with_statement

import os
import errno
import stat

from datetime import datetime
from time import time, mktime
from fuse import FuseOSError, Operations


class Passthrough(Operations):
    def __init__(self, dbx):
        self.dbx = dbx
        self.uid = os.getuid()
        self.gid = os.getgid()

    # Helpers
    # =======

    # def _full_path(self, partial):
    #    if partial.startswith("/"):
    #        partial = partial[1:]
    #    path = os.path.join(self.root, partial)
    #    return path

    # Filesystem methods
    # ==================

    # def access(self, path, mode):
    #    pass

    # def chmod(self, path, mode):
    #    pass

    # def chown(self, path, uid, gid):
    #    pass

    def getattr(self, path, fh=None):
        now = int(time())

        metadata = self.dbx.get_metadata(path)
        if not metadata:
            raise FuseOSError(errno.ENOENT)

        if 'client_modified' in metadata.keys():
            to_str = str(metadata.get('client_modified'))
            modified = mktime(datetime.strptime(to_str, '%Y-%m-%d %H:%M:%S').timetuple())
        else:
            modified = int(now)

        if 'entries' in metadata:
            return {
                'st_atime': now,
                'st_ctime': modified,
                'st_gid': self.gid,
                'st_mode': stat.S_IFDIR,
                'st_mtime': modified,
                'st_nlink': 1,
                'st_size': 0,
                'st_uid': self.uid
            }
        else:
            return {
                'st_atime': now,
                'st_ctime': modified,
                'st_gid': self.gid,
                'st_mode': stat.S_IFREG,
                'st_mtime': modified,
                'st_nlink': 1,
                'st_size': metadata.get('size'),
                'st_uid': self.uid
            }

    def readdir(self, path, fh):
        dirents = ['.', '..']

        metadata = self.dbx.get_metadata(path)

        for file in metadata.get('entries'):
            dirents.append(os.path.basename(file.get('path')))

        for r in dirents:
            yield r

    # def readlink(self, path):
    #     pathname = os.readlink(self._full_path(path))
    #     if pathname.startswith("/"):
    #         # Path name is absolute, sanitize it.
    #         return os.path.relpath(pathname, self.root)
    #     else:
    #         return pathname

    # def mknod(self, path, mode, dev):
    #     return os.mknod(self._full_path(path), mode, dev)

    # def rmdir(self, path):
    #     full_path = self._full_path(path)
    #     return os.rmdir(full_path)

    #  def mkdir(self, path, mode):
    #     return os.mkdir(self._full_path(path), mode)

    # def statfs(self, path):
    #
    #    return {
    #        'f_bavail':,
    #        'f_bfree',
    #        'f_blocks',
    #        'f_bsize',
    #        'f_favail',
    #        'f_ffree',
    #        'f_files',
    #        'f_flag',
    #        'f_frsize',
    #        'f_namemax'))

    # def unlink(self, path):
    #     return os.unlink(self._full_path(path))

    # def symlink(self, name, target):
    #     return os.symlink(name, self._full_path(target))

    def rename(self, old, new):
        try:
            self.dbx.move(old, new)
        except Exception:
            raise FuseOSError(errno.EIO)

    # def link(self, target, name):
    #     return os.link(self._full_path(target), self._full_path(name))

    # def utimens(self, path, times=None):
    #    return os.utime(self._full_path(path), times)

    # File methods
    # ============

    # def open(self, path, flags):
    #    return 0

    # def create(self, path, mode, fi=None):
    #    full_path = self._full_path(path)
    #    return os.open(full_path, os.O_WRONLY | os.O_CREAT, mode)

    # def read(self, path, length, offset, fh):
    #    return length

    # def write(self, path, buf, offset, fh):
    #    self.dbx.put(path)
    #    return len(buf)

    # def truncate(self, path, length, fh=None):
    #    full_path = self._full_path(path)
    #    with open(full_path, 'r+') as f:
    #        f.truncate(length)

    # def flush(self, path, fh):
    #    return os.fsync(fh)

    # def release(self, path, fh):
    #    return

    # def fsync(self, path, fdatasync, fh):
    #    return self.flush(path, fh)
