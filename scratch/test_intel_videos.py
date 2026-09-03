import requests

urls = [
    "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/person-bicycle-car-detection.mp4",
    "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/car-detection.mp4",
    "https://raw.githubusercontent.com/intel-iot-devkit/sample-videos/master/head-pose-face-detection.mp4",
    "https://vjs.zencdn.net/v/oceans.mp4"
]

for url in urls:
    try:
        r = requests.head(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=5)
        print(f"URL: {url}")
        print(f"  Status: {r.status_code} | Content-Type: {r.headers.get('content-type')} | Access-Control-Allow-Origin: {r.headers.get('access-control-allow-origin')}\n")
    except Exception as e:
        print(f"URL: {url} -> ERROR: {e}\n")
