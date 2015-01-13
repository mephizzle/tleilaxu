#!/usr/bin/python

import SimpleHTTPServer
import SocketServer

import atexit
import os
import shutil
import sys
import tarfile


class TleilaxError(Exception):
    pass


class BuildSetup(object):
    def __init__(self):
        try:
            self.path = sys.argv[1]
        except IndexError:
            self.path = os.getcwd()
        self.projectname = os.path.basename(self.path.strip(os.path.sep))
        os.chdir(self.path)
        self.conf = self.parse_config()
        self.setup_build_dir()

    def parse_config(self):
        fn = os.path.join(self.path, '.tleilax')
        if not os.path.exists(fn):
            raise TleilaxError(
                '{0} not configured for deployment, add .tleilax file'
            )
        with open(fn) as inf:
            return [f.strip() for f in inf.readlines()]

    def setup_build_dir(self):
        self.builddir_path = os.path.join(self.path, '.tl_build')
        os.makedirs(self.builddir_path)

        _tfn = os.path.join(self.builddir_path, 'tl_package.tar')

        with tarfile.TarFile(_tfn, 'w') as build_package:
            for line in self.conf:
                build_package.add(
                    os.path.join(self.path, line),
                    arcname=line
                )

        _pfn = os.path.join(self.builddir_path, 'name.conf')
        with open(_pfn, 'w') as _pf:
            _pf.write(self.projectname)

    def cleanup(self):
        shutil.rmtree(self.builddir_path)


if __name__ == '__main__':
    bs = BuildSetup()
    atexit.register(bs.cleanup)

    PORT = 8080
    Handler = SimpleHTTPServer.SimpleHTTPRequestHandler
    httpd = SocketServer.TCPServer(('', PORT), Handler)
    print 'webserver running'
    httpd.serve_forever()
