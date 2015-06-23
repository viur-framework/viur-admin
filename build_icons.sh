#!/bin/sh

pushd viur_admin/icons
cp ../icons.qrc .
pyrcc5 icons.qrc -o ../ui/icons_rc.py
popd
