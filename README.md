# redhead-reviews

[REDHEAD（東京湾の釣り船）](https://redhead-marine.com/) のサイトに表示する、Googleの口コミの評価と件数。

- `reviews.json` を毎日 6:05（日本時間）ごろに GitHub Actions が更新する（`update.py`）
- 取得元は Google の Places API。鍵は秘密の設定 `GOOGLE_PLACES_API_KEY`
- サイトはこのファイルを読み込んで表示する。読めないときはサイトに書いてある数字のまま
