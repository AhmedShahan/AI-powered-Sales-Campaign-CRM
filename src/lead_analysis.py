import os
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import json
from dotenv import load_dotenv
load_dotenv()
# Setup Gemini

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.9
)

print("✅ Gemini ready!")


# Prompt template
prompt = ChatPromptTemplate.from_template("""
Analyze this lead and return ONLY a JSON object:

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
  "filled_notes": "<if notes empty, predict what they need>"
}}

Rules:
- Higher score for: CEO/CTO, larger companies, engaged leads
- Persona examples: "Tech Startup Founder", "Enterprise IT Manager"
- If notes exist, keep them. If empty, predict based on industry + role
""")


def analyze_lead(row):
    try:
        # Handle empty values
        notes = row.get('notes', '') or ''
        last_contact = row.get('last_contact', '') or 'Never contacted'
        
        # Call AI
        messages = prompt.format_messages(
            name=row['name'],
            company=row['company'],
            industry=row['industry'],
            job_title=row['job_title'],
            company_size=row['company_size'],
            location=row['location'],
            notes=notes if notes else 'Empty',
            last_contact=last_contact
        )
        
        response = llm.invoke(messages)
        
        # Parse JSON
        result = json.loads(response.content.strip().replace('```json', '').replace('```', ''))
        
        return result
        
    except Exception as e:
        print(f"Error: {e}")
        return {
            'priority_score': 50,
            'buyer_persona': 'Unknown',
            'filled_notes': notes if notes else 'N/A'
        }


# Main process
def process_leads(csv_file='sales_leads.csv'):
    
    # Load CSV
    df = pd.read_csv(csv_file, dtype={'company_size': str})
    print(f"\nLoaded {len(df)} leads\n")
    
    # Add new columns
    df['priority_score'] = 0
    df['buyer_persona'] = ''
    df['ai_filled_notes'] = ''
    
    # Process each lead
    for idx, row in df.iterrows():
        print(f"Analyzing {idx+1}/{len(df)}: {row['name']}...")
        
        result = analyze_lead(row)
        
        df.at[idx, 'priority_score'] = result['priority_score']
        df.at[idx, 'buyer_persona'] = result['buyer_persona']
        df.at[idx, 'ai_filled_notes'] = result['filled_notes']
        
        print(f"   Score: {result['priority_score']}/100 | {result['buyer_persona']}\n")
    
    # Ensure priority_score is numeric and sort descending (highest priority first)
    df['priority_score'] = pd.to_numeric(df['priority_score'], errors='coerce').fillna(0).astype(int)
    df_sorted = df.sort_values(by='priority_score', ascending=False).reset_index(drop=True)

    # Save
    output_file = '/home/shahanahmed/AI-powered-Sales-Campaign-CRM/output/analyzed_leads.csv'
    df_sorted.to_csv(output_file, index=False)
    
    print(f"Done! Saved to: {output_file} (sorted by priority_score desc)")
    
    return df_sorted


# Runs
if __name__ == "__main__":
    process_leads('/home/shahanahmed/AI-powered-Sales-Campaign-CRM/dataset/leads.csv')