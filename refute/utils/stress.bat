@REM generator opt brute test_write_path
@echo off
setlocal EnableDelayedExpansion

:: Create unique temporary file names using timestamp and random numbers
for /f %%A in ('powershell -command "echo $PID"') do set "PID=%%A"
set /a random_num=%PID%
set "temp_input=%TEMP%\input_!random_num!.txt"
set "temp_opt=%TEMP%\opt_!random_num!.txt"
set "temp_brute=%TEMP%\brute_!random_num!.txt"

:: Compile C++ files if needed
for %%F in (%1 %2 %3) do (
    set "file=%%~F"
    set "ext=%%~xF"
    if /I "!ext!" == ".cpp" (
        echo Compiling !file!
        g++ !file! -static -DONLINE_JUDGE -O2 -std=c++23 -Wl,--stack=268435456 -lstdc++exp -march=native -o !file!.exe
        if errorlevel 1 (
            echo Compilation failed for !file!
            exit /b 1
        )
    )
)

set i=1
:loop
echo !i!

:: Determine command for generator
set "gen_cmd=python %1"
if /I "%~x1" == ".cpp" set "gen_cmd=%1.exe"

:: Generate test case
%gen_cmd% > "!temp_input!"

:: Determine command for optimized solution
set "opt_cmd=python %2"
if /I "%~x2" == ".cpp" set "opt_cmd=%2.exe"

:: Run optimized solution
%opt_cmd% < "!temp_input!" > "!temp_opt!"
if errorlevel 1 (
    :: Clean up temporary files before exiting
    del "!temp_input!" 2>nul
    del "!temp_opt!" 2>nul
    del "!temp_brute!" 2>nul
    exit /b 0
)

:: Determine command for brute force solution
set "brute_cmd=python %3"
if /I "%~x3" == ".cpp" set "brute_cmd=%3.exe"

:: Run brute force solution
%brute_cmd% < "!temp_input!" > "!temp_brute!"

:: Compare outputs
fc /w "!temp_opt!" "!temp_brute!" >nul
if errorlevel 1 (
    echo Different outputs found!
    :: Copy files to permanent location for debugging before cleaning up
    copy /Y "!temp_input!" "%4" >nul
    :: Clean up temporary files
    del "!temp_input!" 2>nul
    del "!temp_opt!" 2>nul
    del "!temp_brute!" 2>nul
    exit /b 0
)

set /a i+=1
goto :loop