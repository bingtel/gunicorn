# -*- coding: utf-8 -
#
# This file is part of gunicorn released under the MIT license.
# See the NOTICE for more information.

import os
import platform
import tempfile

from gunicorn import util

PLATFORM = platform.system()
IS_CYGWIN = PLATFORM.startswith('CYGWIN')


class WorkerTmp(object):

    def __init__(self, cfg):
        old_umask = os.umask(cfg.umask)
        fdir = cfg.worker_tmp_dir
        if fdir and not os.path.isdir(fdir):
            raise RuntimeError("%s doesn't exist. Can't create workertmp." % fdir)
        # 如何你的应用程序需要一个临时文件来存储数据
        # 但不需要同其他程序共享，那么用TemporaryFile函数创建临时文件是最好的选择。
        # 其他的应用程序是无法找到或打开这个文件的，
        # 因为它并没有引用文件系统表。用这个函数创建的临时文件，关闭后会自动删除。
        fd, name = tempfile.mkstemp(prefix="wgunicorn-", dir=fdir)

        # allows the process to write to the file
        util.chown(name, cfg.uid, cfg.gid)
        os.umask(old_umask)

        # unlink the file so we don't leak tempory files
        try:
            if not IS_CYGWIN:
                util.unlink(name)
            self._tmp = os.fdopen(fd, 'w+b', 1)
        except:
            os.close(fd)
            raise

        self.spinner = 0

    def notify(self):
        self.spinner = (self.spinner + 1) % 2
        os.fchmod(self._tmp.fileno(), self.spinner)

    def last_update(self):
        # os.fstat() 方法用于返回文件描述符fd的状态
        # 文件状态信息的修改时间（不是文件内容的修改时间）
        return os.fstat(self._tmp.fileno()).st_ctime

    def fileno(self):
        return self._tmp.fileno()

    def close(self):
        return self._tmp.close()
