#!/usr/bin/python3
# ------------------------------------------------------------------------------

from __future__ import with_statement

import errno
import os

from fuse import FuseOSError, Operations


class ProviderFS(Operations):
    def __init__(self, provider):
        self.provider = provider

    def getattr(self, path, fh=None):
        result = self.provider.lstat(path)
        if result is None:
            raise FuseOSError(errno.ENOENT)

        return result

    def readdir(self, path, fh):
        return ['.', '..'] + list(self.provider.listdir())

    def unlink(self, path):
        result = self.provider.unlink(path)
        if result is False:
            raise FuseOSError(errno.ENOENT)
        return result

    def rename(self, old, new):
        ret = self.provider.rename(old, new)
        if ret is False:
            raise FuseOSError(errno.EPERM)

    def open(self, path, flags):
        if flags & os.O_APPEND:
            raise FuseOSError(errno.EOPNOTSUPP)
        return self.provider.open(path)

    def create(self, path, mode, fi=None):

        fh = self.provider.create(path)
        if fh is False:
            return FuseOSError(errno.EPERM)

        return fh

    def read(self, path, length, offset, fh):
        bytes_read = self.provider.read(fh, path, length, offset)
        if bytes_read is None:
            raise FuseOSError(errno.EROFS)
        return bytes_read

    def write(self, path, buf, offset, fh):
        ret = self.provider.write(path, buf, offset, fh)
        if ret is False:
            raise FuseOSError(errno.EIO)

        return ret

    # def release(self, path, fh):
