#!/usr/bin/python3
# ------------------------------------------------------------------------------

from __future__ import with_statement

import os
import errno
import stat

from datetime import datetime
from time import time, mktime
from fuse import FuseOSError, Operations
from errno import *

class Passthrough(Operations):
    def __init__(self, dbx):
        self.dbx = dbx
        self.uid = os.getuid()
        self.gid = os.getgid()
        self.openfh = {}
        self.runfh = {}
        self.write_cache = 4194304 # Bytes
  



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

      # Change attributes of item. Dummy until now.
    # def chmod(self, path, mode):
    #     print("CHMOD")
    #     #if debug == True: appLog('debug', 'Called: chmod() - Path: ' + path + " Mode: " + str(mode))
    #     if not self.dbx.get_metadata(path):
    #       raise FuseOSError(ENOENT)
    #     return 0o666

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
                'st_mode': stat.S_IFDIR | 0o755,
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
                'st_mode': stat.S_IFREG | 0o644,
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
    #     return os.mknod(path, mode, dev)

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


      # Remove a file.
    def unlink(self, path):
        self.dbx.delete(path)
        return 0

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
    #     print("UTIMENS")
        #print(os.utime(path, times))

    # File methods
    # ============

    # def open(self, path, flags):
    #    return 0

    def open(self, path, flags):
        # Validate flags.
        if flags & os.O_APPEND:
          raise FuseOSError(EOPNOTSUPP)

        fh = self.get_fh('r')
        return fh


    def create(self, path, mode):

        fh = self.get_fh('w')
        now = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')

        self.dbx.put("".encode(),path,True)

        return fh



    # Read data from a remote filehandle.
    def read(self, path, length, offset, fh):

        # Wait while this function is not threadable.
        while self.openfh[fh]['lock'] == True:
          pass

        self.runfh[fh] = True

        if fh in self.openfh:
            if self.openfh[fh]['f'] == False:
                try:
                    self.openfh[fh]['f'] = self.dbx.file_handle(path, offset)
                except Exception:
                    raise FuseOSError(EIO)
            else:
                if self.openfh[fh]['eoffset'] != offset:
                    self.openfh[fh]['f'] = self.dbx.file_handle(path, offset)
                pass

        # Read from FH.
        rbytes = self.openfh[fh]['f'].read(length)

        self.openfh[fh]['lock'] = False
        self.runfh[fh] = False
        self.openfh[fh]['eoffset'] = offset + len(rbytes)
        return rbytes



    def write(self, path, buf, offset, fh):
        try:
            # Check for the beginning of the file.
            if fh in self.openfh:
                if self.openfh[fh]['f'] == False:
                    # Check if the write request exceeds the maximum buffer size.
                    if len(buf) >= self.write_cache or len(buf) < 4096:
                        result = self.dbx.chunked_upload(buf, "", 0)
                        self.openfh[fh]['f'] = {'upload_id':result['upload_id'], 'offset':result['offset'], 'buf':''}
                    else:
                        self.openfh[fh]['f'] = {'upload_id':'', 'offset':0, 'buf':buf}
                    return len(buf)
                else:
                    if len(buf)+len(self.openfh[fh]['f']['buf']) >= self.write_cache or len(buf) < 4096:
                        result = self.dbx.chunked_upload(self.openfh[fh]['f']['buf']+buf, self.openfh[fh]['f']['upload_id'], self.openfh[fh]['f']['offset'])
                        self.openfh[fh]['f'] = {'upload_id':result['upload_id'], 'offset':result['offset'], 'buf':''}
                    else:
                        self.openfh[fh]['f'].update({'buf':self.openfh[fh]['f']['buf']+buf})
                    return len(buf)
            else:
                raise FuseOSError(EIO)
        except Exception:
            raise FuseOSError(EIO)

    # def truncate(self, path, length, fh=None):
    #    full_path = self._full_path(path)
    #    with open(full_path, 'r+') as f:
    #        f.truncate(length)

    # def flush(self, path, fh):
    #     print("=======FLUSH=======")
    #     return 0

      # Flush filesystem cache. Always true in this case.
    # def fsync(self, path, fdatasync, fh):
    #   path = path.encode('utf-8')



      # # Release (close) a filehandle.
    def release(self, path, fh):
        # Check to finish Dropbox upload.
        if type(self.openfh[fh]['f']) is dict and 'upload_id' in self.openfh[fh]['f'] and self.openfh[fh]['f']['upload_id'] != "":
            # Flush still existing data in buffer.
            if self.openfh[fh]['f']['buf'] != "":
                result = self.dbx.chunked_upload(self.openfh[fh]['f']['buf'], self.openfh[fh]['f']['upload_id'], self.openfh[fh]['f']['offset'])
            
            result = self.dbx.commit_chunked_upload(path, self.openfh[fh]['f']['upload_id'], self.openfh[fh]['f']['offset'], True)

        self.release_fh(fh)
        return 0



    def release_fh(self, fh):
        if fh in self.openfh:
          self.openfh.pop(fh)
          self.runfh.pop(fh)
        else:
          return False

      # Get a valid and unique filehandle.
    def get_fh(self, mode):
        for i in range(1,8193):
          if i not in self.openfh:
            self.openfh[i] = {'mode' : mode, 'f' : False, 'lock' : False, 'eoffset': 0}
            self.runfh[i] = False
            return i
        return False
