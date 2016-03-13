from distutils.core import setup
import py2exe
import sys


# If run without args, build executables, in quiet mode.
if len(sys.argv) == 1:
    sys.argv.append("py2exe")
    sys.argv.append("-q")
setup(zipfile=None,
      windows=[{"script":"CSSF_main.py", "icon_resources":[(1, "LRF3032.ico")]}],
      options={  "py2exe":{"compressed":2, "bundle_files":1,
                 "includes":["sip", "PyQt4.QtGui", "PyQt4.QtCore", "serial"],
                 "dll_excludes": ["msvcm90.dll", "msvcp90.dll", "msvcr90.dll"],}},

     )
