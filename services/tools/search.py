from duckduckgo_search import DDGS

def run(query:str):

    results = []

    with DDGS() as ddgs:
        for r in ddgs.text(
            query,
            max_results=5
        ):
            results.append({
                "title": r["title"],
                "url": r["href"],
                "snippet": r["body"]
            })

    return results