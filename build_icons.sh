#!/bin/bash

pushd viur_admin/icons
cp ../cacert.pem .
cp ../icons.qrc .
cp ../app.css .
pyrcc5 icons.qrc -o ../ui/icons_rc.py
rm icons.qrc app.css cacert.pem
popd
