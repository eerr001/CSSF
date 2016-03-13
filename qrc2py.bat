set workdir=%cd%
cd /d "f:\Tools\Portable Python 2.7.6.1\App"

Lib\site-packages\PyQt4\pyrcc4.exe -o "%workdir%\resource_.py" "%workdir%\resource.qrc" 
pause