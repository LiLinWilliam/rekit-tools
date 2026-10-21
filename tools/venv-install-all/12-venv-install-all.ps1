# Exact-version offline restore. Use --online only when index access is intended.
& "$PSScriptRoot\..\bin\repair.exe" @args
exit $LASTEXITCODE
