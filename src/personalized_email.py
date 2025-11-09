"""
AI-Powered Personalized Email Generator
Professional, GRE-style emails with dynamic tone based on lead profile
"""

import os
import pandas as pd
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
import json
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
# Setup Gemini


llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0.8  # Slightly higher for more creative emails
)

print("✅ Email Generator ready!")


# Email Generation Prompt
email_prompt = ChatPromptTemplate.from_template("""
You are an expert B2B sales communication specialist. Write a highly personalized, professional outreach email.

LEAD PROFILE:
- Name: {name}
- Job Title: {job_title}
- Company: {company}
- Industry: {industry}
- Company Size: {company_size}
- Location: {location}
- Priority Score: {priority_score}/100
- Buyer Persona: {buyer_persona}
- Notes/Interests: {notes}
- Last Contact: {last_contact}
- Contact History: {contact_status}

EMAIL TONE & STYLE GUIDELINES:

1. FORMALITY based on Job Title:
   - C-Level (CEO/CTO/CFO): Highly formal, strategic focus, business impact
   - VP/Director: Professional but approachable, ROI-focused
   - Manager: Friendly professional, practical solutions, efficiency
   - Specialist: Conversational professional, technical details

2. URGENCY based on Priority Score:
   - 80-100 (Hot Lead): Direct, value-driven, clear CTA, show you understand their needs
   - 60-79 (Warm Lead): Consultative, problem-solving approach, build relationship
   - 40-59 (Medium): Educational, showcase benefits, nurture interest
   - 0-39 (Cold Lead): Gentle introduction, offer value upfront, low-pressure

3. APPROACH based on Contact History:
   - "Never contacted": Fresh introduction, establish credibility, offer value
   - "Recent contact (within 30 days)": Follow-up, reference previous conversation, next steps
   - "Contacted months ago": Re-engagement, what's new, revive interest
   - "Positive signals in notes": Capitalize on interest, move forward quickly

4. PERSONALIZATION:
   - Reference their industry challenges
   - Mention their company size context (startup vs enterprise needs)
   - Address their likely pain points based on role
   - Use location context if relevant

5. LANGUAGE QUALITY:
   - GRE-level vocabulary (sophisticated but not pretentious)
   - Varied sentence structure
   - Active voice, strong verbs
   - No clichés or generic phrases
   - Crystal clear value proposition

STRUCTURE:
- Subject Line: Compelling, personalized, under 60 characters
- Greeting: Professional, use their name
- Opening: Hook that shows you understand their context
- Body: 2-3 short paragraphs with clear value
- Call-to-Action: Specific, easy to act on
- Closing: Professional sign-off

Return JSON:
{{
  "subject": "email subject line",
  "body": "full email body with proper formatting",
  "tone_used": "describe the tone you applied",
  "key_personalization": "main personalization elements you included"
}}

Write the email now. Make it compelling and professional.
"""
)


def determine_contact_status(last_contact):
    """Contact history analyze করা"""
    if not last_contact or last_contact == 'Never contacted':
        return "Never contacted"
    
    try:
        # Parse date
        contact_date = datetime.strptime(last_contact, '%Y-%m-%d')
        days_ago = (datetime.now() - contact_date).days
        
        if days_ago <= 7:
            return f"Recent contact ({days_ago} days ago)"
        elif days_ago <= 30:
            return f"Contacted {days_ago} days ago"
        elif days_ago <= 90:
            return f"Contacted {days_ago // 30} months ago"
        else:
            return f"Last contacted {days_ago // 30} months ago"
    except:
        return "Contact history unclear"


async def generate_email(lead):
    """একটা lead এর জন্য email generate করা"""
    try:
        # Determine contact status
        contact_status = determine_contact_status(lead.get('last_contact', ''))
        
        # Get values with fallbacks
        priority_score = lead.get('priority_score', 50)
        job_title = lead.get('job_title') or lead.get('ai_filled_job_title', 'Professional')
        industry = lead.get('industry') or lead.get('ai_filled_industry', 'Business')
        company_size = lead.get('company_size') or lead.get('ai_filled_company_size', 'Medium')
        notes = lead.get('notes') or lead.get('ai_filled_notes', 'Potential interest in business solutions')
        
        # Generate email
        messages = email_prompt.format_messages(
            name=lead['name'],
            job_title=job_title,
            company=lead['company'],
            industry=industry,
            company_size=company_size,
            location=lead.get('location', ''),
            priority_score=priority_score,
            buyer_persona=lead.get('buyer_persona', 'Business Professional'),
            notes=notes,
            last_contact=lead.get('last_contact', 'Never contacted'),
            contact_status=contact_status
        )
        
        response = await llm.ainvoke(messages)
        
        # Parse response
        result = json.loads(response.content.strip().replace('```json', '').replace('```', ''))
        
        return result
        
    except Exception as e:
        print(f"❌ Error generating email: {e}")
        return {
            'subject': f"Following up with {lead['company']}",
            'body': f"Dear {lead['name']},\n\nI hope this email finds you well...",
            'tone_used': 'Generic fallback',
            'key_personalization': 'None - error occurred'
        }


async def generate_all_emails_async(input_csv='analyzed_leads.csv', output_csv='emails_generated.csv'):
    """সব leads এর জন্য email generate করা - async version"""
    
    print(f"\n📂 Loading analyzed leads from {input_csv}...")
    
    # Load CSV
    df = pd.read_csv(input_csv)
    
    print(f"✅ Loaded {len(df)} leads")
    print(f"🤖 Starting email generation in parallel...\n")
    
    # Add email columns
    df['email_subject'] = ''
    df['email_body'] = ''
    df['email_tone'] = ''
    df['personalization_notes'] = ''
    df['email_generated_at'] = ''
    
    # Generate emails in parallel with real-time output
    async def generate_with_index(idx, row):
        email = await generate_email(row)
        return idx, row, email
    
    tasks = []
    for idx, row in df.iterrows():
        tasks.append(asyncio.create_task(generate_with_index(idx, row)))
    
    # Process results as they complete
    completed_count = 0
    emails_dict = {}
    
    for coro in asyncio.as_completed(tasks):
        try:
            idx, row, email = await coro
            completed_count += 1
            
            # Print output immediately
            print(f"✍️  [{completed_count}/{len(df)}] Generated email: {row['name']} ({row['company']})")
            print(f"    Priority: {row.get('priority_score', 'N/A')}/100 | Persona: {row.get('buyer_persona', 'N/A')}")
            print("\n📧 Generated Email:")
            print(f"Subject: {email['subject']}")
            print(f"Body: {email['body']}")
            print(f"Tone: {email['tone_used']}")
            print(f"Personalization: {email['key_personalization']}")
            print("-" * 80)  # separator for readability
            print()
            
            # Store email with original index
            emails_dict[idx] = email
            
        except Exception as e:
            completed_count += 1
            print(f"❌ Error generating email: {e}\n")
            # We'll handle missing entries later
    
    # Update dataframe with results
    for idx in df.index:
        if idx in emails_dict:
            email = emails_dict[idx]
            df.at[idx, 'email_subject'] = email['subject']
            df.at[idx, 'email_body'] = email['body']
            df.at[idx, 'email_tone'] = email['tone_used']
            df.at[idx, 'personalization_notes'] = email['key_personalization']
            df.at[idx, 'email_generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        else:
            # Fallback for failed entries
            row = df.loc[idx]
            df.at[idx, 'email_subject'] = f"Following up with {row.get('company', 'Company')}"
            df.at[idx, 'email_body'] = f"Dear {row.get('name', 'Valued Customer')},\n\nI hope this email finds you well..."
            df.at[idx, 'email_tone'] = 'Generic fallback'
            df.at[idx, 'personalization_notes'] = 'Error occurred during generation'
            df.at[idx, 'email_generated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    # Save to CSV
    df.to_csv(output_csv, index=False)
    
    print(f"✅ All emails generated!")
    print(f"💾 Saved to: {output_csv}\n")
    
    # Show sample emails
    print("=" * 80)
    print("📧 SAMPLE EMAILS (Top 3 Priority Leads)")
    print("=" * 80)
    
    for idx, row in df.head(3).iterrows():
        print(f"\n{'='*80}")
        print(f"TO: {row['name']} ({row['job_title']}) - {row['company']}")
        print(f"Priority: {row['priority_score']}/100")
        print(f"{'='*80}")
        print(f"\nSUBJECT: {row['email_subject']}")
        print(f"\n{row['email_body']}")
        print(f"\n{'-'*80}")
        print(f"Tone Used: {row['email_tone']}")
        print(f"Personalization: {row['personalization_notes']}")
        print(f"{'='*80}\n")
    
    return df


def generate_all_emails(input_csv='analyzed_leads.csv', output_csv='emails_generated.csv'):
    """সব leads এর জন্য email generate করা - sync wrapper for backward compatibility"""
    return asyncio.run(generate_all_emails_async(input_csv, output_csv))


# Run
if __name__ == "__main__":
    import os
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_file = os.path.join(base_dir, 'output', 'analyzed_leads.csv')
    output_file = os.path.join(base_dir, 'output', 'emails_generated.csv')
    
    print("=" * 80)
    print("📧 AI-POWERED PERSONALIZED EMAIL GENERATOR")
    print("=" * 80)
    
    asyncio.run(generate_all_emails_async(input_file, output_file))
    
    print("\n✨ Done! Check 'output/emails_generated.csv' for all personalized emails")