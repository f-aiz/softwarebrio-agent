import asyncio
import json
from scraper import scrape_domain
from extractor import extract_intelligence

TARGET_DOMAINS = ["postman.com", "supabase.com", "vapi.ai"]

async def process_domain(domain: str):
    print(f"[*] Starting processing for {domain}...")
    
    print(f"    - Scraping data...")
    clean_text, discovered_emails = await scrape_domain(domain)
    
    print(f"    - Extracting intelligence with Gemini...")
    intelligence = await extract_intelligence(domain, clean_text, discovered_emails)
    
    return intelligence.model_dump()

async def main():
    results = []
    for domain in TARGET_DOMAINS:
        result = await process_domain(domain)
        results.append(result)
        
        # Pause to prevent hitting the free tier 20 RPM limit
        if domain != TARGET_DOMAINS[-1]:
            print(f"    - Pausing for 20 seconds to respect rate limits...\n")
            await asyncio.sleep(20)
        
    with open("output.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print("\n[+] Processing complete! Data saved to output.json")

if __name__ == "__main__":
    asyncio.run(main())