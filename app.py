from flask import Flask, request, render_template_string, send_from_directory
from geopy.geocoders import Nominatim
import time
import os

@app.route("/signup", methods=["POST"])
def signup():
    print(request.json)
    return "ok"


app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ==============================
# トップページ
# ==============================
@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "signup.html")

# ==============================
# JS / CSS 配信
# ==============================
@app.route("/<path:filename>")
def static_files(filename):
    if filename.endswith((".js", ".css")):
        return send_from_directory(BASE_DIR, filename)
    return "", 404

# ==============================
# Geocoder
# ==============================
geolocator = Nominatim(user_agent="jp_render_single_file_app")

# ==============================
# 全体レート制限（IP無関係）
# ==============================
RATE_LIMIT = 10
RATE_WINDOW = 60
request_times = []

def is_rate_limited_global():
    now = time.time()
    while request_times and now - request_times[0] > RATE_WINDOW:
        request_times.pop(0)
    if len(request_times) >= RATE_LIMIT:
        return True
    request_times.append(now)
    return False

# ==============================
# 日本向け住所パース
# ==============================
def parse_japanese_address(address):
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
# 結果HTML
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
# API
# ==============================
@app.route("/signup", methods=["POST"])
def signup():

    if is_rate_limited_global():
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

    return render_template_string(
        HTML_OK,
        nickname=nickname,
        prefecture=prefecture,
        city=city,
        ward=ward
    )
