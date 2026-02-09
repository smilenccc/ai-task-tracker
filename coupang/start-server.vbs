Set objShell = CreateObject("WScript.Shell")
objShell.Run "cmd /c cd /d ""C:\Users\smile\ai-task-tracker"" && node coupang/server.mjs", 0, False
