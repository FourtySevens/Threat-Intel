from enrichment.categorizer import categorize
from enrichment.cve_extractor import extract_cves


def enrich_article(article: dict) -> dict:
    """
    Enrich an article with tags, categories, and CVEs.
    Mutates and returns the article dict.
    """

    content = article.get("content", "")

    # Add category tags
    article.setdefault("tags", [])
    article["tags"].extend(categorize(content))

    # Add CVE tags
    article["tags"].extend(extract_cves(content))

    # Normalize / dedupe tags
    article["tags"] = sorted(set(article["tags"]))

    return article
