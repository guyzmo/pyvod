#!/usr/bin/env python

import sys
import time
import textwrap

from vod.vodservice import VodService

def get_term_size():
    import os
    env = os.environ
    def ioctl_GWINSZ(fd):
        try:
            import fcntl, termios, struct, os
            cr = struct.unpack('hh', fcntl.ioctl(fd, termios.TIOCGWINSZ,
        '1234'))
        except:
            return
        return cr
    cr = ioctl_GWINSZ(0) or ioctl_GWINSZ(1) or ioctl_GWINSZ(2)
    if not cr:
        try:
            fd = os.open(os.ctermid(), os.O_RDONLY)
            cr = ioctl_GWINSZ(fd)
            os.close(fd)
        except:
            pass
    if not cr:
        cr = (env.get('LINES', 25), env.get('COLUMNS', 80))
    return int(cr[1]), int(cr[0])

def show_progress(position, total, spent, start):
    width = (get_term_size()[0]*0.6)
    adv = position/total
    eta = int((time.time() - start)*total/position)
    print((_('Download and convert')+': [{: <'+str(int(width))+'s}] {:0.0%} ETA: {}s/{}s').format('#'*int(width*adv), adv, spent, eta), end='\r')

def run(Search=VodService, doc=__doc__):
    from docopt import docopt
    try:
        args = docopt(doc)
        if args['gui']:
            try:
                import vod.ui.qt
                vod.ui.qt.main(args, Search)
            except ImportError:
                raise Exception(_("Couldn't load Qt libraries. Impossible to run the GUI, sorry."))
        elif args['fetch']:
                if not args['<id>']:
                    raise Exception(_('Missing URL!'))
                with Search(out=sys.stderr) as s:
                    m = s.get_show(args['<id>'])
                    print(_("Download and convert…"), end='\r', file=sys.stderr)
                    dest_file = m.save(args['--target'],
                                       callback=show_progress,
                                       avconv_path=args['--avconv'],
                                       verbose=args['--verbose'])
                    print(("{: <"+str(int(get_term_size()[0]))+"}").format("Download and convertion done: '{}' saved".format(dest_file)))
        elif args['get']:
            if not args['<id>']:
                raise Exception(_('Missing URL!'))
            with Search(out=sys.stderr) as s:
                m = s.get_show(args['<id>'])
                if len(args['<key>']) > 0 and args['<key>'][0] in m.keys():
                    key = " » ".join(args['<key>'])
                    print((_("Showing {}:")+"               ").format(key))
                    v = m[args['<key>'][0]]
                    try:
                        # parse list of keys to get into nested dicts
                        for k in args['<key>'][1:]:
                            v = v[k]
                        else:
                            if isinstance(v, str) and len(v) > 70 and not v.startswith('http:'):
                                for line in textwrap.wrap(v):
                                    print("  {}".format(line))
                            elif isinstance(v, dict):
                                print(_("List of all subkeys for key '{}', show: '{}'").format(args['<key>'][-1], m.title))
                                for k in v.keys():
                                    print("  {}".format(k))
                            else:
                                print("  {}".format(str(v)))
                    except KeyError:
                        raise "key {} not found.".format(args['<key>'][-1])
                else:
                    print(_("List of all keys for the show: '{}'").format(m.title))
                    for k in m.keys():
                        print("  {}".format(k))
        elif args['show']:
            with Search(out=sys.stderr) as s:
                s.get_show(args['<id>']).print()
        elif args['list'] or args['search']:
            with Search(out=sys.stderr) as s:
                if args['search']:
                    args['--sort'] = 'relevance'

                items = ('<query>', '<category>', '<channel>', '--limit', '--sort', '--page')
                list_args = dict(((k.strip('<>-'), args[k]) for k in filter(lambda x: x in items, args.keys())))

                if list_args['category'] == 'help' or list_args['channel'] == 'help' or (args['list'] and not list_args['category']):
                    print(_("Categories:"))
                    for cat in s.get_categories():
                        print("{:>20}".format(cat))

                    print("")
                    print(_("Channels:"))
                    for cat in s.get_channels():
                        print("{:>20}".format(cat))
                    return

                if list_args['category'] == 'all':
                    list_args['category'] = None

                if list_args['channel'] == 'all':
                    list_args['category'] = None

                if args['--image']:
                    for mm in s.list(**list_args):
                        print("{_id_:>12} -- {_title_:<40} {_image_}".format(**mm))
                else:
                    for mm in s.list(**list_args):
                        print("{_id_:>12} -- {_title_:<40}".format(**mm.data))

    except Exception as err:
        print("", file=sys.stderr)
        print(_("Error:"), err, file=sys.stderr)
        if (args['--verbose']):
            import traceback
            traceback.print_exc()
        sys.exit(2)


