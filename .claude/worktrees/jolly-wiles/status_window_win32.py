"""
Jarvis Assistant - Windows status window (win32)
Uses Win32 API so the window always appears in the taskbar, even when tkinter fails in EXE.
"""

import sys

_hwnd = None
_on_close = None

if sys.platform != "win32":
    def create_win32_status_window(on_close_callback=None):
        return False
    def pump_win32_status():
        pass
    def hide_win32_status():
        pass
else:
    def _wndproc(hwnd, msg, wparam, lparam):
        global _on_close
        if msg == 0x0010:  # WM_CLOSE
            try:
                import win32gui
                win32gui.DestroyWindow(hwnd)
            except Exception:
                pass
            return 0
        if msg == 0x0002:  # WM_DESTROY
            if _on_close:
                try:
                    _on_close()
                except Exception:
                    pass
            return 0
        try:
            import win32gui
            return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
        except Exception:
            return 0

    def create_win32_status_window(on_close_callback=None):
        """Create a small Win32 window that shows in the taskbar. Returns True if created."""
        global _hwnd, _on_close
        try:
            import win32gui
            import win32con
            import win32api
        except ImportError:
            return False

        _on_close = on_close_callback
        if _hwnd is not None:
            return True

        hinst = win32api.GetModuleHandle(None)
        class_name = "JarvisStatusWindow"

        try:
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = _wndproc
            wc.lpszClassName = class_name
            wc.hInstance = hinst
            wc.hCursor = win32api.LoadCursor(0, 32512)  # IDC_ARROW
            wc.hbrBackground = win32con.COLOR_WINDOW + 1
            win32gui.RegisterClass(wc)
        except Exception:
            pass

        try:
            _hwnd = win32gui.CreateWindowEx(
                0,
                class_name,
                "Jarvis - Listening",
                win32con.WS_OVERLAPPED | win32con.WS_CAPTION | win32con.WS_SYSMENU | win32con.WS_VISIBLE,
                100, 100, 320, 130,
                0, 0, hinst, None
            )
            # Static text: "Jarvis is listening"
            win32gui.CreateWindowEx(
                0, "STATIC", "Jarvis is listening",
                win32con.WS_CHILD | win32con.WS_VISIBLE,
                20, 16, 280, 24, _hwnd, 0, hinst, None
            )
            win32gui.CreateWindowEx(
                0, "STATIC", "Press F8 or close this window to exit.",
                win32con.WS_CHILD | win32con.WS_VISIBLE,
                20, 44, 280, 20, _hwnd, 0, hinst, None
            )
            win32gui.ShowWindow(_hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(_hwnd)
            # Center at top of screen
            try:
                sw = win32api.GetSystemMetrics(0)
                sh = win32api.GetSystemMetrics(1)
                r = win32gui.GetWindowRect(_hwnd)
                w = r[2] - r[0]
                h = r[3] - r[1]
                x = max(0, (sw - w) // 2)
                win32gui.SetWindowPos(_hwnd, 0, x, 24, 0, 0, 0x0001 | 0x0004)  # SWP_NOSIZE | SWP_NOZORDER
            except Exception:
                pass
            return True
        except Exception:
            _hwnd = None
            return False

    def pump_win32_status():
        """Process pending Win32 messages for the status window. Call from main loop."""
        global _hwnd
        if _hwnd is None:
            return
        try:
            import win32gui
            import win32api
            msg = win32api.MSG()
            while win32gui.PeekMessage(msg, 0, 0, 0, 1):  # PM_REMOVE
                win32gui.TranslateMessage(msg)
                win32gui.DispatchMessage(msg)
        except Exception:
            pass

    def hide_win32_status():
        """Close the Win32 status window."""
        global _hwnd
        if _hwnd is None:
            return
        try:
            import win32gui
            win32gui.DestroyWindow(_hwnd)
        except Exception:
            pass
        _hwnd = None
