/* Windows-only, statically linked bootstrap. No PowerShell/.NET dependency. */
#define UNICODE
#define _UNICODE
#include <windows.h>
#include <stdio.h>
#include <wchar.h>

static BOOL WINAPI console_handler(DWORD kind) {
    return kind == CTRL_C_EVENT || kind == CTRL_BREAK_EVENT;
}

int wmain(void) {
    wchar_t module[32768], root[32768], pattern[32768], python[32768];
    wchar_t tool[256], script[32768];
    WIN32_FIND_DATAW entry;
    GetModuleFileNameW(NULL, module, 32768);
    wcscpy_s(root, 32768, module);
    wchar_t *sep = wcsrchr(root, L'\\');
    if (!sep) return 3;
    wcsncpy_s(tool, 256, sep + 1, _TRUNCATE);
    wchar_t *ext = wcsrchr(tool, L'.');
    if (ext) *ext = 0;
    *sep = 0;
    sep = wcsrchr(root, L'\\');
    if (!sep) return 3;
    *sep = 0;
    swprintf_s(pattern, 32768, L"%s\\toolchain\\python\\cpython-3.12.*-windows-x86_64-none", root);
    HANDLE search = FindFirstFileW(pattern, &entry);
    if (search == INVALID_HANDLE_VALUE) {
        fwprintf(stderr, L"rekit: local Python runtime missing under %s\n", root);
        return 3;
    }
    swprintf_s(python, 32768, L"%s\\toolchain\\python\\%s\\python.exe", root, entry.cFileName);
    FindClose(search);
    swprintf_s(script, 32768, L"%s\\bin\\_launch.py", root);
    const wchar_t *tail = GetCommandLineW();
    if (*tail == L'\"') {
        ++tail;
        while (*tail && *tail != L'\"') ++tail;
        if (*tail) ++tail;
    } else {
        while (*tail && *tail != L' ' && *tail != L'\t') ++tail;
    }
    while (*tail == L' ' || *tail == L'\t') ++tail;
    wchar_t *cmd = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, 32768 * sizeof(wchar_t));
    if (!cmd) return 3;
    int result;
    if (_wcsicmp(tool, L"rekit") == 0) {
        result = swprintf_s(cmd, 32768, L"\"%s\" -I -B -X utf8 -u \"%s\" %s", python, script, tail);
    } else {
        result = swprintf_s(cmd, 32768, L"\"%s\" -I -B -X utf8 -u \"%s\" %s %s", python, script, tool, tail);
    }
    if (result < 0) return 3;
    STARTUPINFOW startup = {0};
    PROCESS_INFORMATION process = {0};
    startup.cb = sizeof(startup);
    startup.dwFlags = STARTF_USESTDHANDLES;
    startup.hStdInput = GetStdHandle(STD_INPUT_HANDLE);
    startup.hStdOutput = GetStdHandle(STD_OUTPUT_HANDLE);
    startup.hStdError = GetStdHandle(STD_ERROR_HANDLE);
    SetConsoleCtrlHandler(console_handler, TRUE);
    if (!CreateProcessW(python, cmd, NULL, NULL, TRUE, 0, NULL, NULL, &startup, &process)) {
        fwprintf(stderr, L"rekit: launch failed, Windows error %lu\n", GetLastError());
        HeapFree(GetProcessHeap(), 0, cmd);
        return 3;
    }
    HeapFree(GetProcessHeap(), 0, cmd);
    WaitForSingleObject(process.hProcess, INFINITE);
    DWORD code = 3;
    GetExitCodeProcess(process.hProcess, &code);
    CloseHandle(process.hThread);
    CloseHandle(process.hProcess);
    return (int)code;
}
