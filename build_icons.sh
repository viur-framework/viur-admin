#!/bin/bash


pushd viur_admin
#cp -r app.css icons.qrc htmleditor resources icons
#pushd icons
# for now generate a missing file until we have updated the icons submodule
pyrcc5 icons.qrc -o ui/icons_rc.py
##cp ../ui/icons_rc.py .
##rm -r app.css icons.qrc htmleditor resources
##popd
#pushd ui
#for uiFile in *.ui; do pyuic5 "${uiFile}" -o "${uiFile%.ui}UI.py"; done
#find . -name '*UI.py' -exec sed -i 's/import icons_rc/import viur_admin.ui.icons_rc/g' {} \;
#popd
popd
