@echo off
cd /d %~dp0
call ..\RC_program\WinPython-32bit-3.5.3.1Zero\python-3.5.3\python.exe ..\RC_program\ratio_christi_filesyncer.py "stream"
