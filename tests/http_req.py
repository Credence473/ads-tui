import httpx

headers = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0 Safari/537.36"
    )
}

url = "https://academic.oup.com/mnras/pdf-lookup/doi/10.1111/j.1365-2966.2009.16077.x"

with httpx.Client(
    headers=headers,
    follow_redirects=True,
    timeout=60,
) as client:
    r = client.get(url)

print(r.status_code)
print(r.headers)
print(r.text[:500])
