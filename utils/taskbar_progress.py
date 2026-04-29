#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Windows Taskbar progress integration using ITaskbarList3 COM interface.

Works on Windows 7+ (Windows 10/11 tested). Silently no-ops on non-Windows
and when comtypes is not installed.

Usage:
    tb = TaskbarProgress(hwnd)
    tb.set_progress(50)       # 50% green bar
    tb.set_state_error()      # red bar
    tb.clear()                # remove progress bar

    send_windows_notification("Title", "Body text")
"""

from __future__ import annotations

import logging
import subprocess
import sys

logger = logging.getLogger(__name__)


class TaskbarProgress:
    """Controls the Windows taskbar button progress indicator via ITaskbarList3.

    All methods are guaranteed to be no-ops on non-Windows or when comtypes
    is unavailable — they will never raise.
    """

    def __init__(self, hwnd: int) -> None:
        """
        Args:
            hwnd: Windows handle from QWidget.winId() — must be cast to int.
        """
        self._hwnd = int(hwnd)
        self._taskbar = None
        if sys.platform == "win32":
            self._taskbar = self._try_init()

    def _try_init(self):
        """Create ITaskbarList3 COM object. Returns None silently on any failure."""
        try:
            import comtypes.client  # type: ignore[import]
            import comtypes.shell   # type: ignore[import]  # noqa: F401 — registers shell types
            tb = comtypes.client.CreateObject(
                "{56FDF344-FD6D-11d0-958A-006097C9A090}",
                interface=comtypes.shell.ITaskbarList3,
            )
            tb.HrInit()
            return tb
        except Exception as exc:  # noqa: BLE001
            logger.debug("TaskbarProgress COM init skipped: %s", exc)
            return None

    def set_progress(self, percent: int) -> None:
        """Set progress 0–100. Automatically switches taskbar button to NORMAL (green) state.

        Values outside [0, 100] are clamped silently.
        """
        if self._taskbar is None:
            return
        try:
            clamped = max(0, min(int(percent), 100))
            self._taskbar.SetProgressState(self._hwnd, 0x2)   # TBPF_NORMAL
            self._taskbar.SetProgressValue(self._hwnd, clamped, 100)
        except Exception as exc:  # noqa: BLE001
            logger.debug("TaskbarProgress.set_progress failed: %s", exc)

    def set_state_error(self) -> None:
        """Switch taskbar button to error state (red bar)."""
        if self._taskbar is None:
            return
        try:
            self._taskbar.SetProgressState(self._hwnd, 0x4)   # TBPF_ERROR
        except Exception as exc:  # noqa: BLE001
            logger.debug("TaskbarProgress.set_state_error failed: %s", exc)

    def clear(self) -> None:
        """Remove the progress bar from the taskbar button."""
        if self._taskbar is None:
            return
        try:
            self._taskbar.SetProgressState(self._hwnd, 0x0)   # TBPF_NOPROGRESS
        except Exception as exc:  # noqa: BLE001
            logger.debug("TaskbarProgress.clear failed: %s", exc)


def send_windows_notification(title: str, message: str) -> None:
    """Send a Windows balloon-tip toast notification via PowerShell.

    Uses System.Windows.Forms.NotifyIcon — no external packages needed.
    Silently does nothing on non-Windows or on any error.

    Args:
        title:   Notification title (shown in bold).
        message: Notification body text.
    """
    if sys.platform != "win32":
        return
    try:
        # Escape single quotes to avoid breaking the PowerShell string literals
        safe_title   = title.replace("'", "\\'")
        safe_message = message.replace("'", "\\'")
        script = (
            "Add-Type -AssemblyName System.Windows.Forms; "
            "Add-Type -AssemblyName System.Drawing; "
            "$n = New-Object System.Windows.Forms.NotifyIcon; "
            "$n.Icon = [System.Drawing.SystemIcons]::Application; "
            "$n.Visible = $True; "
            f"$n.ShowBalloonTip(4000, '{safe_title}', '{safe_message}', "
            "[System.Windows.Forms.ToolTipIcon]::Info); "
            "Start-Sleep -Milliseconds 4500; "
            "$n.Visible = $False; "
            "$n.Dispose()"
        )
        subprocess.Popen(
            ["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
            creationflags=0x08000000,  # CREATE_NO_WINDOW — suppress console flash
        )
    except Exception as exc:  # noqa: BLE001
        logger.debug("send_windows_notification failed: %s", exc)
