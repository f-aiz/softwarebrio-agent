# Autonomous Lead Enrichment Agent

An intelligent, resilient web scraping and data extraction pipeline built for the SoftwareBrio AI Engineer Internship technical assignment. This agent autonomously navigates target domains, handles dynamic JavaScript content, and leverages LLM-driven structured extraction to generate high-fidelity company intelligence.

## 🚀 Key Features & Architecture

This pipeline is engineered to meet and exceed the assignment requirements, specifically addressing edge cases, API rate limits, and missing DOM data.

* **Agentic Search Fallback (Bonus Achieved):** Implements a custom multi-step tool-calling loop. If the initial LLM extraction detects missing leadership data on the target website, the agent autonomously triggers a DuckDuckGo search to hunt down founders and their verified LinkedIn profiles, feeding that context back into the LLM.
* **Resilient Automated Browsing:** Built with Playwright for asynchronous, headless scraping. It bypasses basic anti-bot blockers, implements `www.` URL fallbacks for timeout handling, and seamlessly tracks links across subdomains (e.g., `docs.vapi.ai/support`) to ensure no critical pages are missed.
* **Token Optimization & Sanitization:** Uses BeautifulSoup and Markdownify to strip out heavy HTML boilerplates, `<script>`, `<style>`, and SVG tags before passing the DOM to the LLM. Includes custom Regex cleaning to sanitize HTML entities (like `u003e`) from discovered email addresses.
* **Strict Structured Outputs:** Integrated with Gemini 3.6 Flash using Pydantic schemas to enforce a strict JSON output containing the Company Overview, Target Audience (ICP), Contact Points, Leadership profiles, and a calculated Data Confidence Score.
* **Cost & Token Tracking (Bonus Achieved):** Logs the exact token usage for the LLM requests dynamically in the terminal to monitor efficiency.

## 🛠 Tech Stack

* **Language:** Python 3.10+
* **Scraping:** `playwright` (Async Headless Browsing)
* **DOM Processing:** `beautifulsoup4`, `markdownify`, `re` (Regex)
* **LLM Integration:** `google-genai` (Gemini 3.6 Flash)
* **Structured Data:** `pydantic`
* **Agentic Search:** `ddgs` (DuckDuckGo Search)

## ⚙️ Setup & Installation

**1. Clone the repository and navigate to the project directory:**

```powershell
git clone <your-repo-url>
cd softwarebrio-agent

```

**2. Create and activate a virtual environment:**

```powershell
python -m venv venv
.\venv\Scripts\activate

```

**3. Install dependencies:**

```powershell
pip install -r requirements.txt

```

**4. Install Playwright browsers:**

```powershell
playwright install chromium

```

**5. Configure Environment Variables:**
Create a `.env` file in the root directory and add your Gemini API key:

```env
GEMINI_API_KEY=your_api_key_here

```

## 💻 Usage

Run the orchestrator script to start the extraction pipeline. The script includes built-in 20-second pauses between domains to respect free-tier API rate limits.

```powershell
python main.py

```

### Expected Output

The script will log its progress, sub-page discovery, autonomous search triggers, and token usage to the terminal. Upon completion, it generates an `output.json` file structured exactly to the prompt's specifications.

## 📁 Project Structure

```text
softwarebrio-agent/
│
├── main.py           # Orchestrator handling the async loop and rate-limit delays
├── scraper.py        # Playwright logic, subdomain URL discovery, DOM to Markdown parsing
├── extractor.py      # Gemini 3.6 Flash integration, Pydantic schema, DDGS agentic fallback
├── models.py         # Pydantic models defining the strict CompanyIntelligence schema
├── .env              # Environment variables (API Keys)
├── requirements.txt  # Project dependencies
└── output.json       # Generated structured output

```