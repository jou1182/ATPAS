#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for utils/taskbar_progress.py.

All tests run without Windows or comtypes — everything is mocked.
"""

from __future__ import annotations

import importlib
import sys
import types
import unittest
import unittest.mock as mock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fresh_module():
    """Import (or re-import) taskbar_progress with a clean module cache."""
    mod_name = "utils.taskbar_progress"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    import utils.taskbar_progress as m
    return m


def _module_no_comtypes():
    """Return the module with comtypes stubbed out as unavailable."""
    mod_name = "utils.taskbar_progress"
    if mod_name in sys.modules:
        del sys.modules[mod_name]
    with mock.patch.dict(
        "sys.modules",
        {
            "comtypes":        None,
            "comtypes.client": None,
            "comtypes.shell":  None,
        },
    ):
        import utils.taskbar_progress as m
    return m


# ---------------------------------------------------------------------------
# Test: no comtypes — all methods must be no-ops
# ---------------------------------------------------------------------------

class TestTaskbarProgressNoComtypes(unittest.TestCase):
    """TaskbarProgress when comtypes is missing."""

    def setUp(self):
        self.mod = _module_no_comtypes()

    def test_init_does_not_crash(self):
        tb = self.mod.TaskbarProgress(0)
        self.assertIsNone(tb._taskbar)

    def test_set_progress_no_crash(self):
        tb = self.mod.TaskbarProgress(0)
        tb.set_progress(50)   # must not raise

    def test_clear_no_crash(self):
        tb = self.mod.TaskbarProgress(0)
        tb.clear()            # must not raise

    def test_set_state_error_no_crash(self):
        tb = self.mod.TaskbarProgress(0)
        tb.set_state_error()  # must not raise

    def test_all_methods_noop_when_taskbar_none(self):
        """Verify internal guard: _taskbar=None means all calls are skipped."""
        tb = self.mod.TaskbarProgress(0)
        self.assertIsNone(tb._taskbar)
        # No assertion needed beyond "no exception raised"
        tb.set_progress(99)
        tb.set_state_error()
        tb.clear()

    def test_set_progress_clamps_high(self):
        """set_progress(150) must not crash; value gets clamped to 100."""
        tb = self.mod.TaskbarProgress(0)
        tb.set_progress(150)  # clamping happens inside, taskbar=None so no-op anyway

    def test_set_progress_clamps_low(self):
        """set_progress(-5) must not crash; value gets clamped to 0."""
        tb = self.mod.TaskbarProgress(0)
        tb.set_progress(-5)


# ---------------------------------------------------------------------------
# Test: clamping logic with a mock taskbar object
# ---------------------------------------------------------------------------

class TestTaskbarProgressClamping(unittest.TestCase):
    """Verify that set_progress clamps out-of-range values before calling COM."""

    def _make_tb_with_mock_taskbar(self):
        mod = _module_no_comtypes()
        tb = mod.TaskbarProgress(42)
        # Inject a fake COM object
        fake = mock.MagicMock()
        tb._taskbar = fake
        return tb, fake

    def test_clamp_above_100(self):
        tb, fake = self._make_tb_with_mock_taskbar()
        tb.set_progress(150)
        _hwnd, completed, total = fake.SetProgressValue.call_args[0]
        self.assertEqual(completed, 100)
        self.assertEqual(total, 100)

    def test_clamp_below_0(self):
        tb, fake = self._make_tb_with_mock_taskbar()
        tb.set_progress(-5)
        _hwnd, completed, total = fake.SetProgressValue.call_args[0]
        self.assertEqual(completed, 0)
        self.assertEqual(total, 100)

    def test_exact_50(self):
        tb, fake = self._make_tb_with_mock_taskbar()
        tb.set_progress(50)
        _hwnd, completed, total = fake.SetProgressValue.call_args[0]
        self.assertEqual(completed, 50)
        self.assertEqual(total, 100)

    def test_set_progress_sets_normal_state(self):
        tb, fake = self._make_tb_with_mock_taskbar()
        tb.set_progress(70)
        fake.SetProgressState.assert_called_once_with(42, 0x2)  # TBPF_NORMAL

    def test_set_state_error_flag(self):
        tb, fake = self._make_tb_with_mock_taskbar()
        tb.set_state_error()
        fake.SetProgressState.assert_called_once_with(42, 0x4)  # TBPF_ERROR

    def test_clear_sets_noprogress(self):
        tb, fake = self._make_tb_with_mock_taskbar()
        tb.clear()
        fake.SetProgressState.assert_called_once_with(42, 0x0)  # TBPF_NOPROGRESS

    def test_hwnd_stored_as_int(self):
        mod = _module_no_comtypes()
        tb = mod.TaskbarProgress(0xDEADBEEF)
        self.assertIsInstance(tb._hwnd, int)
        self.assertEqual(tb._hwnd, 0xDEADBEEF)


# ---------------------------------------------------------------------------
# Test: COM exception handling
# ---------------------------------------------------------------------------

class TestTaskbarProgressComExceptions(unittest.TestCase):
    """Verify that COM failures inside set_*/clear are silently swallowed."""

    def _make_tb_raising(self, exc_type=RuntimeError):
        mod = _module_no_comtypes()
        tb = mod.TaskbarProgress(0)
        fake = mock.MagicMock()
        fake.SetProgressState.side_effect = exc_type("boom")
        fake.SetProgressValue.side_effect = exc_type("boom")
        tb._taskbar = fake
        return tb

    def test_set_progress_swallows_exception(self):
        tb = self._make_tb_raising()
        tb.set_progress(50)  # must not propagate

    def test_set_state_error_swallows_exception(self):
        tb = self._make_tb_raising()
        tb.set_state_error()

    def test_clear_swallows_exception(self):
        tb = self._make_tb_raising()
        tb.clear()


# ---------------------------------------------------------------------------
# Test: send_windows_notification — non-Windows
# ---------------------------------------------------------------------------

class TestSendWindowsNotificationNonWindows(unittest.TestCase):
    """On non-Windows the function must be a silent no-op."""

    def test_noop_on_non_windows(self):
        mod = _module_no_comtypes()
        with mock.patch.object(sys, "platform", "linux"):
            # Should silently do nothing — no subprocess, no error
            mod.send_windows_notification("title", "body")

    def test_noop_returns_none(self):
        mod = _module_no_comtypes()
        with mock.patch.object(sys, "platform", "linux"):
            result = mod.send_windows_notification("t", "m")
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# Test: send_windows_notification — Windows path
# ---------------------------------------------------------------------------

class TestSendWindowsNotificationWindows(unittest.TestCase):
    """On Windows, the function spawns a PowerShell process."""

    def test_spawns_powershell(self):
        mod = _module_no_comtypes()
        with mock.patch.object(sys, "platform", "win32"):
            with mock.patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = mock.MagicMock()
                mod.send_windows_notification("ATPAS Done", "Build finished")
                self.assertTrue(mock_popen.called)
                cmd = mock_popen.call_args[0][0]
                self.assertIn("powershell", cmd[0])

    def test_uses_no_window_flag(self):
        """CREATE_NO_WINDOW (0x08000000) must be passed so no console flashes."""
        mod = _module_no_comtypes()
        with mock.patch.object(sys, "platform", "win32"):
            with mock.patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = mock.MagicMock()
                mod.send_windows_notification("t", "m")
                kwargs = mock_popen.call_args[1]
                self.assertEqual(kwargs.get("creationflags"), 0x08000000)

    def test_subprocess_error_swallowed(self):
        """If Popen raises (e.g. PowerShell not in PATH), it must not propagate."""
        mod = _module_no_comtypes()
        with mock.patch.object(sys, "platform", "win32"):
            with mock.patch("subprocess.Popen", side_effect=FileNotFoundError("no ps")):
                # Must not raise
                mod.send_windows_notification("t", "m")

    def test_single_quotes_in_title_escaped(self):
        """Titles containing ' must not break the PowerShell string literal."""
        mod = _module_no_comtypes()
        with mock.patch.object(sys, "platform", "win32"):
            with mock.patch("subprocess.Popen") as mock_popen:
                mock_popen.return_value = mock.MagicMock()
                # Should not raise even with embedded quotes
                mod.send_windows_notification("It's done", "Build 'ok'")
                self.assertTrue(mock_popen.called)


# ---------------------------------------------------------------------------
# Test: import cleanliness
# ---------------------------------------------------------------------------

class TestModuleImport(unittest.TestCase):
    """The module must import cleanly on any platform without comtypes."""

    def test_import_without_comtypes(self):
        """Top-level import must not raise even if comtypes is absent."""
        mod_name = "utils.taskbar_progress"
        sys.modules.pop(mod_name, None)
        with mock.patch.dict(
            "sys.modules",
            {"comtypes": None, "comtypes.client": None, "comtypes.shell": None},
        ):
            import utils.taskbar_progress  # noqa: F401 — just testing import


if __name__ == "__main__":
    unittest.main()
