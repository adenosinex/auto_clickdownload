@echo off
:: 1. 检查管理员权限，如果没有则静默提权
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo Set UAC = CreateObject^("Shell.Application"^) > "%temp%\getadmin.vbs"
    :: 使用 runas 提权，提权后新窗口执行，当前旧窗口立刻 exit 关闭
    echo UAC.ShellExecute "%~s0", "", "", "runas", 1 >> "%temp%\getadmin.vbs"
    "%temp%\getadmin.vbs"
    exit
)

:: 2. 清理提权临时文件
if exist "%temp%\getadmin.vbs" ( del "%temp%\getadmin.vbs" )

:: 3. 核心：将当前 RDP 会话转移到 Console（保持屏幕常亮）
for /f "skip=1 tokens=3" %%s in ('query user %USERNAME%') do (
  %windir%\System32\tscon.exe %%s /dest:console
)

:: 4. 重点：强制退出！瞬间关闭黑窗口，绝不遮挡任何画面
exit