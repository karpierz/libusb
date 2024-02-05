# Copyright (c) 2016 Adam Karpierz
# Licensed under the zlib/libpng License
# https://opensource.org/license/zlib

from libusb._platform import is_windows

if is_windows:

    import ctypes
    from ctypes import windll
    from ctypes import wintypes
    from ctypes import WINFUNCTYPE
    from ctypes.wintypes import (
        CHAR, WCHAR, BOOLEAN, BOOL, BYTE, WORD, DWORD, SHORT, USHORT, INT,
        UINT, LONG, ULONG, LARGE_INTEGER, ULARGE_INTEGER, FLOAT, DOUBLE,
        LPBYTE, PBYTE, LPWORD, PWORD, LPDWORD, PDWORD, LPLONG, PLONG, LPSTR,
        LPCSTR, LPVOID, LPCVOID, LPVOID as PVOID, HANDLE, LPHANDLE, PHANDLE,
        WPARAM, LPARAM, FILETIME, LPFILETIME,
    )

    from ctypes.wintypes import WPARAM as ULONG_PTR # workaround
    PULONG_PTR = ctypes.POINTER(ULONG_PTR)

    ULONG32   = ctypes.c_uint32
    ULONGLONG = ctypes.c_uint64
    DWORDLONG = ctypes.c_uint64
    SIZE_T    = ctypes.c_size_t

    WAIT_ABANDONED = 0x00000080
    WAIT_OBJECT_0  = 0x00000000
    WAIT_TIMEOUT   = 0x00000102
    WAIT_FAILED    = 0xFFFFFFFF

    IGNORE   = 0
    INFINITE = 0xFFFFFFFF

    class SECURITY_ATTRIBUTES(ctypes.Structure):
        _fields_ = [
        ("nLength",              DWORD),
        ("lpSecurityDescriptor", LPVOID),
        ("bInheritHandle",       BOOL),
    ]
    LPSECURITY_ATTRIBUTES = ctypes.POINTER(SECURITY_ATTRIBUTES)

    LPTHREAD_START_ROUTINE = WINFUNCTYPE(DWORD, LPVOID)
    CreateThread = windll.kernel32.CreateThread
    CreateThread.restype  = HANDLE
    CreateThread.argtypes = [LPSECURITY_ATTRIBUTES,
                             SIZE_T,
                             LPTHREAD_START_ROUTINE,
                             LPVOID,
                             DWORD,
                             LPDWORD]

    WaitForSingleObject = windll.kernel32.WaitForSingleObject
    WaitForSingleObject.restype  = DWORD
    WaitForSingleObject.argtypes = [HANDLE,
                                    DWORD]

    CreateSemaphore = windll.kernel32.CreateSemaphoreA
    CreateSemaphore.restype  = HANDLE
    CreateSemaphore.argtypes = [LPSECURITY_ATTRIBUTES,
                                LONG,
                                LONG,
                                LPCSTR]

    ReleaseSemaphore = windll.kernel32.ReleaseSemaphore
    ReleaseSemaphore.restype  = BOOL
    ReleaseSemaphore.argtypes = [HANDLE,
                                 LONG,
                                 LPLONG]

    Sleep = windll.kernel32.Sleep
    Sleep.restype  = None
    Sleep.argtypes = [DWORD]

    CloseHandle = windll.kernel32.CloseHandle
    CloseHandle.restype  = BOOL
    CloseHandle.argtypes = [HANDLE]

    del ctypes
