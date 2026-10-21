# Recover runtime environments with rollback; no changes to shared GhidraLab.
& "$PSScriptRoot\..\bin\repair.exe" @args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
& "$PSScriptRoot\..\bin\doctor.exe"
exit $LASTEXITCODE
