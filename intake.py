import json
import multiprocessing
import multiprocessing.process
import sqlite3
import time
import feedparser
import requests
import os
import psycopg2
from psycopg2 import sql
from jetstream import jetstream
from hashlib import sha256
from base64 import urlsafe_b64encode
import pypandoc
import mimetypes
import re
from bs4 import BeautifulSoup

# Database connection
DB_PARAMS = {
    "dbname": "cybercanary",
    "user": "zack_db",
    "password": "test",
    "host": "127.0.0.1",
    "port": "5432"
}

def get_db_connection():
    return psycopg2.connect(**DB_PARAMS)

def add_to_queue(data, task):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        INSERT INTO queue (data, task) VALUES (%s, %s)
    ''', (data, task))
    
    conn.commit()
    cursor.close()
    conn.close()

def post_exists(cid):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM posts WHERE uid = %s", (cid,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists


# Function to download HTML of linked websites
def get_extension(content_type, url):
    """Determine file extension from Content-Type header or URL."""
    if content_type:
        ext = mimetypes.guess_extension(content_type.split(";")[0])
        if ext:
            return ext
    
    # Fallback: Try to guess from URL
    ext = os.path.splitext(url)[-1]
    return ext if ext else ".bin"  # Default to .bin if unknown

def extract_main_content(html):
    """Extracts the main content from an HTML page, removing headers, footers, sidebars, and scripts."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove unwanted elements
    for tag in soup(["script", "style", "aside", "nav", "footer", "header", "form", "iframe"]):
        tag.decompose()

    # Try to find main content
    main_content = soup.find("article") or soup.body
    
    return main_content.get_text(separator="\n") if main_content else soup.get_text(separator="\n")

def clean_markdown(md_content):
    """Remove images and unnecessary blocks from Markdown."""
    # Remove images (Markdown format: ![alt](url) or ![](url))
    md_content = re.sub(r"!\[.*?\]\(.*?\)", "", md_content)
    
    # Remove block sections starting with ':::'
    md_content = re.sub(r"^:::.*?$", "", md_content, flags=re.MULTILINE)
    
    return md_content.strip()

def download_url(link: str, folder: str):
    if not os.path.exists(folder):
        os.makedirs(folder)

    filename_base = urlsafe_b64encode(link.encode()).decode()
    
    try:
        response = requests.get(link, stream=True)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")
        ext = get_extension(content_type, link)
        filename = os.path.join(folder, f"{filename_base}{ext}")

        if "text" in content_type or "html" in content_type:
            # Convert to Markdown if pypandoc can handle it
            try:
                main_text = extract_main_content(response.text)

                md_content = pypandoc.convert_text(main_text, "md", format="html")
                md_content = clean_markdown(md_content)
                filename = os.path.join(folder, f"{filename_base}.md")
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(md_content)
            except Exception as e:
                print(f"Error converting text to Markdown: {e}")
                with open(filename, "w", encoding="utf-8") as file:
                    file.write(response.text)  # Fallback: Save as raw text
        else:
            # Save binary content (images, videos, etc.)
            with open(filename, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)

        return filename
    except Exception as e:
        print(f"Error downloading URL: {e}")
        return None

# Function to clean and store data
def clean_and_store_post(post):
    # print(post)

    cid = post.get("commit", {}).get("cid", "")
    if not cid or post_exists(cid):
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()

    extracted_info = extract_bsky_post_info(post)

    text = post.get("commit", {}).get("record", {}).get("text", "")
    media_urls = [facet["features"][0]["uri"] for facet in post.get("commit", {}).get("record", {}).get("facets", []) if "uri" in facet["features"][0]]
    media_files = [download_url(url, "media") for url in media_urls if url]
    
    links = [word for word in text.split() if word.startswith("http")]
    external_uri = extracted_info.get("external_uri")
    if external_uri:
        links.append(external_uri)
    html_snapshots = [download_url(link, "html") for link in links]
    
    text = post.get("commit", {}).get("record", {}).get("text", "")
    media_files = json.dumps([])
    html_snapshots = json.dumps([download_url(link, "html") for link in text.split() if link.startswith("http")])
    
    cursor.execute(
        "INSERT INTO posts (source, uid, content, media, html_snapshot) VALUES (%s, %s, %s, %s, %s)",
        ("bluesky", cid, json.dumps(extracted_info), media_files, html_snapshots)
    )
    
    add_to_queue(cid, "ai-filter-for-threats")
    print("BSKY:", extracted_info)
    conn.commit()
    cursor.close()
    conn.close()


# RSS feed fetching
def fetch_rss_feeds():
    feeds = [
        # "https://www.darkreading.com/rss.xml",
        "https://krebsonsecurity.com/feed/",
        "https://threatpost.com/feed/",
        "https://hnrss.org/newest",
        "https://feeds.feedburner.com/TheHackersNews",
        "https://www.grahamcluley.com/feed/",
        "https://www.schneier.com/blog/atom.xml",
        "https://www.csoonline.com/feed/",
        "https://www.darkreading.com/rss/all.xml",
        "https://www.troyhunt.com/rss/",
        "http://feeds.feedburner.com/eset/blog",
        "https://news.sophos.com/en-us/feed/",
        "https://www.infosecurity-magazine.com/rss/news/"
    ]
    
    for feed_url in feeds:
        multiprocessing.Process(target=rss_get, args=(feed_url,)).start()

def rss_get(feed_url):
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        store_rss_post(entry)


# Function to check if an RSS post exists
def rss_post_exists(link):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM posts WHERE uid = %s", (link,))
    exists = cursor.fetchone() is not None
    cursor.close()
    conn.close()
    return exists

def clean_rss(entry):
    new_entry = {}

    keep_fields = ['title', 'link', 'author', 'published', 'summary', 'tags', 'id']

    for field in keep_fields:
        if field in entry:
            new_entry[field] = entry[field]

    return new_entry

# Function to clean and store RSS posts
def store_rss_post(entry):
    link = entry['link']
    entry = clean_rss(entry)

    if rss_post_exists(link):
        return
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    
    html_snapshot = [download_url(link, "html")]
    cursor.execute("INSERT INTO posts (source, uid, content, html_snapshot) VALUES (%s, %s, %s, %s)",
                   ("rss", link, json.dumps(entry), json.dumps(html_snapshot)))
    
    print("RSS:", entry['title'], entry['link'])
    add_to_queue(link, "ai-filter-for-threats")

    conn.commit()
    cursor.close()
    conn.close()

def bsky_thumb(did, blob_id):
    return f"https://cdn.bsky.app/img/feed_thumbnail/plain/{did}/{blob_id}"

def extract_bsky_post_info(post_data):
    """
    Extracts relevant information from a Bluesky post data dictionary, including thumbnails.

    Args:
        post_data: A dictionary representing a Bluesky post.

    Returns:
        A dictionary containing extracted information.
    """

    extracted_info = {}

    try:
        commit = post_data.get('commit')
        if commit:
            record = commit.get('record')
            if record:
                extracted_info['text'] = record.get('text', None)
                extracted_info['created_at'] = record.get('createdAt', None)
                extracted_info['langs'] = record.get('langs', [])

                if record.get('embed') and record['embed'].get('external'):
                    external_embed = record['embed']['external']
                    extracted_info['external_title'] = external_embed.get('title', None)
                    extracted_info['external_description'] = external_embed.get('description', None)
                    extracted_info['external_uri'] = external_embed.get('uri', None)

                    if external_embed.get('thumb'):
                        thumb = external_embed['thumb']
                        if thumb.get('$type') == 'blob' and thumb.get('ref') and thumb['ref'].get('$link'):
                            extracted_info['thumb_blob_cid'] = thumb['ref']['$link']
                            extracted_info['thumb_mime_type'] = thumb.get('mimeType')
                            extracted_info['thumb_size'] = thumb.get('size')

                facets = record.get('facets', [])
                tags = []
                for facet in facets:
                    for feature in facet.get('features', []):
                        if feature.get('$type') == 'app.bsky.richtext.facet#tag':
                            tags.append(feature.get('tag'))
                extracted_info['tags'] = tags

        extracted_info['cid'] = commit.get('cid', None) if commit else None
        extracted_info['did'] = post_data.get('did', None)

    except (AttributeError, KeyError, TypeError) as e:
        print(f"Error extracting data: {e}")
        return None

    return extracted_info

def bsky_thumb(did, thumb_blob_cid):
    """
    Generates a thumbnail URL given a DID and blob CID.

    Args:
        did: The DID of the user.
        thumb_blob_cid: The blob CID of the thumbnail.

    Returns:
        The thumbnail URL, or None if the input is invalid.
    """
    if did and thumb_blob_cid:
        # Construct the thumbnail URL. Replace with your actual implementation.
        # This is a placeholder, as the actual URL structure may vary.
        return f"https://example.com/thumb/{did}/{thumb_blob_cid}"
    else:
        return None

def process_bsky_data(data):
    """
    Processes a Bluesky post dictionary and prints the extracted information, including thumbnail URL.

    Args:
        data: A dictionary representing a Bluesky post.
    """
    extracted_data = extract_bsky_post_info(data)

    if extracted_data:
        print("Extracted Bluesky Post Information:")
        for key, value in extracted_data.items():
            print(f"{key}: {value}")

        if 'thumb_blob_cid' in extracted_data and extracted_data['did']:
            thumb_url = bsky_thumb(extracted_data['did'], extracted_data['thumb_blob_cid'])
            if thumb_url:
                print(f"Thumbnail URL: {thumb_url}")
            else:
                print("Could not generate thumbnail URL.")
    else:
        print("Could not process the post.")


# Main function to scan Bluesky posts
def scan_bluesky_posts():
    cybersecurity_keywords = [
        "CyberSecurity", "InfoSec", "CyberThreats", "DataBreach", "ethical hacking",
        "threat intelligence", "PenTesting", "network security", "CyberAwareness", "phishing attacks",
        "ransomware protection", "#CyberAttack", "data privacy laws", "Malware", "zero trust architecture",
        "cloud security", "security operations center", "digital forensics", "red team vs blue team",
        "BlueTeam", "cyber defense strategies", "bug bounty programs", "risk assessment",
        "threat hunting", "#SecurityAnalyst", "security operations", "cyber threat landscape", "penetration testing", "cyber hygiene", "IoT security risks", "supply chain vulnerabilities", "security awareness training",
        "IdentityTheft", "insider threats", "social engineering tactics", "MITRE ATT&CK framework", "cyber compliance",
        "RiskManagement", "dark web monitoring", "cyber forensics tools", "advanced persistent threats", "zero-day vulnerabilities",
        "firewall configuration", "endpoint protection", "DDoS", "secure software development",
        "DevSecOps best practices", "cyber trends", "security monitoring tools", "cloud security threats", "password managers",
        "ThreatActors", "insider threat detection", "mobile security", "web application security", "cyber law enforcement",
        "SOC 2 compliance", "NIST cybersecurity framework", "ISO 27001 certification", "PCI DSS compliance", "secure coding principles",
        "AI in cybersecurity", "nation-state cyber attacks", "threat modeling techniques", "common vulnerabilities and exposures", "cyber insurance policies",
        "CyberResilience", "bug bounty hunting", "red teaming vs blue teaming", "industrial control system", "SCADA security challenges",
        "ethical hacker mindset", "automating security processes", "deep web vs dark web", "cyber surveillance", "APT groups tactics",
        "OSINT", "penetration tester skills", "threat intelligence feeds", "deep web exploration",
        "cyber terrorism threats", "cyber warfare tactics", "offensive security strategies", "cyber threat actors motivations", "vulnerability scanning tools",
        "security operations best practices", "SIEM deployment strategies", "cyber awareness campaigns", "malware analysis techniques",
        "blockchain security", "hacking toolkits", "cybersecurity job market", "security consulting services", "cybersecurity for small businesses"
    ]

    cybersecurity_keywords = [x.lower() for x in cybersecurity_keywords]
    
    def post_contains_keywords(post_text, keywords):
        post_text_lower = post_text.lower()
        return any(keyword in post_text_lower for keyword in keywords)

    for bsky_post in jetstream(collections=["app.bsky.feed.post"], yield_response=True, cursor=int((time.time()-1e5)*1e6)):
        bsky_post = json.loads(bsky_post)
        
        if "commit" not in bsky_post or "record" not in bsky_post["commit"] or "text" not in bsky_post["commit"]["record"]:
            continue
        
        
        if "langs" not in bsky_post["commit"]["record"] or "en" not in bsky_post["commit"]["record"]["langs"]:
            continue

        if post_contains_keywords(bsky_post["commit"]["record"]["text"], cybersecurity_keywords):
            multiprocessing.Process(target=clean_and_store_post, args=(bsky_post,)).start()


def main():
    multiprocessing.Process(target=scan_bluesky_posts).start()
    multiprocessing.Process(target=fetch_rss_feeds).start()

if __name__ == "__main__":
    fetch_rss_feeds()