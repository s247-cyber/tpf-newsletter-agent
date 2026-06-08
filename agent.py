# ==============================================================================
# agent.py - TPF NEWSLETTER RESEARCH AGENT: INGESTION PIPELINE NODE
# ==============================================================================
# Functional Overview:
# This script forms the automated ingestion layer of the research framework. It:
#   1. Polls 9 distinct industry streams (RSS, product launches, newsletters).
#   2. Runs a semantic text matching filter via pre-defined technical keywords.
#   3. Batches payloads to the Groq API using the high-throughput Llama 3.1 8B 
#      model to safely generate 2-sentence executive briefs and tag taxonomy categories.
#   4. Commits structured data concurrently to Google Sheets (Cloud Production)
#      and custom visual ASCII matrices (Local Fallback Database).
# ==============================================================================

import os
from datetime import datetime
import feedparser
from groq import Groq
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# ENVIRONMENT & CORE INITIALIZATION
# ------------------------------------------------------------------------------
# Gracefully checks for isolated Docker/virtual environment configurations ('env') 
# before defaulting to standard developer local workspace configuration files ('.env').
if os.path.exists("env"):
    load_dotenv(dotenv_path="env")
else:
    load_dotenv()

# Instantiates the main Groq AI Client engine utilizing the API access key 
# loaded securely from systemic platform context environments.
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ------------------------------------------------------------------------------
# DATA DICTIONARIES & PIPELINE TARGET CONFIGURATIONS
# ------------------------------------------------------------------------------
# Array of target streams covering 5 mandatory domain verticals requested by TPF.
# Configured with production proxy stream alternative URLs to bypass rate-limits.
SOURCES = [
    {"name": "TechCrunch AI", "url": "https://techcrunch.com/category/artificial-intelligence/feed/", "category": "Newsletter"},
    {"name": "MIT Technology Review", "url": "https://www.technologyreview.com/topic/artificial-intelligence/feed/", "category": "Newsletter"},
    {"name": "Product Hunt", "url": "https://www.producthunt.com/feed", "category": "Product Launch"},
    {"name": "Hacker News", "url": "https://news.ycombinator.com/rss", "category": "Blog"},
    {"name": "The Verge AI", "url": "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml", "category": "Blog"},
    {"name": "Hugging Face Blog", "url": "https://huggingface.co/blog/feed.xml", "category": "AI Research"},
    {"name": "DeepMind Blog", "url": "https://deepmind.google/blog/rss.xml", "category": "AI Research"},
    {"name": "X - Andrej Karpathy", "url": "https://xcancel.com/karpathy/rss", "category": "X/Twitter"},
    {"name": "X - Yann LeCun", "url": "https://xcancel.com/ylecun/rss", "category": "X/Twitter"}
]

# Strategic matching array keywords designed to block unrelated general news 
# items from filtering through to the curation layer.
KEYWORDS = ["ai", "llm", "gpt", "model", "product", "launch", "funding", "startup", "tool", "machine learning", "deepmind"]


def connect_google_sheets():
    """
    Establishes OAuth2 server-to-server credentials to link up with Google Sheets API.
    
    Returns:
        gspread.models.Worksheet: The primary sheet asset instance if authorized.
    """
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
    client_gs = gspread.authorize(creds)
    return client_gs.open("TPF Newsletter Research").sheet1


def is_relevant(title, summary):
    """
    Scans document strings to prevent macro noise from entering the pipeline.
    
    Args:
        title (str): Post title text.
        summary (str): Main content snippet body.
        
    Returns:
        bool: True if context matches keyword array elements, otherwise False.
    """
    content = f"{title} {summary}".lower()
    return any(keyword in content for keyword in KEYWORDS)


def get_ai_summary_and_tag(title, description):
    """
    Leverages Groq Cloud's Llama 3.1 8B Instant endpoint model to execute
    rapid zero-shot inference categorization and semantic summary extraction.
    
    Args:
        title (str): Clean raw entry headline.
        description (str): Raw article feed descriptive paragraph block.
        
    Returns:
        tuple: (str: 2-sentence executive summary brief, str: structured taxonomy category tag)
    """
    prompt = f"""Analyze the following article. 
Provide a clear, exactly 2-sentence summary. 
Then, pick the single most accurate category tag from this list: [Launch, Funding, Research, Tool, Industry News, Twitter/X].

Article Title: {title}
Description/Snippet: {description}

Output your response EXACTLY like this layout format:
Summary: <your 2-sentence summary here>
Tag: <selected category tag>"""

    # Model 'llama-3.1-8b-instant' is strategically selected over 70B models to 
    # exploit separate, higher token-per-minute limits for heavy iterative batch loops.
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150,
        temperature=0.2  # Low temperature minimizes hallucinations and stabilizes parsing formatting.
    )
    
    text = response.choices[0].message.content
    summary, tag = "No summary generated.", "Industry News"
    
    # Iterates line-by-line to parse out structured string fragments from model completions.
    for line in text.split("\n"):
        if line.startswith("Summary:"):
            summary = line.replace("Summary:", "").strip()
        elif line.startswith("Tag:"):
            tag = line.replace("Tag:", "").strip()
            
    return summary, tag


def main():
    print("🚀 Starting TPF Newsletter Research Agent Ingestion Pipeline...\n")
    
    # Column matrix layouts allocating precise spatial cell capacities for local box formatting.
    # Total combined horizontal character width boundary matches 266 cells.
    widths = [12, 22, 17, 40, 15, 60, 100]
    
    # Mathematical Unicode characters map uniform dividers across the text table structure.
    top_divider = "┌" + "┬".join("─" * (w + 2) for w in widths) + "┐\n"
    mid_divider = "├" + "┼".join("─" * (w + 2) for w in widths) + "┤\n"
    bot_divider = "└" + "┴".join("─" * (w + 2) for w in widths) + "┘\n"
    
    # Checks if a table database structure is present to prevent appending duplicate headers.
    needs_header = True
    if os.path.exists("output.txt") and os.path.getsize("output.txt") > 10:
        with open("output.txt", "r", encoding="utf-8") as f:
            lines = [f.readline().strip() for _ in range(3)]
            if any("Source Category" in l for l in lines if l):
                needs_header = False

    # Generates a fresh datastore table with standardized tracking column tags if missing.
    if needs_header:
        print("📝 Missing or broken table header text detected. Re-initializing fresh database layout frame...")
        headers = ["Date", "Source", "Source Category", "Title", "Category", "Summary", "Link"]
        header_line = "│" + "│".join(f" {headers[i]:<{widths[i]}} " for i in range(len(widths))) + "│\n"
        
        with open("output.txt", "w", encoding="utf-8") as f:
            f.write(top_divider)
            f.write(header_line)
            f.write(mid_divider)

    # Secondary storage checklist verify. Activates cloud sheet arrays if auth file exists.
    sheet_available = False
    try:
        sheet = connect_google_sheets()
        sheet_available = True
        print("📊 Successfully connected to Google Sheets cloud layer.")
    except Exception as e:
        print(f"⚠️ Google Sheets not available ({e}). Reverting to local closed box storage structure.")

    all_data_lines = []

    # Iteration engine core loops through each configured industry target stream tracking node.
    for src in SOURCES:
        print(f"📡 Fetching: {src['name']} [{src['category']}]")
        feed = feedparser.parse(src["url"])
        
        if not feed.entries:
            print(f"   ⚠️ No entries found (feed may be blocked, empty, or down)")
            continue
            
        count = 0
        for entry in feed.entries[:5]:  # Processes the 5 most recent records to stay relevant.
            # Filters visual vertical bars out of headlines to preserve database string formatting boundaries.
            title = entry.get("title", "").replace("│", "-").replace("｜", "-").strip()
            desc = entry.get("description", entry.get("summary", ""))
            link = entry.get("link", "").strip()
            
            if is_relevant(title, desc):
                try:
                    summary, tag = get_ai_summary_and_tag(title, desc)
                    summary = summary.replace("│", "-").replace("｜", "-").strip()
                    current_date = datetime.now().strftime("%Y-%m-%d")
                    
                    # Safe-trimming blocks ensure long strings never break local visual table grid lines.
                    t_title = title[:37] + "..." if len(title) > 40 else title
                    t_summary = summary[:57] + "..." if len(summary) > 60 else summary
                    t_link = link[:97] + "..." if len(link) > 100 else link
                    
                    # Maps tokens into spatial pad slots according to cell width restrictions.
                    vals = [current_date, src['name'], src['category'], t_title, tag, t_summary, t_link]
                    data_line = "│" + "│".join(f" {vals[i]:<{widths[i]}} " for i in range(len(widths))) + "│\n"
                    all_data_lines.append(data_line)
                    
                    # Appends full un-truncated URLs to cloud sheet storage for the compilation step.
                    if sheet_available:
                        sheet.append_row([current_date, src['name'], src['category'], title, tag, summary, link])
                        
                    count += 1
                except Exception as ex:
                    print(f"   ❌ Error processing entry '{title}': {ex}")
                    
        print(f"   ✅ Processed and logged {count} relevant articles.")

    # Commits buffered text database records to disk files.
    if all_data_lines:
        file_existed = os.path.exists("output.txt") and os.path.getsize("output.txt") > 300
        
        # Pulls out previous bottom base plates to cleanly scale existing data sets.
        if file_existed:
            with open("output.txt", "r", encoding="utf-8") as f:
                content = f.readlines()
            if content and content[-1].startswith("└"):
                content = content[:-1]
            with open("output.txt", "w", encoding="utf-8") as f:
                f.writelines(content)
                f.write(mid_divider)

        # Appends rows separated by middle borders, closing with a clean bottom baseline.
        with open("output.txt", "a", encoding="utf-8") as f:
            for line in all_data_lines[:-1]:
                f.write(line)
                f.write(mid_divider)
            f.write(all_data_lines[-1])
            f.write(bot_divider)

    print("\n🏁 Ingestion Complete. Closed-box visual data table safely synced.")


if __name__ == "__main__":
    main()