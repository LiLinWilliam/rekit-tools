# 构建 binwalk 3.1.1 (Rust) —— 产物走 CARGO_TARGET_DIR
. "$PSScriptRoot\..\env.ps1"
Use-Msvc
Push-Location "$RK\binwalk"
try {
    & "$env:CARGO_HOME\bin\cargo.exe" build --release --locked --offline -j 6
    if ($LASTEXITCODE -ne 0) { throw "cargo build failed: $LASTEXITCODE" }
    & "$env:CARGO_TARGET_DIR\release\binwalk.exe" --help
} finally { Pop-Location }
