import streamlit as st
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from collections import Counter
import re

# Optional: Playwright/Selenium imports (only if used)
# from playwright.sync_api import sync_playwright

st.set_page_config(page_title="Web Audit Tool", layout="wide")

st.title("🕷️ Web Audit Tool")
st.markdown("A 5-step audit tool for analyzing a website's crawlability, content, JS/API dependencies, and more.")

# Step 1 – Crawlability Specialist
st.header("🔍 Step 1: Crawlability Analysis")

def analyze_robots_txt(url):
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    try:
        response = requests.get(robots_url, timeout=10)
        lines = response.text.splitlines()
        allowed = []
        disallowed = []
        crawl_delay = None
        sitemaps = []

        for line in lines:
            line = line.strip()
            if line.startswith("Allow:"):
                allowed.append(line.split(":")[1].strip())
            elif line.startswith("Disallow:"):
                disallowed.append(line.split(":")[1].strip())
            elif line.lower().startswith("crawl-delay:"):
                crawl_delay = line.split(":")[1].strip()
            elif line.lower().startswith("sitemap:"):
                sitemaps.append(line.split(":")[1].strip())

        return {
            "allowed": allowed,
            "disallowed": disallowed,
            "crawl_delay": crawl_delay,
            "sitemaps": sitemaps,
            "status": "Success"
        }
    except Exception as e:
        return {"status": f"Error: {str(e)}"}

url = st.text_input("Enter the website URL (e.g., https://example.com)", "https://example.com")

if st.button("Analyze"):
    if not url.startswith("http"):
        st.error("Please enter a valid URL.")
    else:
        with st.spinner("Fetching and analyzing robots.txt..."):
            robots_data = analyze_robots_txt(url)
        if robots_data["status"] == "Success":
            st.success("Crawlability analysis completed.")
            st.subheader("Crawlability Rules")
            st.write("**Allowed Paths:**", robots_data["allowed"] or "None")
            st.write("**Disallowed Paths:**", robots_data["disallowed"] or "None")
            st.write("**Crawl Delay:**", robots_data["crawl_delay"] or "Not specified")
            st.write("**Sitemaps:**", robots_data["sitemaps"] or "Not found")
        else:
            st.error(robots_data["status"])

# Step 2 – Content Extractor
st.header("📄 Step 2: Content Extraction")

def extract_content(url):
    try:
        session = requests.Session()
        response = session.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        titles = [t.get_text(strip=True) for t in soup.find_all(['h1', 'h2'])]
        links = [a['href'] for a in soup.find_all('a', href=True)]
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc["content"] if meta_desc else "No meta description found."
        return {
            "titles": titles,
            "description": description,
            "links": links[:10]  # Limit output for clarity
        }
    except Exception as e:
        return {"error": str(e)}

if st.button("Extract Content"):
    with st.spinner("Extracting page content..."):
        content = extract_content(url)
    if "error" in content:
        st.error(f"Extraction failed: {content['error']}")
    else:
        st.success("Content extracted.")
        st.write("**Meta Description:**", content["description"])
        st.write("**Titles Found:**", content["titles"])
        st.write("**Sample Links:**", content["links"])

# Step 3 – JS & API Handler
st.header("⚙️ Step 3: JS & API Detection")

def detect_js_and_apis(url):
    result = {"js_detected": False, "rss": [], "api_keywords": []}
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, "html.parser")
        scripts = soup.find_all("script")
        result["js_detected"] = len(scripts) > 5

        result["rss"] = [link['href'] for link in soup.find_all("link", type="application/rss+xml")]

        api_keywords = re.findall(r"https?://[^\s\"']+/api/[^\s\"']+", r.text)
        result["api_keywords"] = list(set(api_keywords))
    except:
        result["error"] = "Failed to check JS/API usage."
    return result

if st.button("Check JS/API"):
    with st.spinner("Analyzing JS and APIs..."):
        jsapi = detect_js_and_apis(url)
    if "error" in jsapi:
        st.error(jsapi["error"])
    else:
        st.success("JS/API analysis done.")
        st.write("**JavaScript Heavy Site?**", "Yes" if jsapi["js_detected"] else "No")
        st.write("**RSS Feeds Found:**", jsapi["rss"] or "None")
        st.write("**API-like URLs Found:**", jsapi["api_keywords"] or "None")

# Step 4 – Visual & Report Designer
st.header("📊 Step 4: Dashboard & Recommendations")

if url:
    st.subheader("📈 Summary")
    st.metric("Allowed Paths", len(robots_data.get("allowed", [])))
    st.metric("Disallowed Paths", len(robots_data.get("disallowed", [])))
    st.metric("JS Scripts", "Yes" if jsapi.get("js_detected") else "No")
    st.metric("API Endpoints", len(jsapi.get("api_keywords", [])))

    st.subheader("🛠️ Recommendations")
    recs = []
    if robots_data.get("crawl_delay"):
        recs.append("Respect the crawl-delay directive.")
    if jsapi.get("js_detected"):
        recs.append("Consider using Playwright or Selenium for dynamic rendering.")
    if jsapi.get("rss"):
        recs.append("Use RSS feed for structured data extraction.")
    if jsapi.get("api_keywords"):
        recs.append("Check if API requires auth, then crawl via API.")
    st.write(recs if recs else "No major recommendations.")

# Step 5 – Documentation & Deployment
st.header("📘 Step 5: Documentation & Deployment")
st.markdown("""
**Deployment Notes**
- You can deploy this app to [Streamlit Cloud](https://streamlit.io/cloud).
- Clone this repo and run locally using `streamlit run app.py`.

**README Sections Suggestion:**
- Overview
- Installation
- Usage
- Sample Output Screenshots
- Crawlability Recommendations
- Visual Sitemap (if generated)

**Future Features:**
- Visual sitemap generation
- Pagination handling
- Full Playwright/Selenium headless support
""")
