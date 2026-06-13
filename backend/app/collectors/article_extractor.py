import trafilatura

def extract_article(url):

    downloaded = trafilatura.fetch_url(url)

    if not downloaded:
        return ""

    text = trafilatura.extract(downloaded)

    return text or ""