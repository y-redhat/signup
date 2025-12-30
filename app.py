from flask import Flask, request, render_template_string
from geopy.geocoders import Nominatim
import time

from flask import Flask, send_from_directory

app = Flask(__name__, static_folder="static")

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


app = Flask(__name__)

# ==============================
# Geocoder
# ==============================
geolocator = Nominatim(user_agent="jp_render_single_file_app")

# ==============================
# 全体レート制限（IP無関係）
# ==============================
RATE_LIMIT = 10      # 1分あたり最大処理数
RATE_WINDOW = 60     # 秒
request_times = []   # 全リクエストの時刻を保存

def is_rate_limited_global() -> bool:
    now = time.time()

    # 60秒より古い記録を削除
    while request_times and now - request_times[0] > RATE_WINDOW:
        request_times.pop(0)

    # 制限超過なら処理しない
    if len(request_times) >= RATE_LIMIT:
        return True

    # 記録
    request_times.append(now)
    return False


# ==============================
# 日本向け住所パース
# ==============================
def parse_japanese_address(address: dict):
    prefecture = address.get("state") or address.get("province") or ""
    city = (
        address.get("city")
        or address.get("county")
        or address.get("town")
        or address.get("village")
        or ""
    )
    ward = address.get("suburb") or address.get("neighbourhood") or ""
    return prefecture, city, ward


# ==============================
# HTML
# ==============================
HTML_OK = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>登録完了</title>
</head>
<body>
<h2>登録完了</h2>
<p>{{ nickname }} さん</p>
<p>位置: {{ prefecture }} {{ city }} {{ ward }}</p>
</body>
</html>
"""

HTML_LIMIT = """
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<title>制限中</title>
</head>
<body>
<h2>アクセス制限中</h2>
<p>現在リクエストが集中しています。少し待ってから再試行してください。</p>
</body>
</html>
"""


# ==============================
# エンドポイント
# ==============================
@app.route("/signup", methods=["POST"])
def signup():

    # ---- 全体レート制限 ----
    if is_rate_limited_global():
        print("[BLOCKED] global rate limit exceeded")
        return render_template_string(HTML_LIMIT), 429

    data = request.get_json(force=True)

    nickname = data.get("nickname", "ゲスト")
    lat = data.get("latitude")
    lon = data.get("longitude")

    prefecture = city = ward = "未取得"

    if lat is not None and lon is not None:
        try:
            location = geolocator.reverse(
                f"{lat}, {lon}",
                language="ja",
                timeout=10
            )
            if location:
                address = location.raw.get("address", {})
                prefecture, city, ward = parse_japanese_address(address)
        except Exception as e:
            print("住所取得エラー:", e)

    print("[OK]", nickname, prefecture, city, ward)

    return render_template_string(
        HTML_OK,
        nickname=nickname,
        prefecture=prefecture,
        city=city,
        ward=ward
    )


# ==============================
# 起動
# ==============================
if __name__ == "__main__":
    app.run(debug=True, port=5000)
