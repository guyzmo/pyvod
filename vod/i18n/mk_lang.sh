#!/bin/sh

POT=pyvod.cplus.po

if [ $(uname -s) == "Darwin" ]; then
    gettext="/usr/local/Cellar/python3/3.3.3/Frameworks/Python.framework/Versions/3.3/share/doc/python3.3/examples/Tools/i18n/pygettext.py"
else
    gettext="/usr/bin/gettext"
fi

${gettext} -D -o ${POT} ../../**.py

for lang in ${PWD}/*/; do
    cp ${POT} ${lang}/LC_MESSAGES/
done

rm -f ${POT}
