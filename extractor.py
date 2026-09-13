import os
import re
from google import genai
from google.genai import types
from models import CompanyIntelligence
from dotenv import load_dotenv
from ddgs import DDGS

load_dotenv()

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def search_founders(domain: str) -> str:
    """Performs an external web search to discover founders and LinkedIn links."""
    print(f"      - [Agent Action] Finding leadership for {domain} via external search...")
    try:
        results = list(DDGS().text(f"{domain} founders CEO CTO LinkedIn", max_results=5))
        snippets = [f"Title: {r.get('title','')}\nURL: {r.get('href','')}\nSnippet: {r.get('body','')}" for r in results]
        return "\n\n--- SEARCH ENGINE INTELLIGENCE (Leadership Discovery) ---\n" + "\n\n".join(snippets)
    except Exception as e:
        print(f"      [!] Search fallback failed: {e}")
        return ""

async def extract_intelligence(domain: str, raw_text: str, fallback_emails: list[str] = None) -> CompanyIntelligence:
    if not raw_text.strip():
        return CompanyIntelligence(
            domain=domain,
            company_overview="Scraping failed or blocked.",
            target_audience="Unknown",
            confidence_score=0.0
        )
        
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        response_schema=CompanyIntelligence,
        system_instruction=(
            "You are an expert lead enrichment agent. Extract company overview, target audience (ICP), "
            "contact emails, and key leadership. For leadership members, extract their verified personal LinkedIn URL "
            "if present in the context; otherwise leave it null. Never invent URLs."
        )
    )

    try:
        prompt = f"Domain: {domain}\n\nContext:\n{raw_text[:30000]}"
        chat = client.chats.create(model="gemini-3.6-flash", config=config)
        response = chat.send_message(prompt)
        parsed_data = response.parsed
        print(f"      [Token Usage] {response.usage_metadata.total_token_count} tokens used for {domain}")
        parsed_data.domain = domain

        # Fallback Trigger: If website has no leadership info, trigger external search
        if not parsed_data.leadership:
            search_context = search_founders(domain)
            if search_context:
                refined_prompt = f"Domain: {domain}\n\nContext:\n{raw_text[:20000]}\n{search_context}"
                refined_chat = client.chats.create(model="gemini-3.6-flash", config=config)
                refined_resp = refined_chat.send_message(refined_prompt)
                parsed_data = refined_resp.parsed
                parsed_data.domain = domain

        # Deduplicate and clean emails
        all_emails = {re.sub(r'^(?:u003e|gt;|lt;)+', '', e.lower()).strip('.-_') for e in parsed_data.contact_points}
        if fallback_emails:
            for e in fallback_emails:
                cleaned_e = re.sub(r'^(?:u003e|gt;|lt;)+', '', e.lower()).strip('.-_')
                all_emails.add(cleaned_e)
        parsed_data.contact_points = sorted(list(all_emails))

        return parsed_data
        
    except Exception as e:
        print(f"Extraction error for {domain}: {e}")
        return CompanyIntelligence(
            domain=domain,
            company_overview="Extraction error.",
            target_audience="Unknown",
            confidence_score=0.0
        )