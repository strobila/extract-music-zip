@echo off

set SCRIPT_NAME=%~nx0
set SCRIPT_DIR=%~dp0

:::::::::::::::::::::::::::::::::::::::::::::::
:: python仮想環境アクティベート
:::::::::::::::::::::::::::::::::::::::::::::::

set MY_VENV_DIR=%USERPROFILE%\python_envs
set MY_VENV_NAME=env_for_ext_music_zip

call %MY_VENV_DIR%\%MY_VENV_NAME%\Scripts\activate.bat

if %errorlevel% neq 0 (
echo %SCRIPT_NAME% : activateエラー（%MY_VENV_NAME%）
pause
exit /b 1
)

echo %SCRIPT_NAME% : Activated "%MY_VENV_NAME%"
::pip freeze
::pause
::exit /b 0

:::::::::::::::::::::::::::::::::::::::::::::::
::python実行
:::::::::::::::::::::::::::::::::::::::::::::::

set PY_SCRIPT_NAME=extract_music_zip.py

python %PY_SCRIPT_NAME%

if %errorlevel% neq 0 (
echo %SCRIPT_NAME% : pythonスクリプト実行エラー（%MY_VENV_NAME%）
pause
exit /b 1
)

echo %SCRIPT_NAME% : 完了
pause
exit /b 0
