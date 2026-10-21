$ErrorActionPreference = 'Stop'
. "$PSScriptRoot\..\env.ps1" 6>$null
Use-Msvc
$target = Join-Path $RK 'bin\rekit.exe'
& cl.exe /nologo /O2 /MT /W4 "$PSScriptRoot\launcher.c" "/Fe:$target" "/Fo:$RK\build\launcher.obj" /link /SUBSYSTEM:CONSOLE
if ($LASTEXITCODE -ne 0) { throw "launcher compilation failed: $LASTEXITCODE" }
foreach ($name in @('python','binwalk','rizin','diec','diec-db','die','jadx','jadx-gui','capa','floss','ghidra','ghidra-headless','frida','frida-ps','frida-trace','frida-ls-devices','objection','uv','doctor','repair','pyinstxtractor','shell')) {
    Copy-Item -LiteralPath $target -Destination (Join-Path $RK "bin\$name.exe") -Force
}
Write-Host 'Native launchers built.'
