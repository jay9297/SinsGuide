import base64
import re
import zlib
from dataclasses import dataclass



@dataclass
class GemSetup:
    name: str
    level: int
    links: list[str]


@dataclass
class Build:
    name: str
    class_name: str
    level: int
    gems: list[GemSetup]
    tree_url: str


class PoBParser:
    POB_URL = "https://pobb.in"

    def parse_url(self, url: str) -> Build | None:
        code = self._extract_code(url)
        if not code:
            return None
        return self._decode(code)

    def _extract_code(self, url: str) -> str | None:
        match = re.search(r"pobb\.in/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        match = re.search(r"poe\.ninja/pob/([a-zA-Z0-9_-]+)", url)
        if match:
            return match.group(1)
        return None

    def _decode(self, code: str) -> Build | None:
        try:
            raw = base64.urlsafe_b64decode(code + "==")
            decompressed = zlib.decompress(raw)
            xml = decompressed.decode("utf-8")
            return self._parse_xml(xml)
        except Exception:
            return None

    def _parse_xml(self, xml: str) -> Build:
        name_match = re.search(r'<PathOfBuilding[^>]+>([^<]+)</PathOfBuilding>', xml)
        name = name_match.group(1) if name_match else "Unknown Build"

        class_match = re.search(r'<ClassName>([^<]+)</ClassName>', xml)
        class_name = class_match.group(1) if class_match else "Unknown"

        level_match = re.search(r'<Level>(\d+)</Level>', xml)
        level = int(level_match.group(1)) if level_match else 1

        gems = []
        for gem_match in re.finditer(r'<Gem[^>]+>', xml):
            gem_str = gem_match.group(0)
            name_m = re.search(r'name="([^"]+)"', gem_str)
            level_m = re.search(r'level="(\d+)"', gem_str)
            if name_m:
                gem = GemSetup(
                    name=name_m.group(1),
                    level=int(level_m.group(1)) if level_m else 1,
                    links=[],
                )
                gems.append(gem)

        return Build(
            name=name,
            class_name=class_name,
            level=level,
            gems=gems,
            tree_url="",
        )
