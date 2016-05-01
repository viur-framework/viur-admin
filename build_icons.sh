#!/bin/bash

pushd viur_admin
cp cacert.pem app.css html/mdedit.html html/mdedit_docs.md icons.qrc icons
pushd icons
pyrcc5 icons.qrc -o ../ui/icons_rc.py
rm cacert.pem app.css mdedit.html mdedit_docs.md icons.qrc
