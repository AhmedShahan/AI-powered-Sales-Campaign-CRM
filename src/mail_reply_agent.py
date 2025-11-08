import pandas as pd
import random
import asyncio
from langchain_google_genai import ChatGoogleGenerativeAI
import os

from dotenv import load_dotenv
load_dotenv()

async def process_single_email_reply(row, idx, llm):
    """Process a single email reply - async"""
    email_body = str(row['email_body'])
    
    # Randomly select one of the 5 types
    reply_type = random.choice([
        "SKIP",
        "INTERESTED",
        "NOT_INTERESTED", 
        "NEEDS_FOLLOW_UP",
        "UNCLEAR"
    ])
    
    # If SKIP, no reply
    if reply_type == "SKIP":
        return {
            'idx': idx,
            'reply': "No",
            'reply_mail_body': "",
            'reply_type': reply_type
        }
    
    # Generate reply based on type
    prompts = {
        "INTERESTED": f"Write a brief (2-3 sentences) INTERESTED and enthusiastic reply to: {email_body}",
        "NOT_INTERESTED": f"Write a brief (2-3 sentences) polite NOT INTERESTED response to: {email_body}",
        "NEEDS_FOLLOW_UP": f"Write a brief (2-3 sentences) reply requesting follow-up or more information about: {email_body}",
        "UNCLEAR": f"Write a brief (2-3 sentences) reply asking for clarification about: {email_body}"
    }
    
    try:
        reply_body = (await llm.ainvoke(prompts[reply_type])).content
        return {
            'idx': idx,
            'reply': "Yes",
            'reply_mail_body': reply_body,
            'reply_type': reply_type
        }
    except Exception as e:
        return {
            'idx': idx,
            'reply': "No",
            'reply_mail_body': "",
            'reply_type': reply_type,
            'error': str(e)
        }


async def process_emails_with_types_async(input_csv: str, output_csv: str):
    """
    Process emails with 5 random reply types as specified - async version.
    """
    # Read CSV
    print(f"Reading {input_csv}...")
    df = pd.read_csv(input_csv)
    
    # Initialize LLM
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.9
    )
    
    # Add reply columns
    df['reply'] = ""
    df['reply_mail_body'] = ""
    
    print(f"\nProcessing {len(df)} emails in parallel...\n")
    
    # Process all emails in parallel with real-time output
    async def process_with_index(idx, row):
        result = await process_single_email_reply(row, idx, llm)
        return idx, result
    
    tasks = []
    for idx, row in df.iterrows():
        tasks.append(asyncio.create_task(process_with_index(idx, row)))
    
    # Process results as they complete
    completed_count = 0
    results_dict = {}
    
    for coro in asyncio.as_completed(tasks):
        try:
            idx, result = await coro
            completed_count += 1
            
            # Print output immediately
            reply_type = result.get('reply_type', 'Unknown')
            if result['reply'] == 'Yes':
                print(f"📧 [{completed_count}/{len(df)}] Reply generated for email {idx+1}")
                print(f"    Reply type: {reply_type}")
                reply_body = result.get('reply_mail_body', '')
                if reply_body:
                    preview = reply_body[:100] + "..." if len(reply_body) > 100 else reply_body
                    print(f"    Preview: {preview}")
                print()
            else:
                error_msg = f" - Error: {result.get('error', '')}" if result.get('error') else ""
                print(f"⏭️  [{completed_count}/{len(df)}] Skipped email {idx+1} (Type: {reply_type}){error_msg}\n")
            
            # Store result with original index
            results_dict[idx] = result
            
        except Exception as e:
            completed_count += 1
            print(f"❌ [{completed_count}/{len(df)}] Error processing email: {e}\n")
            # We can't recover idx from exception, skip this entry
    
    # Update dataframe with results
    for idx, result in results_dict.items():
        df.at[df.index[idx], 'reply'] = result['reply']
        df.at[df.index[idx], 'reply_mail_body'] = result['reply_mail_body']
    
    # Save
    df.to_csv(output_csv, index=False)
    print(f"✓ Saved to {output_csv}")
    
    # Summary
    print(f"\nReplied: {(df['reply'] == 'Yes').sum()}")
    print(f"Skipped: {(df['reply'] == 'No').sum()}\n")


def process_emails_with_types(input_csv: str, output_csv: str):
    """
    Process emails with 5 random reply types as specified - sync wrapper for backward compatibility.
    """
    return asyncio.run(process_emails_with_types_async(input_csv, output_csv))

# Run
if __name__ == "__main__":
    asyncio.run(process_emails_with_types_async("/home/shahanahmed/AI-powered-Sales-Campaign-CRM/output/emails_sent_status.csv", "output/emails_with_replies.csv"))
