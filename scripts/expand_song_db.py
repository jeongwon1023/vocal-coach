"""data/song_hints.json 확장 스크립트."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "song_hints.json"

NEW = [
    ("Stereotype", "STAYC", "STAYC Stereotype instrumental", "hiphop", "K-Pop", ["스테레오타입"]),
    ("Teddy Bear", "STAYC", "STAYC Teddy Bear instrumental", "hiphop", "K-Pop", ["테디베어"]),
    ("DASH", "NMIXX", "NMIXX DASH instrumental", "hiphop", "K-Pop", []),
    ("Love Me Like This", "NMIXX", "NMIXX Love Me Like This instrumental", "hiphop", "K-Pop", []),
    ("Sugar Rush Ride", "TXT", "TXT Sugar Rush Ride instrumental", "hiphop", "K-Pop", ["슈가러시라이드"]),
    ("In Bloom", "ZEROBASEONE", "ZEROBASEONE In Bloom instrumental", "hiphop", "K-Pop", []),
    ("Candy", "NCT DREAM", "NCT DREAM Candy instrumental", "hiphop", "K-Pop", ["캔디"]),
    ("View", "SHINee", "SHINee View MR", "hiphop", "K-Pop", ["뷰"]),
    ("HIP", "MAMAMOO", "MAMAMOO HIP instrumental", "hiphop", "K-Pop", []),
    ("Gashina", "Sunmi", "Sunmi Gashina MR", "hiphop", "K-Pop", ["가시나"]),
    ("Me After You", "Paul Kim", "Paul Kim Me After You MR", "ballad", "발라드", ["너를 만나"]),
    ("Love, Maybe", "Melomance", "Melomance Love Maybe MR", "ballad", "발라드", ["나의 만화"]),
    ("Spring Snow", "10CM", "10CM Spring Snow MR", "ballad", "발라드", []),
    ("Cruel Summer", "Taylor Swift", "Taylor Swift Cruel Summer instrumental", "hiphop", "Pop", []),
    ("Speechless", "Naomi Scott", "Speechless Aladdin instrumental", "ballad", "Pop", []),
    ("Counting Stars", "OneRepublic", "OneRepublic Counting Stars instrumental", "rock", "Pop", []),
    ("Golden", "HUNTR/X", "Golden Huntrix instrumental", "hiphop", "K-Pop", ["골든"]),
    ("APT.", "ROSÉ & Bruno Mars", "APT Rose Bruno Mars instrumental", "hiphop", "Pop", ["아파트"]),
    ("Espresso", "Sabrina Carpenter", "Sabrina Carpenter Espresso instrumental", "hiphop", "Pop", []),
    ("Nxde", "(G)I-DLE", "(G)I-DLE Nxde instrumental", "hiphop", "K-Pop", ["엑스디"]),
    ("Cupid", "FIFTY FIFTY", "FIFTY FIFTY Cupid instrumental", "hiphop", "K-Pop", ["큐피드"]),
    ("Standing Next to You", "Jungkook", "Jungkook Standing Next to You instrumental", "hiphop", "K-Pop", []),
    ("Die With A Smile", "Lady Gaga & Bruno Mars", "Die With A Smile instrumental", "ballad", "Pop", []),
    ("Beautiful Things", "Benson Boone", "Beautiful Things instrumental", "ballad", "Pop", []),
    ("비밀번호 486", "윤하", "Younha Password 486 MR", "ballad", "발라드", ["486"]),
    ("혜성", "윤하", "Younha Comet MR", "ballad", "발라드", []),
    ("좋니", "윤종신", "Yoon Jong Shin Like It MR", "ballad", "발라드", []),
    ("벚꽃 엔딩", "Busker Busker", "Busker Busker Cherry Blossom Ending MR", "ballad", "발라드", ["벚꽃"]),
    ("벌써 일년", "Brown Eyed Soul", "Brown Eyed Soul Already One Year MR", "ballad", "R&B", []),
    ("소주 한 잔", "임창정", "Im Chang Jung One Shot of Soju MR", "ballad", "발라드", []),
    ("신호등", "Lee Young Ji", "Lee Youngji Traffic Light MR", "hiphop", "K-Pop", []),
    ("Everyday", "Ariana Grande", "Ariana Grande Everyday instrumental", "hiphop", "Pop", []),
    ("Into the Unknown", "Idina Menzel", "Into the Unknown instrumental karaoke", "ballad", "Pop", []),
    ("Can You Feel the Love Tonight", "Elton John", "Can You Feel the Love Tonight instrumental", "ballad", "Pop", []),
    ("A Whole New World", "Peabo Bryson", "A Whole New World instrumental karaoke", "ballad", "Pop", []),
    ("Fly Me to the Moon", "Frank Sinatra", "Fly Me to the Moon karaoke", "ballad", "Jazz", []),
    ("River Flows in You", "Yiruma", "River Flows in You piano", "ballad", "Pop", []),
    ("Lemon", "Yonezu Kenshi", "Kenshi Yonezu Lemon instrumental", "ballad", "J-Pop", []),
    ("Pretender", "Official HIGE DANdism", "Official Hige Dandism Pretender instrumental", "rock", "J-Pop", []),
    ("Night Dancer", "imase", "imase Night Dancer instrumental", "hiphop", "J-Pop", []),
]


def main() -> None:
    data = json.loads(DB.read_text(encoding="utf-8"))
    existing = {(s["artist"], s["title"]) for s in data["songs"]}
    added = 0
    for title, artist, query, preset, genre, aliases in NEW:
        title = title.strip()
        if (artist, title) in existing:
            continue
        data["songs"].append(
            {
                "title": title,
                "artist": artist,
                "youtube_query": query,
                "style_preset": preset,
                "genre_label": genre,
                "aliases": aliases,
            }
        )
        added += 1
    DB.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"total={len(data['songs'])} added={added}")


if __name__ == "__main__":
    main()
