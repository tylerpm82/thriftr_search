from flask import Flask, request, render_template_string
from supabase import create_client, Client
from math import radians, cos, sin, sqrt, atan2
import requests

# -------------------- Configuration --------------------

# Supabase
SUPABASE_URL = "https://dpubxmdntecwomzfhfqr.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRwdWJ4bWRudGVjd29temZoZnFyIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDE3MTkzOTAsImV4cCI6MjA1NzI5NTM5MH0.rd5a7HWNFOiLwedvZdS0pv1p-_zFC6jztV6K4bZU1MM"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Geocoding API (OpenCage)
GEOCODE_KEY = "c5d9b8a5c0694099a9cf2654fab69be3"  # Or use Google if you prefer

# Flask
app = Flask(__name__)

# -------------------- Utility Functions --------------------

def geocode_address(address):
    url = f"https://api.opencagedata.com/geocode/v1/json?q={address}&key={GEOCODE_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()["results"]
        if results:
            coords = results[0]["geometry"]
            return coords["lat"], coords["lng"]
    return None, None

def haversine(lat1, lon1, lat2, lon2):
    R = 3958.8  # Earth radius in MILES
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c  # result in miles


def get_closest_stores(user_lat, user_lng, count=10, filter_by='both'):
    data = supabase.table("locations").select("*").execute()
    if not data.data:
        return []

    distances = []
    for place in data.data:
        if filter_by != 'both' and place.get("type") != filter_by:
            continue  # skip non-matching types

        store_lat = place.get("latitude")
        store_lng = place.get("longitude")
        if store_lat and store_lng:
            dist = haversine(user_lat, user_lng, store_lat, store_lng)
            distances.append((dist, place))

    distances.sort(key=lambda x: x[0])
    return distances[:count]

# -------------------- Flask Routes --------------------

@app.route('/', methods=['GET', 'POST'])
def index():
    results_html = ""
    if request.method == 'POST':
        address = request.form['address']
        store_filter = request.form.get('filter', 'both')
        lat, lng = geocode_address(address)
        
        if lat and lng:
            nearest = get_closest_stores(lat, lng, filter_by = store_filter)
            results_html = "<h3>Nearest Thrift Stores:</h3><ul>"
            for dist, store in nearest:
                results_html += f"<li><b>{store['name']}</b><br>{store['address']}<br>📍 {round(dist, 2)} miles away</li>"
            results_html += "</ul>"
        else:
            results_html = "<p style='color:red;'>Could not geocode that address.</p>"

    return render_template_string(f'''
<html>
<head>
    <title>Find Nearby Thrift Stores</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f1f1f1;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            height: 100vh;
        }}
        .container {{
            margin-top: 60px;
            background: white;
            padding: 30px 40px;
            border-radius: 12px;
            box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            max-width: 600px;
            width: 90%;
        }}
        h2 {{
            text-align: center;
            color: #333;
        }}
        form {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
        }}
        input[type=text] {{
            padding: 10px;
            width: 100%;
            max-width: 350px;
            font-size: 16px;
            border-radius: 6px;
            border: 1px solid #ccc;
        }}
        input[type=submit] {{
            padding: 10px 16px;
            background-color: #E3A87B;
            border: none;
            color: white;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
        }}
        ul {{
            list-style-type: none;
            padding-left: 0;
        }}
        li {{
            margin-bottom: 15px;
            background: #f8f8f8;
            padding: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        }}
        li b {{
            font-size: 18px;
            color: #E3A87B;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h2>🧭 Find Thrift Stores Near You</h2>
        <form method="POST">
    <input type="text" name="address" placeholder="Enter your address..." required>
    <select name="filter" style="padding: 10px; border-radius: 6px;">
        <option value="both">All</option>
        <option value="thrift_store">Thrift Stores Only</option>
        <option value="coffee_shop">Coffee Shops Only</option>
    </select>
    <input type="submit" value="Search">
</form>

        {results_html}
    </div>
</body>
</html>
''')


# -------------------- Run App --------------------

if __name__ == '__main__':
    import os

    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

