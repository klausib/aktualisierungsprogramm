@echo off
call "d:\osge4w\bin\o4w_env.bat"
@echo off
path %OSGEO4W_ROOT%\apps\qgis\bin;%PATH%
d:
cd d:\aktualisierungsprogramm\
d:\osge4w\bin\python.exe aktualisierung_main.py