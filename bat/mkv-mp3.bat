@echo off
setlocal enabledelayedexpansion

:: ----------------------------------------
:: Settings
:: ----------------------------------------

:: Use extended-length paths to avoid MAX_PATH issues
set "INPUT=\\?\C:\Users\admin\OneDrive\Desktop\Sweeney Todd (1982)\Sweeney Todd (1982).mkv"
set "OUTPUT_DIR=\\?\C:\Users\admin\OneDrive\Desktop\Sweeney Todd (1982)\Soundtrack1982"

:: Metadata
set "ARTIST=Stephen Sondheim"
set "ALBUM=Sweeney Todd: The Demon Barber of Fleet Street (1982)"
set "YEAR=1982"

:: ----------------------------------------
:: Prepare output folder & logs
:: ----------------------------------------

if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!"

:: Get an ISO-formatted timestamp for log headers
for /f %%I in ('powershell -NoProfile -Command "Get-Date -Format yyyy-MM-ddTHH:mm:ss"') do set "TIMESTAMP=%%I"

> "!OUTPUT_DIR!\success_log.txt" echo Extraction started %TIMESTAMP%
> "!OUTPUT_DIR!\error_log.txt"   echo Extraction started %TIMESTAMP%

:: ----------------------------------------
:: Song definitions (Title|Start|End)
:: ----------------------------------------

set songs[1]=The Ballad of Sweeney Todd (Prelude)|00:00:00|00:06:30
set songs[2]=No Place Like London|00:06:30|00:14:50
set songs[3]=The Barber and His Wife|00:14:50|00:16:30
set songs[4]=The Worst Pies in London|00:16:30|00:19:30
set songs[5]=Poor Thing|00:19:30|00:23:00
set songs[6]=My Friends|00:23:00|00:26:30
set songs[7]=Green Finch and Linnet Bird|00:27:30|00:30:00
set songs[8]=Ah Miss|00:30:00|00:31:00
set songs[9]=Johanna|00:31:00|00:34:00
set songs[10]=Pirelli's Miracle Elixir|00:34:00|00:36:30
set songs[11]=The Contest|00:36:30|00:39:30
set songs[12]=Wait|00:39:30|00:42:00
set songs[13]=Kiss Me & Ladies in Their Sensitivities|00:42:00|00:46:30
set songs[14]=Pretty Women|00:46:30|00:49:30
set songs[15]=Epiphany|00:49:30|00:53:30
set songs[16]=A Little Priest|01:12:30|01:18:30
set songs[17]=God That's Good|01:18:30|01:22:30
set songs[18]=Johanna (Quartet)|01:22:30|01:25:30
set songs[19]=By the Sea|01:25:30|01:28:00
set songs[20]=Wigmaker Sequence|01:28:00|01:31:00
set songs[21]=Not While I'm Around|01:31:00|01:34:00
set songs[22]=Parlor Songs|01:34:00|01:37:30
set songs[23]=City on Fire|01:37:30|01:40:30
set songs[24]=Final Sequence|01:40:30|01:46:00
set songs[25]=The Ballad of Sweeney Todd (Epilogue)|01:46:00|01:49:00

:: ----------------------------------------
:: Extraction loop
:: ----------------------------------------

for /L %%i in (1,1,25) do (
    for /f "tokens=1-3 delims=|" %%A in ("!songs[%%i]!") do (
        set "TITLE=%%A"
        set "START=%%B"
        set "END=%%C"
        set "TRACKNUM=%%i"

        :: — Sanitize TITLE for filename —
        set "sanitizedTitle=!TITLE!"
        set "sanitizedTitle=!sanitizedTitle:<=-!"
        set "sanitizedTitle=!sanitizedTitle:>=-!"
        set "sanitizedTitle=!sanitizedTitle::=-!"
        set "sanitizedTitle=!sanitizedTitle:"=-!"
        set "sanitizedTitle=!sanitizedTitle:/=-!"
        set "sanitizedTitle=!sanitizedTitle:\=-!"
        set "sanitizedTitle=!sanitizedTitle:|=-!"
        set "sanitizedTitle=!sanitizedTitle:?=-!"
        set "sanitizedTitle=!sanitizedTitle:*= -!"

        set "OUTFILE=!OUTPUT_DIR!\%%i - !sanitizedTitle!.mp3"

        echo Extracting Track %%i - "!TITLE!"...

        ffmpeg -y -ss !START! -to !END! -i "!INPUT!" -vn -c:a libmp3lame -b:a 320k ^
            -metadata title="!TITLE!" ^
            -metadata artist="!ARTIST!" ^
            -metadata album="!ALBUM!" ^
            -metadata date="!YEAR!" ^
            -metadata track="!TRACKNUM!" ^
        "!OUTFILE!"

        if errorlevel 1 (
            >> "!OUTPUT_DIR!\error_log.txt" echo [!TRACKNUM!] ERROR extracting "!TITLE!" at %TIMESTAMP%
        ) else (
            >> "!OUTPUT_DIR!\success_log.txt" echo [!TRACKNUM!] Extracted "!TITLE!" at %TIMESTAMP%
        )
    )
)

echo.
echo All tracks processed. Check logs in %OUTPUT_DIR%.
pause
