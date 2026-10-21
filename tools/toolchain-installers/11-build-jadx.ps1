# 构建 jadx (Gradle) —— 产物 jadx\build\jadx\bin
. "$PSScriptRoot\..\env.ps1"
Push-Location "$RK\jadx"
try {
    .\gradlew.bat dist :jadx-cli:installDist :jadx-gui:installDist --offline --max-workers=4 --no-daemon
    if ($LASTEXITCODE -ne 0) { throw "gradle build failed: $LASTEXITCODE" }
} finally { Pop-Location }
