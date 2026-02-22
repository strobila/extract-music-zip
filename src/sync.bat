@echo off
set SOURCE=d:\repos\extract-music-zip
set DEST=%USERPROFILE%\Downloads\music_zip

echo "Sync ? (y/n)"
set /p ANSWER=
if /i not "%ANSWER%"=="y" ( exit /b 0 )

copy /y "%SOURCE%\*.py" "%DEST%"
copy /y "%SOURCE%\transport_music_file.bat" "%DEST%"

echo "Sync completed."
pause