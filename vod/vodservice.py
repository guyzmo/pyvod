#!/usr/bin/env python

import sys
import requests
import http.cookiejar

from .video import VideoDownloader

class OnlineService():
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:19.0) Gecko/20100101 Firefox/19.0'}
    cookiejar = http.cookiejar.CookieJar()

    def get(self, *args):
        return requests.get(*args, headers=self.headers, cookies=self.cookiejar)


class VodService(OnlineService):
    def __init__(self, out=None, verbose=False):
        self.out = out
        self.verbose = verbose
        print(_('Init…'), end="\r", file=self.out)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        pass

    def get_categories(self):
        raise NotImplementedError

    def get_channels(self):
        raise NotImplementedError

    def list(self, query=None, category=None, channel=None, limit=0, sort=None, page=0):
        raise NotImplementedError

class VodServiceShow(OnlineService):

    def __init__(self, data, out=None, downloader=VideoDownloader):
        self.data = data
        self.data['_id_'] = self.id
        self.data['_title_'] = self.title
        self.data['_image_'] = self.image
        self.out = out
        self.downloader = downloader

    @property
    def id(self):
        raise NotImplementedError

    @property
    def title(self):
        raise NotImplementedError

    @property
    def image(self):
        raise NotImplementedError

    def keys(self):
        return list(filter(lambda x: not x.startswith('_') and not x.endswith('_'), self.data.keys()))

    def items(self):
        return self.data.items()

    def __getitem__(self, it):
        return self.data[it]

    def __setitem__(self, it, val):
        raise Exception("Movie data are immutables")

    def print(self, out=sys.stdout):
        print(_("Summary of the show '{}'").format(self.title))
        nb_short=0
        for k, v, kind in self.get_summary():
            if kind is "short":
                nb_short += 1
                if nb_short == 2:
                    print("")
                    nb_short=0
            else:
                print("")

            print("{:>12}: {:<30}".format(k,v), end="")
        else:
            print("")

        print("{:>12}: ".format(_("Crew")))
        for f, p, n in self.get_crew():
            print("{:>20}: {} {}".format(f, p, n))

        print("{:>12}: ".format(_("Synopsis")))
        for line in self.get_synopsis():
            print(line)

    def get_summary(self):
        raise NotImplementedError

    def get_crew(self):
        raise NotImplementedError

    def get_synopsis(self):
        raise NotImplementedError
