"""
Morning Digest — News Fetcher
Fetches news from reputable academic and practitioner sources for each topic,
then uses the Anthropic API to generate practical takeaways for each article.

Requires: ANTHROPIC_API_KEY environment variable (set as a GitHub secret).
"""

import json
import os
import re
import time
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

# ── Topics & Queries ───────────────────────────────────────────────────────────
# Each query is targeted at reputable sources via search terms.
# The TRUSTED_DOMAINS list acts as a post-fetch filter.

TOPICS = [
    {
        "id": "ai_literacy",
        "label": "AI Literacy & Capability",
        "emoji": "🤖",
        "description": "Critical capabilities needed to become AI fluent — frameworks, competencies, and workforce readiness.",
        "queries": [
            "AI literacy competency framework workforce research",
            "AI fluency critical capabilities employees upskilling",
            "artificial intelligence literacy skills assessment framework 2025",
        ],
    },
    {
        "id": "org_psych_ai",
        "label": "AI & Organisational Psychology",
        "emoji": "🏢",
        "description": "Impact of AI on wellbeing, engagement, job crafting, trust, and other org psych constructs.",
        "queries": [
            "AI impact employee wellbeing organizational psychology research",
            "artificial intelligence workplace engagement psychological research",
            "AI adoption employee job crafting wellbeing empirical study",
        ],
    },
    {
        "id": "behaviour_change",
        "label": "Behavioural Change Frameworks",
        "emoji": "🔄",
        "description": "Evidence-based frameworks for driving behaviour change — in the context of AI adoption and workforce transformation.",
        "queries": [
            "behavioural change framework workplace AI adoption research",
            "behavior change model employee technology adoption COM-B nudge",
            "behavioural science AI upskilling habit formation organizational research",
        ],
    },
    {
        "id": "fun_research",
        "label": "Fascinating Psychology Research",
        "emoji": "🧩",
        "description": "Surprising, counterintuitive, and delightful findings from personality and behaviour research — the kind of study you'd share at dinner.",
        "queries": [
            "surprising personality trait correlation behaviour study psychology journal",
            "unexpected psychology research finding personality daily life habits",
            "personality differences quirky study cognitive behavior psychology 2024 2025",
        ],
    },
    {
        "id": "psych_safety",
        "label": "Psychological Safety",
        "emoji": "🛡️",
        "description": "Research on psychological safety and its role in team learning, AI experimentation, and innovation.",
        "queries": [
            "psychological safety AI workplace innovation team performance research",
            "psychological safety learning behavior empirical study 2025",
            "Amy Edmondson psychological safety leadership research",
        ],
    },
]

MAX_ARTICLES_PER_TOPIC = 6

# ── Trusted Sources ────────────────────────────────────────────────────────────
# Articles from these domains are preferred. Others are filtered out.

TRUSTED_DOMAINS = {
    # Academic journals & databases
    "ncbi.nlm.nih.gov", "pubmed.ncbi.nlm.nih.gov", "pmc.ncbi.nlm.nih.gov",
    "frontiersin.org", "sciencedirect.com", "apa.org", "psycnet.apa.org",
    "springer.com", "link.springer.com", "tandfonline.com", "jstor.org",
    "nature.com", "wiley.com", "onlinelibrary.wiley.com",
    "bera-journals.onlinelibrary.wiley.com",
    "sagepub.com", "journals.sagepub.com", "cambridge.org",
    "arxiv.org", "ssrn.com",
    # Universities
    "mit.edu", "stanford.edu", "harvard.edu", "ox.ac.uk",
    "lse.ac.uk", "ucl.ac.uk", "cam.ac.uk", "yale.edu", "columbia.edu",
    # Top practitioner / consultancy
    "mckinsey.com", "hbr.org", "deloitte.com", "pwc.com",
    "bcg.com", "weforum.org", "oecd.org", "brookings.edu",
    # People, HR & behavioural science
    "shrm.org", "cipd.org", "gallup.com",
    "irrationallabs.com",          # Dan Ariely's behavioural lab
    "ailiteracy.institute",
    "fastcompany.com",
    "thehappyworkplace.org.uk",
    "thehrdigest.com",
    # Psychology science journalism (report on peer-reviewed studies)
    "psypost.org",                 # covers academic psychology research
    "sciencedaily.com",            # press releases from universities/journals
    "bps.org.uk",                  # British Psychological Society
    "psychologicalscience.org",    # Association for Psychological Science
    "digest.bps.org.uk",           # BPS Research Digest
    # Government / IGO
    "eda.gov", "dol.gov", "ec.europa.eu",
}


def domain_of(url: str) -> str:
    try:
        host = urllib.parse.urlparse(url).netloc.lower()
        return host.lstrip("www.")
    except Exception:
        return ""


def is_trusted(source_url: str) -> bool:
    """Check the publisher's URL (from the RSS <source url="..."> attribute), not the Google redirect link."""
    d = domain_of(source_url)
    return any(d == td or d.endswith("." + td) for td in TRUSTED_DOMAINS)


# ── RSS Fetcher ────────────────────────────────────────────────────────────────

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"


def fetch_rss(query: str) -> list[dict]:
    url = GOOGLE_NEWS_RSS.format(query=urllib.parse.quote(query))
    req = urllib.request.Request(
        url, headers={"User-Agent": "Mozilla/5.0 (compatible; MorningDigest/1.0)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
        root = ET.fromstring(raw)
        items = []
        for item in root.findall(".//item"):
            title_el = item.find("title")
            link_el  = item.find("link")
            pub_el   = item.find("pubDate")
            src_el   = item.find("source")
            desc_el  = item.find("description")

            title      = (title_el.text  or "").strip()
            link       = (link_el.text   or "").strip()
            pub        = (pub_el.text    or "").strip()
            source     = (src_el.text    or "").strip()
            # The publisher's actual domain is the 'url' attribute on <source>
            source_url = (src_el.get("url") or "") if src_el is not None else ""
            desc       = re.sub(r"<[^>]+>", "", desc_el.text or "").strip()

            items.append({
                "title":      title,
                "url":        link,
                "source":     source,
                "source_url": source_url,   # used for trusted-domain filtering
                "pubDate":    pub,
                "snippet":    desc[:300],
            })
        return items
    except Exception as e:
        print(f"    ⚠ RSS fetch failed for '{query}': {e}")
        return []


def dedup(articles: list[dict]) -> list[dict]:
    seen = set()
    out = []
    for a in articles:
        key = re.sub(r"\s+", " ", a["title"].lower()[:70])
        if key not in seen:
            seen.add(key)
            out.append(a)
    return out


# ── Anthropic Summariser ───────────────────────────────────────────────────────

SYSTEM_PROMPT = (
    "You are a research assistant for an organisational psychologist who specialises "
    "in helping employees develop AI capabilities. Given an article's title, snippet, "
    "and topic category, generate 2–3 concise responses tailored to the topic type:\n\n"
    "- For practical topics (AI literacy, org psych, behaviour change, psychological safety): "
    "extract specific, actionable takeaways they can act on in their work. "
    "Each must be concrete — not a restatement of the title.\n\n"
    "- For 'fun_research' (fascinating/quirky psychology studies): write 2–3 short, engaging "
    "observations — why the finding is surprising, and one practical implication or "
    "conversation-starter it offers for their work with people and teams.\n\n"
    "Format: a JSON array of strings, e.g. [\"Point 1.\", \"Point 2.\"]"
)


def get_takeaways(title: str, snippet: str, api_key: str, topic_id: str = "") -> list[str]:
    """Call claude-haiku via the Anthropic Messages API and return takeaway strings."""
    payload = {
        "model": "claude-haiku-4-5-20251001",
        "max_tokens": 300,
        "system": SYSTEM_PROMPT,
        "messages": [
            {
                "role": "user",
                "content": (
                    f"Topic category: {topic_id}\n"
                    f"Article title: {title}\n\n"
                    f"Snippet: {snippet or '(no snippet available)'}"
                ),
            }
        ],
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=data,
        headers={
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = json.loads(resp.read())
        text = body["content"][0]["text"].strip()
        # Extract JSON array from response
        match = re.search(r"\[.*?\]", text, re.DOTALL)
        if match:
            return json.loads(match.group())
        # Fallback: split on newlines
        lines = [l.strip("•–- ").strip() for l in text.splitlines() if l.strip()]
        return lines[:3]
    except Exception as e:
        print(f"    ⚠ Anthropic API error: {e}")
        return []


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        print("✓ Anthropic API key found — AI-powered takeaways enabled")
    else:
        print("⚠ No ANTHROPIC_API_KEY — takeaways will use article snippets only")

    print(f"\nMorning Digest — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "topics": [],
    }

    for topic in TOPICS:
        print(f"{topic['emoji']}  {topic['label']}")
        raw = []
        for q in topic["queries"]:
            print(f"   → {q}")
            raw.extend(fetch_rss(q))
            time.sleep(0.5)   # be polite to Google

        # Filter to trusted sources only — use the publisher URL, not the Google redirect link
        trusted = [a for a in raw if is_trusted(a.get("source_url", ""))]
        print(f"   {len(raw)} found → {len(trusted)} from trusted sources")

        articles = dedup(trusted)[:MAX_ARTICLES_PER_TOPIC]

        # Generate practical takeaways via Anthropic API
        for art in articles:
            if api_key:
                print(f"   📝 Summarising: {art['title'][:60]}…")
                art["takeaways"] = get_takeaways(art["title"], art["snippet"], api_key, topic["id"])
                time.sleep(0.3)
            else:
                art["takeaways"] = []

        result["topics"].append({
            "id":          topic["id"],
            "label":       topic["label"],
            "emoji":       topic["emoji"],
            "description": topic["description"],
            "articles":    articles,
        })

        total = sum(len(t["articles"]) for t in result["topics"])
        print()

    with open("articles.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    total = sum(len(t["articles"]) for t in result["topics"])
    print(f"✅  Saved articles.json — {total} articles across {len(TOPICS)} topics")


if __name__ == "__main__":
    main()
