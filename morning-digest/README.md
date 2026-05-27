# 🌅 Morning Digest

A self-hosted daily news dashboard for **organisational psychologists working on AI upskilling**.  
Runs automatically every morning at **08:00 UTC** via GitHub Actions, serves a live page on **GitHub Pages**, and uses **Claude** to generate practical takeaways for each article.

**Topics:**
- 🤖 AI Literacy & Capability — critical competencies for AI fluency
- 🏢 AI & Organisational Psychology — impact of AI on wellbeing, engagement, job crafting
- 🔄 Behavioural Change Frameworks — evidence-based models for driving AI adoption
- 🛡️ Psychological Safety — team learning, innovation, and AI experimentation

All articles are filtered to **verified academic and practitioner sources** — journals (Frontiers, ScienceDirect, NCBI/PMC, APA, Wiley, Springer), universities (MIT, Harvard, LSE, Oxford), and top consultancies/institutes (McKinsey, HBR, CIPD, SHRM, WEF, Gallup, Irrational Labs).

---

## ⚡ Setup (~10 minutes)

### Step 1 — Get an Anthropic API key

The digest uses Claude to generate practical takeaways for each article.

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Create an account (or sign in)
3. Go to **API Keys → Create Key**
4. Copy the key — you'll need it in Step 4

> **Cost note:** Each daily run calls Claude Haiku for ~20 articles. At current pricing this costs roughly **$0.01–0.02 per day** (< $0.50/month).

---

### Step 2 — Create a GitHub repository

1. Go to [github.com/new](https://github.com/new)
2. Name it `morning-digest`
3. Set visibility to **Public** (required for free GitHub Pages)
4. Click **Create repository** — do NOT initialise with a README

---

### Step 3 — Upload the files

**Mac tip:** To see the hidden `.github/` folder in Finder, press `Cmd + Shift + .`

**Option A — GitHub web UI:**
1. On the empty repo page, click **uploading an existing file**
2. Drag in all files from the `morning-digest` folder, including `.github/workflows/daily_digest.yml`
3. Click **Commit changes**

**Option B — Git CLI:**
```bash
cd /path/to/morning-digest
git init
git remote add origin https://github.com/YOUR_USERNAME/morning-digest.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

---

### Step 4 — Add your Anthropic API key as a secret

1. In your repo, go to **Settings → Secrets and variables → Actions**
2. Click **New repository secret**
3. Name: `ANTHROPIC_API_KEY`
4. Value: paste your key from Step 1
5. Click **Add secret**

---

### Step 5 — Enable GitHub Pages

1. Go to **Settings → Pages**
2. Under **Source**, select **GitHub Actions**
3. Click **Save**

---

### Step 6 — Enable workflow write permissions

1. Go to **Settings → Actions → General**
2. Scroll to **Workflow permissions**
3. Select **Read and write permissions**
4. Click **Save**

---

### Step 7 — Run it for the first time

1. Go to the **Actions** tab
2. Click **Morning Digest** in the left sidebar
3. Click **Run workflow → Run workflow**
4. Wait ~2 minutes for it to complete

---

### Step 8 — Open your dashboard 🎉

```
https://YOUR_USERNAME.github.io/morning-digest/
```

From now on, it updates itself every day at 08:00 UTC with fresh articles and AI-generated takeaways.

---

## 🔧 Customisation

### Change topics or queries
Edit `fetch_news.py` → the `TOPICS` list. Each entry has:
- `label` + `emoji` — displayed in the UI
- `description` — shown under the topic title
- `queries` — list of Google News search strings

### Change trusted sources
Edit the `TRUSTED_DOMAINS` set in `fetch_news.py` to add or remove allowed domains.

### Change the schedule
Edit `.github/workflows/daily_digest.yml` → the `cron` value (UTC):
- `"0 7 * * *"` — 07:00 UTC
- `"0 6 * * 1-5"` — 06:00 UTC, weekdays only

### Run locally
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python fetch_news.py       # generates articles.json
python -m http.server 8080 # serve locally
# visit http://localhost:8080
```

---

## 📁 File structure

```
morning-digest/
├── .github/
│   └── workflows/
│       └── daily_digest.yml   # Scheduled GitHub Action
├── fetch_news.py              # News fetcher + AI summariser
├── articles.json              # Daily output (auto-committed)
├── index.html                 # Live dashboard
└── README.md
```

---

## 🛠 Troubleshooting

| Issue | Fix |
|-------|-----|
| No articles / "could not load" | Trigger the workflow manually from Actions tab |
| Takeaways are missing | Check that `ANTHROPIC_API_KEY` secret is set correctly |
| Workflow fails: permissions | Settings → Actions → General → Read and write permissions |
| Pages 404 | Wait 3–5 min after first deploy; check Settings → Pages → Source = GitHub Actions |
| All articles filtered out | Some topics return few trusted-source results on quiet days — normal |
