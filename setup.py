from cx_Freeze import setup, Executable
import sys, os.path

#Try reading the .git version
version = "unknown"
try:
	gitHead = open(".git/FETCH_HEAD", "r").read()
	for line in gitHead.splitlines():
		line = line.replace("\t", " ")
		if "branch 'master'" in line:
			version = line.split(" ")[0]
except:
	pass

extraArgs = {}
if sys.platform.startswith("win32"):
    extraArgs.update( {"base": "Win32GUI"} )

fwadmin = Executable(
        script="admin.py", icon=os.path.join( "icons","viur_win.ico" ), **extraArgs )
fwupdater = Executable(
        script="updater.py", icon=os.path.join( "icons","viur_updater_win.ico" ), **extraArgs )
buildList = [fwadmin, fwupdater]
if sys.platform.startswith("win32"):
    fwadmindbg = Executable( script="admin.py", icon=os.path.join( "icons","viur_win.ico" ), targetName="admindbg.exe" )
    buildList.append( fwadmindbg )

opts = {"build_exe": {"include_files": ["app.css", "cacert.pem", "license.txt", "mime.types","plugins", "icons","locales"]} }
    
setup( name = "ViUR-Admin",
       version = version,
       description = "ViUR Administations-Tool",
       executables = buildList, 
       )

