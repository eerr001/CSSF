set workdir=%cd%
cd /d "D:\Portable\Portable Python 2.7.6.1\App\"

python.exe Lib\site-packages\PyQt4\uic\pyuic.py -o "%workdir%\CSSF_UI.py" "%workdir%\CSSF_UI.ui"
pause