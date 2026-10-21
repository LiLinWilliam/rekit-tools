# rizin: ninja 构建 + 本地安装
. "$PSScriptRoot\..\env.ps1"
Use-Msvc
Push-Location "$RK\rizin"
try {
    ninja -C build -j 10
    if ($LASTEXITCODE -ne 0) { throw "ninja failed: $LASTEXITCODE" }
    ninja -C build -j 10 install
    if ($LASTEXITCODE -ne 0) { throw "ninja install failed: $LASTEXITCODE" }
    & "$RK\rizin\rizin-install\bin\rizin.exe" -v
} finally { Pop-Location }
