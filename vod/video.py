#!/usr/bin/env python

import io
import os
import re
import sys
import time
import select
import subprocess

class VideoDownloader():
    def __init__(self, target_path='~/Downloads', avconv_path='/usr/bin/avconv', verbose=False):
        self.target_path = target_path
        self.avconv_path = avconv_path
        self.verbose = verbose

    def __enter__(self):
        if not os.path.isdir(os.path.expanduser(self.target_path)):
            raise Exception("Can't download and convert: target directory '{}' does not exists".format(target_path))
        return self

    def __exit__(self, *args):
        pass

    def save(self, dest_file, video_url, callback=lambda p, t, d, s: print(p, t, d, s)):
        raise NotImplementedError


class AVConvDownloader(VideoDownloader):
    avconv_args = ['-y', '-vcodec', 'copy', '-acodec', 'copy']

    # Duration: 00:44:47.95, start: 0.100667, bitrate: 0 kb/s\n
    duration_r = re.compile(r'.*Duration: (\d\d):(\d\d):(\d\d.\d\d), .*')
    # frame=59282 fps=939 q=-1.0 size=  244134kB time=2371.24 bitrate= 843.4kbits/s
    processd_r = re.compile(r'.* time=(\d+.\d\d) .*')
    # already exists. Overwrite ? [y/N]
    overwrite_r = re.compile(r".*File '([^']+)' already exists.*")
    # No such file or directory
    notfound_r = re.compile(r".*No such file or directory")
    error_r = re.compile(r".*error.*")

    def save(self, dest_file, video_url, callback):
        dest_file = os.path.join(os.path.expanduser(self.target_path), dest_file)
        def output_parser(output, env={}):
            if self.verbose:
                print(output, file=sys.stderr, end="")
                return
            duration_m = self.duration_r.match(output)
            if duration_m:
                h,m,s = duration_m.groups()
                env['duration'] = int(h)*3600 + int(m)*60 + float(s)
                env['start'] = time.time()
            elif 'duration' in env.keys():
                processd_m = self.processd_r.match(output)
                if processd_m:
                    pos = float(processd_m.groups()[0])
                    spt = int(time.time()-env['start'])
                    callback(pos, env['duration'], spt, env['start'])
                else:
                    overwrite_m = self.overwrite_r.match(output)
                    if overwrite_m:
                        path = overwrite_m.groups()[0]
                        raise Exception('Output file "{}" already exists in target directory.'.format(path))
                    else:
                        if self.error_r.match(output):
                            raise Exception("Can't write to file '{}'.".format(dest_file))
            else:
                if self.error_r.match(output):
                    raise Exception('Impossible to download: {}.'.format(output))
        p = subprocess.Popen([self.avconv_path, '-i', video_url] + self.avconv_args + [dest_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        out = io.TextIOWrapper(p.stdout)
        err = io.TextIOWrapper(p.stderr)
        while p.poll() == None:
            ret = select.select([out.fileno(), err.fileno()], [], [])
            for fd in ret[0]:
                if fd == out.fileno():
                    output_parser(out.readline())
                if fd == err.fileno():
                    output_parser(err.readline())
        for line in out.read().split('\n'):
            output_parser(line)
        for line in err.read().split('\n'):
            output_parser(line)
        return dest_file


