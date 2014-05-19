#!/usr/bin/env python

try:
    from PyQt5 import QtCore
    from PyQt5 import QtWidgets, QtWebKitWidgets
except ImportError:
    from PyQtX import QtCore
    from PyQtX import QtWidgets, QtWebKitWidgets

import re
import os
import sys
import time
import types
from lxml.html import builder as hb
from lxml.html import tostring as html_dumps

TOPBAR_JS="""\
var channels = document.getElementsByClassName("channel");
for (var i=0;i<channels.length; ++i) {
    console.log(channels[i]);
    channels[i].getElementsByTagName('a')[0].onclick = function() {
        qvodservice.select_channel(this.innerHTML);
        return false;
    }
}
var categories = document.getElementsByClassName("category");
for (var i=0;i<categories.length; ++i) {
    categories[i].getElementsByTagName('a')[0].onclick = function() {
        qvodservice.select_category(this.innerHTML);
        return false;
    }
}
"""

SHOWS_JS="""\
var shows = document.getElementsByClassName("show");
for (var i=0;i<shows.length; ++i) {
    shows[i].onclick = function() {
        qvodservice.select_show(this.getAttribute('id'));
        return false;
    }
}
"""

SHOW_JS="""\
document.getElementById("back").onclick = function() {
    qvodservice.goto_list();
    return false;
}
"""

class QVideoView(QtWebKitWidgets.QWebView):
    css_head = hb.LINK(rel="stylesheet", href='file://{}'.format(os.path.join(os.path.dirname(__file__),"resources","pyvodservice.css")), type="text/css")
    def __init__(self, *args, Search, verbose=False):
        super(QVideoView, self).__init__(*args)
        self.page().mainFrame().javaScriptWindowObjectCleared.connect(self.handle_slots)
        self.topbar_channels = []
        self.topbar_categories = []
        self.category_selected = "all"
        self.channel_selected = "all"
        self.verbose = verbose
        self.vodservice = Search(verbose=verbose)

    def handle_slots(self):
        self.page().mainFrame().addToJavaScriptWindowObject("qvodservice", self);

    def setup_topbar(self):
        with self.vodservice as s:
            try:
                cat_l = [hb.LI(hb.CLASS("category") if c != self.category_selected else hb.CLASS("category selected"),
                                hb.A(c, href="javascript:void(0)")) for c in s.get_categories()]
                chn_l = [hb.LI(hb.CLASS("channel") if c != self.channel_selected else hb.CLASS("channel selected"),
                                hb.A(c, href="javascript:void(0)")) for c in s.get_channels()]
                self.topbar_channels = hb.UL(*(chn_l), id='channels')
                self.topbar_categories = hb.UL(*(cat_l), id='categories')
            except Exception as err:
                if self.verbose:
                    import traceback
                    traceback.print_exc()

    def build_show_list(self, **args):
        self.setup_topbar()
        with self.vodservice as s:
            try:
                shw_l = [hb.DIV(hb.CLASS("image"),
                                hb.A(hb.CLASS("show"),
                                     hb.IMG(src=md['_image_'],
                                            alt=md['_title_']),
                                     hb.DIV(hb.CLASS('caption'),
                                            hb.P(hb.CLASS('caption_content'),
                                                 md['_title_'])),
                                     id=md['_id_'], href="javascript:void(0)")) for md in s.list(**args)]
            except Exception as err:
                shw_l = [str(err)]
                if self.verbose:
                    import traceback
                    traceback.print_exc()

        doc = hb.HTML(hb.HEAD(self.css_head),
                      hb.BODY(hb.DIV(hb.CLASS('header'),
                                     self.topbar_channels,
                                     self.topbar_categories),
                              hb.DIV(hb.CLASS('content'),
                                     hb.UL(*(shw_l)))
                              )
                      )
        self.setHtml(html_dumps(doc).decode('utf8'))
        self.settings().setUserStyleSheetUrl(QtCore.QUrl(os.path.join(os.path.dirname(__file__),"resources","qvodservice.css")))
        self.page().mainFrame().evaluateJavaScript(TOPBAR_JS)
        self.page().mainFrame().evaluateJavaScript(SHOWS_JS)

    def build_show_data(self, i):
        with self.vodservice as s:
            m = s.get_show(i)
            try:
                show_md = [hb.H1(m.title)]
                for key, value, kind in m.get_summary():
                    print(key, value)
                    if kind == 'link':
                        show_md.append(hb.DIV(hb.SPAN(hb.CLASS('md_key'),
                                                      hb.A(key,
                                                           onclick='qvodservice.open_url({})'.format(value),
                                                           href="javascript:void(0)"))))
                    elif kind == 'image':
                           show_md.append(hb.DIV(hb.SPAN(hb.CLASS('md_key'), key, ':'),
                                                 hb.IMG(hb.CLASS('md_val'), src=value)))
                    else:
                        show_md.append(hb.DIV(hb.SPAN(hb.CLASS('md_key'), key, ':'),
                                              hb.SPAN(hb.CLASS('md_val'), value)))



                show_md.append(hb.DIV(hb.SPAN(hb.CLASS('md_key'), _('Crew'), ':')     ,
                    hb.UL(hb.CLASS('crew_list'),
                                *([hb.LI(hb.UL(hb.SPAN(hb.CLASS('md_key'), f, ':'),
                                                hb.SPAN(hb.CLASS('md_val'), ' ', p, ' ', n))) for f, p, n in m.get_crew()])
                            )
                    ))
                show_md.append(hb.P(hb.CLASS('synopsis'), "\n".join(m.get_synopsis())))
            except Exception as err:
                show_md = [str(err)]
                if self.verbose:
                    import traceback
                    traceback.print_exc()

        doc = hb.HTML(hb.HEAD(self.css_head),
                      hb.BODY(hb.DIV(hb.A('×', href="javascript:void(0)"), id='back'),
                              hb.DIV(hb.CLASS('header')),
                              hb.DIV(hb.CLASS('content'),
                                     hb.UL(*(show_md)))
                              )
                      )

        self.setHtml(html_dumps(doc).decode('utf8'))
        self.settings().setUserStyleSheetUrl(QtCore.QUrl(os.path.join(os.path.dirname(__file__),"resources","qvodservice.css")))
        self.page().mainFrame().evaluateJavaScript(TOPBAR_JS)
        self.page().mainFrame().evaluateJavaScript(SHOW_JS)

    @QtCore.pyqtSlot("QString")
    def open_url(self, url):
        print("open_url({})".format(url))
        QtCore.QDesktopServices.openUrl(url)

    @QtCore.pyqtSlot()
    def goto_list(self):
        if self.parent().in_download:
            return
        self.parent().url_txt.setText('')
        self.parent().start_btn.setVisible(False)
        self.parent().pbar.setVisible(False)
        self.parent().eta.setVisible(False)
        self.build_show_list(channel=self.channel_selected,
                             category=self.category_selected,
                             limit=100, sort="alpha")

    @QtCore.pyqtSlot("QString")
    def select_show(self, i):
        self.parent().url_txt.setText(i)
        self.parent().start_btn.setVisible(True)
        self.parent().pbar.setVisible(True)
        self.parent().eta.setVisible(True)
        self.build_show_data(i)

    @QtCore.pyqtSlot("QString")
    def select_category(self, i):
        self.category_selected = i
        self.build_show_list(channel=self.channel_selected,
                             category=self.category_selected,
                             limit=100, sort="alpha")

    @QtCore.pyqtSlot("QString")
    def select_channel(self, i):
        self.channel_selected = i
        self.build_show_list(channel=self.channel_selected,
                             category=self.category_selected,
                             limit=100, sort="alpha")

class QVideoService(QtWidgets.QWidget):

    update_progress_bar = QtCore.pyqtSignal(int)
    update_eta_text = QtCore.pyqtSignal(str)

    def __init__(self, args, Search):
        super(QVideoService, self).__init__()

        self.defaults = args
        self.in_download = False

        # row #0
        vbox = QtWidgets.QVBoxLayout()
        vbox.addWidget(QtWidgets.QLabel(_('VOD Service Movie Downloader')))
        # row #1
        self.web_view = QVideoView(self, Search=Search, verbose=args['--verbose'])
        self.web_view.build_show_list(limit=100, sort="alpha")
        vbox.addWidget(self.web_view)
        # row #2
        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(QtWidgets.QLabel(_('Search TV show')))
        self.url_txt = QtWidgets.QLineEdit()
        self.url_txt.setText(args['<id>'])
        self.url_txt.editingFinished.connect(self.on_update_search)
        hbox.addWidget(self.url_txt)
        vbox.addLayout(hbox)
        # row #3
        hbox = QtWidgets.QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(QtWidgets.QLabel(_('Directory where to download')))
        self.path_txt = QtWidgets.QLineEdit()
        self.path_txt.setText(args['--target'])
        hbox.addWidget(self.path_txt)
        vbox.addLayout(hbox)
        # row #4
        hbox = QtWidgets.QHBoxLayout()
        self.eta = QtWidgets.QLabel('')
        self.update_eta_text.connect(self.eta.setText)
        hbox.addWidget(self.eta)
        self.pbar = QtWidgets.QProgressBar()
        self.pbar.setMinimum(0)
        self.pbar.setMaximum(100)
        self.pbar.setTextVisible(True)
        self.update_progress_bar.connect(self.pbar.setValue)
        hbox.addWidget(self.pbar, stretch=1)
        vbox.addLayout(hbox)
        # row #5
        self.start_btn = QtWidgets.QPushButton(_('Start Download!'))
        self.start_btn.clicked.connect(self.on_click_start)
        vbox.addWidget(self.start_btn)
        vbox.addStretch(1)

        if args['<id>']:
            self.eta.setVisible(True)
            self.pbar.setVisible(True)
            self.start_btn.setVisible(True)
        else:
            self.start_btn.setVisible(False)
            self.pbar.setVisible(False)
            self.eta.setVisible(False)

        self.setLayout(vbox)

        self.setWindowTitle(_('VOD Service Movie loader'))
        self.show()

    re_match_id = re.compile(r'^\d+$')

    @QtCore.pyqtSlot()
    def on_update_search(self):
        if self.url_txt.text().lstrip().startswith('http://'):
            self.web_view.select_show(self.url_txt.text())
        elif self.re_match_id.match(self.url_txt.text().lstrip()):
            self.web_view.select_show(self.url_txt.text())
        else:
            self.web_view.build_show_list(channel=self.web_view.channel_selected,
                                          category=self.web_view.category_selected,
                                          query=self.url_txt.text(),
                                          limit=100, sort="relevance")

    @QtCore.pyqtSlot()
    def on_click_start(self):
        def update_progress(position, total, spent, start):
            eta = int((time.time() - start)*total/position)
            adv = position/total
            if self.defaults['--verbose']:
                print("{: >10}/{: <10} : {: >3}s/{: <3}s".format(position, total, spent, eta), end='\r')
            self.update_eta_text.emit("ETA {}s/{}s".format(spent, eta))
            self.update_progress_bar.emit(adv*100)

        def dl(that):
            self.start_btn.setDisabled(True)
            self.in_download = True
            movie.save(callback=update_progress, avconv_path=self.defaults['--avconv'], verbose=self.defaults['--verbose'])
            self.update_eta_text.emit("ETA -/-")
            self.update_progress_bar.emit(0)
            self.start_btn.setEnabled(True)
            self.in_download = False

        with self.web_view.vodservice as s:
            movie = s.get_show(i)
            t = QtCore.QThread(self)
            # Monkey patching of QThread to change the run function!
            t.run = types.MethodType(dl, t)
            t.start()

def main(args, Search=None):
    app = QtWidgets.QApplication(sys.argv)
    qpluzz = QVideoService(args, Search)
    sys.exit(app.exec_())

