# TPF Newsletter Research Agent
### AI Intern Assignment — The Product Folks (TPF)

An AI-powered research agent that automatically monitors 9 sources across 5 categories, summarizes articles using LLM, and generates a structured weekly digest for an AI/Product newsletter.

---

## How It Works

```
RSS Feeds (9 sources)
       ↓
agent.py — fetches, filters, summarizes via Groq AI
       ↓
output.txt / Google Sheets — stores all articles
       ↓
digest.py — generates weekly digest via Groq AI
       ↓
digest_YYYY-MM-DD.txt — final newsletter digest
```

---

## Sources Monitored (9 total)

| Source | Category |
|---|---|
| TechCrunch AI | Newsletter |
| MIT Technology Review | Newsletter |
| Product Hunt | Product Launch |
| Hacker News | Blog |
| The Verge AI | Blog |
| Hugging Face Blog | AI Research |
| DeepMind Blog | AI Research |
| X - Andrej Karpathy (via Nitter RSS) | X/Twitter |
| X - Yann LeCun (via Nitter RSS) | X/Twitter |

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Add your Groq API key (free at console.groq.com)
Create an `env` file (or a `.env` file) in the root directory:
```
GROQ_API_KEY=gsk_your_key_here
```

### 3. (Optional) Google Sheets setup
- Create a Google Cloud project
- Enable Google Sheets API + Google Drive API
- Download service account credentials as `credentials.json`
- Create a Google Sheet named `TPF Newsletter Research`
- Share the sheet with your service account email

---

## Usage

### Step 1 — Run the research agent
```bash
python agent.py
```
Fetches articles from all 9 sources, summarizes them, saves to `output.txt`

### Step 2 — Generate the weekly digest
```bash
python digest.py
```
Reads articles, generates structured digest, saves to `digest_YYYY-MM-DD.txt`

---

## Output Format

### output.txt columns
`Date | Source | Source Category | Title | Category | Summary | Link`

### digest sections
- Top Themes This Week
- Key Launches & Tools
- Funding & Industry News
- Research & Model Releases
- From X / Twitter
- Insight of the Week

---

## Tech Stack

| Tool | Purpose |
|---|---|
| Python 3.12+ | Core language |
| feedparser | RSS feed parsing |
| Groq API (Llama 3.3 70B) | AI summarization & digest generation |
| gspread + oauth2client | Google Sheets integration |
| python-dotenv | Secure API key management |
| GitHub | Version control & submission |

---

## Cost
- Groq API — **Free tier** (rate limited, sufficient for weekly use)
- Google Sheets API — **Free**
- **Total: $0/week**