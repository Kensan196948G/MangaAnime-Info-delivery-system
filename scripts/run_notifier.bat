@echo off
REM ===========================================================
REM MangaAnime-Info-delivery-system ノーティファイア実行スクリプト
REM Windows タスクスケジューラから呼び出されます
REM ===========================================================

REM プロジェクトルートの設定
set PROJECT_ROOT=D:\MangaAnime-Info-delivery-system

REM ログファイルのパス設定
set LOG_FILE=%PROJECT_ROOT%\logs\scheduler.log

REM タイムスタンプ生成（YYYY-MM-DD HH:MM:SS形式）
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set YEAR=%%d
    set MONTH=%%b
    set DAY=%%c
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set HOUR=%%a
    set MINUTE=%%b
)
set TIMESTAMP=%YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%

REM ログに開始記録
echo [%TIMESTAMP%] INFO: MangaAnime Notifier 開始 >> "%LOG_FILE%"

REM プロジェクトルートに移動
cd /d "%PROJECT_ROOT%"

REM Python -X utf8 で release_notifier.py を実行
REM .env は python-dotenv により自動読み込み
python -X utf8 "%PROJECT_ROOT%\app\release_notifier.py" >> "%LOG_FILE%" 2>&1

REM 終了コードの記録
set EXIT_CODE=%ERRORLEVEL%

REM 終了状態をログに記録
for /f "tokens=1-4 delims=/ " %%a in ('date /t') do (
    set YEAR=%%d
    set MONTH=%%b
    set DAY=%%c
)
for /f "tokens=1-2 delims=: " %%a in ('time /t') do (
    set HOUR=%%a
    set MINUTE=%%b
)
set TIMESTAMP=%YEAR%-%MONTH%-%DAY% %HOUR%:%MINUTE%

if %EXIT_CODE% EQU 0 (
    echo [%TIMESTAMP%] INFO: MangaAnime Notifier 正常終了 (終了コード: %EXIT_CODE%) >> "%LOG_FILE%"
) else (
    echo [%TIMESTAMP%] ERROR: MangaAnime Notifier 異常終了 (終了コード: %EXIT_CODE%) >> "%LOG_FILE%"
)

echo ------------------------------------------------------------------ >> "%LOG_FILE%"

exit /b %EXIT_CODE%
