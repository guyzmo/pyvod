#!/bin/bash

PWD=$(dirname $0)


if [ $(uname -s) == "Darwin" ]; then
    msgfmt=/usr/local/Cellar/python3/3.3.3/Frameworks/Python.framework/Versions/3.3/share/doc/python3.3/examples/Tools/i18n/msgfmt.py
else
    msgfmt=/usr/bin/msgfmt
fi

for lang in ${PWD}/*/; do
     ${msgfmt} -o ${PWD}/${lang}/LC_MESSAGES/pyvod.mo ${PWD}/${lang}/LC_MESSAGES/pyvod.po
done
