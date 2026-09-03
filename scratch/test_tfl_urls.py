import requests

tfl_urls = [
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01401.mp4",
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01402.mp4",
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01403.mp4",
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01404.mp4",
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01405.mp4",
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01406.mp4",
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01407.mp4",
    "https://s3-eu-west-1.amazonaws.com/jamcams.tfl.gov.uk/00001.01408.mp4"
]

for url in tfl_urls:
    try:
        r = requests.head(url, headers={"User-Agent": "Mozilla/5.0"}, allow_redirects=True, timeout=5)
        print(f"TfL URL: {url} -> Status: {r.status_code} | Content-Type: {r.headers.get('content-type')}")
    except Exception as e:
        print(f"TfL URL: {url} -> ERROR: {e}")
