"""
Simple AI Lead Analyzer
শুধু 3টা কাজ: Score + Missing Data Fill + Buyer Persona
"""

import os
import pandas as pd
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.prompts import ChatPromptTemplate
import json
from dotenv import load_dotenv
load_dotenv()
# Setup Gemini

llm = HuggingFaceEndpoint(
    repo_id="meta-llama/Llama-2-7b-chat-hf",
    task="text-generation",
    api_url="https://api-inference.huggingface.co/models/meta-llama/Llama-2-7b-chat-hf",
    temperature=0.7,
    huggingfacehub_api_token=os.getenv("HUGGINGFACEHUB_API_TOKEN"),
)

print("Gemini ready!")
# Prompt template
prompt = ChatPromptTemplate.from_template("""
You are a B2B sales analyst. Analyze this lead carefully and fill missing information.

Lead Data:
- Name: {name}
- Company: {company}
- Industry: {industry}
- Job Title: {job_title}
- Company Size: {company_size}
- Location: {location}
- Notes: {notes}
- Last Contact: {last_contact}

Return JSON with exactly these fields:
{{
  "priority_score": <number 0-100>,
  "buyer_persona": "<persona type>",
  "filled_industry": "<predict if missing, based on company name>",
  "filled_job_title": "<predict if missing, based on available info>",
  "filled_company_size": "<predict if missing>",
  "filled_notes": "<if notes empty, predict what they need>"
}}

PRIORITY SCORING RULES (0-100):
Consider these factors carefully:

1. ENGAGEMENT SIGNALS (30 points max):
   - Notes with positive signals ("interested", "requested demo", "budget approved") → +20-30 points
   - Notes with concerns ("limited budget", "needs follow-up") → +5-10 points
   - Empty/no notes → 0 points

2. RECENCY OF CONTACT (25 points max):
   - Contacted within last 7 days → +25 points
   - Contacted within last 30 days → +15 points
   - Contacted 1-3 months ago → +10 points
   - Contacted 3+ months ago → +5 points
   - Never contacted → 0 points (but can still be high priority based on other factors)

3. JOB TITLE SENIORITY (25 points max):
   - C-Level (CEO, CTO, CFO, COO) → +25 points
   - VP/Director level → +20 points
   - Manager level → +15 points
   - Specialist/Analyst → +10 points

4. COMPANY SIZE (20 points max):
   - 500+ employees → +20 points
   - 200-500 employees → +15 points
   - 100-200 employees → +12 points
   - 50-100 employees → +10 points
   - 10-50 employees → +7 points
   - 1-10 employees → +5 points

Example scoring:
- Hot lead: CEO + contacted yesterday + "very interested" in notes = 80+ points
- Warm lead: Manager + contacted 2 weeks ago + no strong signals = 50-60 points
- Cold lead: Junior role + never contacted + no notes = 20-30 points

FILLING MISSING DATA:
- Industry: Analyze company name (e.g., "TechBangla" → Software, "HealthCare BD" → Healthcare)
- Job Title: Use context clues (if unknown, predict based on seniority signals)
- Company Size: Estimate from industry standards and company name
- Notes: Predict likely interests based on industry + role

BUYER PERSONA:
Create descriptive personas like:
- "Enterprise Technology Decision Maker"
- "Growth-Stage Startup Founder"
- "Mid-Market Operations Leader"
- "SMB Business Owner"
""")


async def analyze_lead(row):
    # Handle empty values - treat empty strings as missing
    industry = row.get('industry', '') or 'Not provided'
    job_title = row.get('job_title', '') or 'Not provided'
    company_size = row.get('company_size', '') or 'Not provided'
    notes = row.get('notes', '') or 'Not provided'
    last_contact = row.get('last_contact', '') or 'Never contacted'
    
    try:
        # Call AI
        messages = prompt.format_messages(
            name=row['name'],
            company=row['company'],
            industry=industry,
            job_title=job_title,
            company_size=company_size,
            location=row['location'],
            notes=notes,
            last_contact=last_contact
        )
        
        response = await llm.ainvoke(messages)
        
        # Parse JSON
        result = json.loads(response.content.strip().replace('```json', '').replace('```', ''))
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'priority_score': 50,
            'buyer_persona': 'Unknown',
            'filled_industry': industry if industry != 'Not provided' else 'Unknown',
            'filled_job_title': job_title if job_title != 'Not provided' else 'Unknown',
            'filled_company_size': company_size if company_size != 'Not provided' else 'Unknown',
            'filled_notes': notes if notes != 'Not provided' else 'N/A'
        }


# Main process
async def process_leads_async(csv_file='sales_leads.csv'):
    """CSV process করা - async version"""
    
    # Load CSV
    df = pd.read_csv(csv_file, dtype={'company_size': str})
    print(f"\nLoaded {len(df)} leads\n")
    
    # Add new columns
    df['priority_score'] = 0
    df['buyer_persona'] = ''
    df['ai_filled_industry'] = ''
    df['ai_filled_job_title'] = ''
    df['ai_filled_company_size'] = ''
    df['ai_filled_notes'] = ''
    
    # Process all leads in parallel with real-time output
    print(f"🤖 Analyzing {len(df)} leads in parallel...\n")
    
    # Create tasks with indices - use a wrapper to track index
    async def analyze_with_index(idx, row):
        result = await analyze_lead(row)
        return idx, row, result
    
    tasks = []
    for idx, row in df.iterrows():
        tasks.append(asyncio.create_task(analyze_with_index(idx, row)))
    
    # Process results as they complete
    completed_count = 0
    results_dict = {}
    
    for coro in asyncio.as_completed(tasks):
        try:
            idx, row, result = await coro
            completed_count += 1
            
            # Print output immediately
            print(f"🤖 [{completed_count}/{len(df)}] Analyzed: {row['name']}...")
            print(f"   Score: {result['priority_score']}/100 | {result['buyer_persona']}\n")
            
            # Store result with original index
            results_dict[idx] = result
            
        except Exception as e:
            completed_count += 1
            # Extract idx and row from exception if possible, or use fallback
            print(f"❌ Error analyzing lead: {e}\n")
            # We can't recover idx/row from exception, so we'll handle it differently
            # For now, just continue
    
    # Update dataframe with results
    for idx, result in results_dict.items():
        row = df.loc[idx]
        df.at[idx, 'priority_score'] = result['priority_score']
        df.at[idx, 'buyer_persona'] = result['buyer_persona']
        
        # Fill missing data - use AI prediction only if original is empty
        df.at[idx, 'ai_filled_industry'] = result.get('filled_industry', row.get('industry', ''))
        df.at[idx, 'ai_filled_job_title'] = result.get('filled_job_title', row.get('job_title', ''))
        df.at[idx, 'ai_filled_company_size'] = result.get('filled_company_size', row.get('company_size', ''))
        df.at[idx, 'ai_filled_notes'] = result['filled_notes']
    
    # Sort by priority score (highest first)
    df = df.sort_values('priority_score', ascending=False)
    
    # Save - use relative path (works in both Docker and local)
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'output')
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'analyzed_leads.csv')
    df.to_csv(output_file, index=False)
    
    print(f"✅ Done! Saved to: {output_file}")
    print(f"✅ Sorted by priority (highest to lowest)\n")
    
    return df


def process_leads(csv_file='sales_leads.csv'):
    """CSV process করা - sync wrapper for backward compatibility"""
    return asyncio.run(process_leads_async(csv_file))


# Run
if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    dataset_file = os.path.join(base_dir, 'dataset', 'leads.csv')
    asyncio.run(process_leads_async(dataset_file))