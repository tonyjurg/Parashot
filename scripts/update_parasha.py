"""Generate Jekyll data for the coming Shabbat using Hebcal's calendar API."""

import argparse
import json
import os
import re
import time
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


ROOT = Path(__file__).resolve().parents[1]
NAMES = (
    "Bereshit|Noach|Lech-Lecha|Vayera|Chayei Sara|Toldot|"
    "Vayetzei|Vayishlach|Vayeshev|Miketz|Vayigash|Vayechi|"
    "Shemot|Vaera|Bo|Beshalach|Yitro|Mishpatim|Terumah|"
    "Tetzaveh|Ki Tisa|Vayakhel|Pekudei|Vayikra|Tzav|"
    "Shmini|Tazria|Metzora|Achrei Mot|Kedoshim|Emor|Behar|"
    "Bechukotai|Bamidbar|Nasso|Behaalotcha|Shlach|Korach|"
    "Chukat|Balak|Pinchas|Matot|Masei|Devarim|Vaetchanan|"
    "Eikev|Reeh|Shoftim|Ki Teitzei|Ki Tavo|Nitzavim|"
    "Vayeilech|Haazinu|Vezot Haberakhah"
).split("|")
DOUBLES = [(22, 23), (27, 28), (29, 30), (32, 33),
           (39, 40), (42, 43), (51, 52)]


def normalize(text):
    text = unicodedata.normalize("NFKD", text).casefold()
    return re.sub(r"[^a-z0-9]", "", text)


def build_pages(root=ROOT):
    """Map Hebcal names to the repository's actual numbered folders."""
    pages = {}
    for number, name in enumerate(NAMES, start=1):
        folders = [p for p in (root / "WeeklyParasha").glob(f"{number:02d} - *")
                   if p.is_dir()]
        if len(folders) != 1 or not (folders[0] / "README.md").is_file():
            raise ValueError(f"Expected one folder with README.md for portion {number}")
        folder = folders[0]
        pages[normalize(name)] = [{
            "name": folder.name.split(" - ", 1)[1],
            "url": "/" + quote(folder.relative_to(root).as_posix(), safe="/") + "/",
        }]
    for first, second in DOUBLES:
        first_name, second_name = NAMES[first - 1], NAMES[second - 1]
        pages[normalize(f"{first_name}-{second_name}")] = (
            pages[normalize(first_name)] + pages[normalize(second_name)]
        )
    return pages


def upcoming_shabbat(today):
    # On Saturday, retain that day's reading until Sunday.
    return today + timedelta(days=(5 - today.weekday()) % 7)


def fetch_calendar(shabbat, israel):
    params = {"v": "1", "cfg": "json", "s": "on", "maj": "on",
              "start": shabbat.isoformat(), "end": shabbat.isoformat(),
              "i": israel, "lg": "s"}
    request = Request("https://www.hebcal.com/hebcal?" + urlencode(params),
                      headers={"User-Agent": "Parashot-GitHub-Pages"})
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return json.load(response)
        except (OSError, ValueError):
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def build_reading(calendar, shabbat, israel, pages):
    items = calendar["items"]
    if not isinstance(items, list):
        raise ValueError("Unexpected Hebcal response")
    events = [item for item in items if item.get("date") == shabbat.isoformat()]
    portions = [item for item in events if item.get("category") == "parashat"]
    data = {
        "date": shabbat.isoformat(),
        "date_label": f"{shabbat.day} {shabbat:%B %Y}",
        "cycle": "Israel" if israel == "on" else "Diaspora",
        "portions": [],
        "torah": "",
    }
    if portions:
        if len(portions) != 1:
            raise ValueError("Expected one parasha event")
        event = portions[0]
        name = event["title"].removeprefix("Parashat ")
        key = normalize(name)
        if key not in pages:
            raise ValueError(f"Unmapped Hebcal portion: {name}")
        data["portions"] = pages[key]
        data["torah"] = event.get("leyning", {}).get("torah", "")
    else:
        festivals = [item for item in events if item.get("category") == "holiday"
                     and item.get("leyning", {}).get("torah")]
        if not festivals:
            raise ValueError(f"No Torah reading returned for {shabbat}")
        data["festival"] = "; ".join(item["title"] for item in festivals)
        data["torah"] = "; ".join(item["leyning"]["torah"] for item in festivals)
    return data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--date", type=date.fromisoformat,
                        help="Override today's date (YYYY-MM-DD) for previews")
    args = parser.parse_args()
    israel = os.getenv("HEBCAL_ISRAEL", "off")
    if israel not in {"on", "off"}:
        raise ValueError("HEBCAL_ISRAEL must be 'on' or 'off'")
    today = args.date or datetime.now(
        ZoneInfo(os.getenv("SITE_TIMEZONE", "Europe/Amsterdam"))
    ).date()
    shabbat = upcoming_shabbat(today)
    data = build_reading(fetch_calendar(shabbat, israel), shabbat, israel, build_pages())
    output = ROOT / "_data" / "next_shabbat.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                      encoding="utf-8")
    print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
