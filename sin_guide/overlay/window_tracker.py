import logging
import subprocess
from Xlib import X
from Xlib.display import Display


class WindowTracker:
    def __init__(self, window_title: str = "Path of Exile 2"):
        self.window_title = window_title.lower()
        self.display = Display()
        self.root = self.display.screen().root
        self.game_window = None

    def find_game_window(self):
        self.game_window = self._find_window(self.root)
        return self.game_window

    def _find_window(self, parent):
        try:
            children = parent.query_tree().children
            for child in children:
                try:
                    name = child.get_wm_name()
                    if name and self.window_title in name.lower():
                        return child
                except Exception:
                    pass
                try:
                    class_name = child.get_wm_class()
                    if class_name and any(self.window_title in c.lower() for c in class_name if c):
                        return child
                except Exception:
                    pass
                result = self._find_window(child)
                if result:
                    return result
        except Exception:
            pass
        return None

    def _get_active_title_via_subprocess(self) -> str | None:
        try:
            r1 = subprocess.run(
                ["xprop", "-root", "_NET_ACTIVE_WINDOW"],
                capture_output=True, text=True, timeout=2
            )
            if r1.returncode != 0:
                return None
            out = r1.stdout.strip()
            if "window id" not in out:
                return None
            parts = out.split("#")
            if len(parts) < 2:
                return None
            window_id = parts[-1].strip()
            r2 = subprocess.run(
                ["xprop", "-id", window_id, "_NET_WM_NAME", "WM_NAME"],
                capture_output=True, text=True, timeout=2
            )
            if r2.returncode != 0:
                return None
            import re
            for line in r2.stdout.split("\n"):
                if "_NET_WM_NAME" in line or "WM_NAME" in line:
                    m = re.search(r'"([^"]+)"', line)
                    if m:
                        return m.group(1)
        except Exception:
            pass
        return None

    def _get_focus_title_via_xlib(self) -> str | None:
        try:
            focus = self.display.get_input_focus().focus
            if not focus:
                return None
            try:
                atom = self.display.intern_atom("_NET_WM_NAME")
                prop = focus.get_full_property(atom, 0)
                if prop and prop.value:
                    return prop.value.decode("utf-8", errors="ignore")
            except Exception:
                pass
            try:
                return focus.get_wm_name()
            except Exception:
                pass
            try:
                parent = focus.query_tree().parent
                while parent and parent.id != self.root.id:
                    try:
                        return parent.get_wm_name()
                    except Exception:
                        pass
                    parent = parent.query_tree().parent
            except Exception:
                pass
        except Exception:
            pass
        return None

    def is_game_focused(self) -> bool:
        title = self._get_active_title_via_subprocess()
        if title and self.window_title in title.lower():
            return True
        title = self._get_focus_title_via_xlib()
        if title and self.window_title in title.lower():
            return True
        return False

    def is_game_mapped(self) -> bool:
        if not self.game_window:
            return False
        try:
            attrs = self.game_window.get_attributes()
            return attrs.map_state == X.IsViewable
        except Exception:
            return False

    def _is_poe2_process_running(self) -> bool:
        try:
            result = subprocess.run(
                ["pgrep", "-f", "PathOfExile"],
                capture_output=True, timeout=2
            )
            return result.returncode == 0
        except Exception:
            return False

    def log_discovered_titles(self) -> None:
        logger = logging.getLogger(__name__)
        titles: list[str] = []

        def _collect_titles(parent) -> None:
            try:
                children = parent.query_tree().children
                for child in children:
                    try:
                        name = child.get_wm_name()
                        if name and "path of exile" in name.lower():
                            titles.append(name)
                    except Exception:
                        pass
                    try:
                        class_name = child.get_wm_class()
                        if class_name and any("path of exile" in c.lower() for c in class_name if c):
                            titles.append(f"[class] {class_name}")
                    except Exception:
                        pass
                    _collect_titles(child)
            except Exception:
                pass

        _collect_titles(self.root)
        if titles:
            for title in titles:
                logger.debug("Discovered PoE window: %s", title)
        else:
            logger.debug("No windows matching 'path of exile' found")

    def debug_active_window(self) -> None:
        logger = logging.getLogger(__name__)
        title = self._get_active_title_via_subprocess()
        if title is None:
            title = self._get_focus_title_via_xlib()
        is_poe = self.is_game_focused()
        logger.debug("Active window: %s | PoE2 focused: %s", title or "<unknown>", is_poe)

    def should_show_overlay(self, overlay_window_id: int | None = None) -> bool:
        if self.is_game_focused():
            return True
        if overlay_window_id:
            try:
                focus = self.display.get_input_focus().focus
                if focus and focus.id == overlay_window_id:
                    return True
            except Exception:
                pass
        return False

    def subscribe_to_active_window_changes(self) -> None:
        try:
            self.root.change_attributes(event_mask=X.PropertyChangeMask)
            self.display.flush()
            self._net_active_window_atom = self.display.intern_atom("_NET_ACTIVE_WINDOW")
        except Exception:
            self._net_active_window_atom = None

    def drain_active_window_events(self) -> bool:
        if not getattr(self, "_net_active_window_atom", None):
            return False
        changed = False
        try:
            while self.display.pending_events() > 0:
                event = self.display.next_event()
                if event.type == X.PropertyNotify and event.atom == self._net_active_window_atom:
                    changed = True
        except Exception:
            pass
        return changed

    def get_game_geometry(self):
        if not self.game_window:
            return None
        try:
            geom = self.game_window.get_geometry()
            parent = self.game_window.query_tree().parent
            if parent:
                pgeom = parent.get_geometry()
                return {
                    "x": pgeom.x + geom.x,
                    "y": pgeom.y + geom.y,
                    "width": geom.width,
                    "height": geom.height,
                }
            return {"x": geom.x, "y": geom.y, "width": geom.width, "height": geom.height}
        except Exception:
            return None

    def cleanup(self):
        self.display.close()
