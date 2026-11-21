# -*- coding: utf-8 -*-
"""REDHEAD の Googleの口コミ（評価と件数）を取ってきて reviews.json に書く。毎日 GitHub Actions で動く。

- 鍵は GitHub の秘密の設定 GOOGLE_PLACES_API_KEY（無ければ何もせずに終わる）
- 店の特定は Text Search（初回）。PLACE_ID が分かったら reviews.json に残し、次からは Place Details で取る
- 数字がおかしい時（評価が1〜5の外・件数が0・別の店）は書き換えずに失敗で止める
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

KEY = os.environ.get("GOOGLE_PLACES_API_KEY", "").strip()
PATH = "reviews.json"
QUERY = "REDHEAD 千葉県市川市高谷新町16-1"
NAMES = ("REDHEAD", "レッドヘッド")


def call(url, body=None, mask=""):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body else None,
                                 method="POST" if body else "GET")
    req.add_header("X-Goog-Api-Key", KEY)
    req.add_header("X-Goog-FieldMask", mask)
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main():
    if not KEY:
        print("GOOGLE_PLACES_API_KEY が未登録なので、今回は何もしません")
        return
    old = json.load(open(PATH, encoding="utf-8"))
    pid = old.get("place_id")
    if pid:
        p = call(f"https://places.googleapis.com/v1/places/{pid}", mask="id,displayName,rating,userRatingCount")
    else:
        res = call("https://places.googleapis.com/v1/places:searchText", {"textQuery": QUERY, "languageCode": "ja"},
                   mask="places.id,places.displayName,places.rating,places.userRatingCount,places.formattedAddress")
        cands = [x for x in res.get("places", []) if any(n.lower() in x.get("displayName", {}).get("text", "").lower() for n in NAMES)]
        if not cands:
            sys.exit(f"REDHEAD が見つかりません: {json.dumps(res, ensure_ascii=False)[:500]}")
        p = cands[0]
        print("見つけた店:", p.get("displayName", {}).get("text"), p.get("formattedAddress"), p["id"])

    name = p.get("displayName", {}).get("text", "")
    rating, count = p.get("rating"), p.get("userRatingCount")
    # 検算：別の店・ありえない値なら書き換えない
    if not any(n.lower() in name.lower() for n in NAMES):
        sys.exit(f"店の名前が違います: {name}")
    if not isinstance(rating, (int, float)) or not 1 <= rating <= 5:
        sys.exit(f"評価がおかしい: {rating}")
    if not isinstance(count, int) or count <= 0:
        sys.exit(f"件数がおかしい: {count}")
    if old.get("count") and count < old["count"] - 5:
        sys.exit(f"件数が急に減りました: {old['count']} → {count}（取り違えの可能性）")

    now = datetime.now(timezone(timedelta(hours=9)))
    new = {"rating": round(float(rating), 1), "count": count, "place_id": p["id"], "name": name,
           "updated": now.strftime("%Y-%m-%d"), "updated_label": f"{now.year}年{now.month}月{now.day}日時点",
           "source": "Google（Places API）"}
    json.dump(new, open(PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"★{new['rating']}・{count}件（前回 ★{old.get('rating')}・{old.get('count')}件）")


if __name__ == "__main__":
    main()
