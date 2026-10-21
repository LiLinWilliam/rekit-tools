# rizin: meson setup（首次会联网抓 wrap 子项目；已配置过则原地重新生成 build.ninja）
. "$PSScriptRoot\..\env.ps1"
Use-Msvc
Push-Location "$RK\rizin"
$meson   = "$env:VENV_BUILDTOOLS\Scripts\meson.exe"
$prefix  = "$RK\rizin\rizin-install"
try {
if (Test-Path -LiteralPath "build\meson-private\coredata.dat") {
    & $meson setup build --reconfigure --buildtype=release -Dportable=true --prefix="$prefix"
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "reconfigure 失败（构建目录被移动过时会发生），改用 --wipe 重新配置"
        & $meson setup build --wipe --buildtype=release -Dportable=true --prefix="$prefix"
    }
} else {
    & $meson setup build --buildtype=release -Dportable=true --prefix="$prefix"
}
if ($LASTEXITCODE -ne 0) { throw "meson setup failed: $LASTEXITCODE" }
Write-Host "MESON-SETUP-OK"
} finally { Pop-Location }
