"""
Simple Email Sender for MailHog
Reads CSV and sends personalized emails
"""

import smtplib
import asyncio
import os
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# MailHog SMTP Configuration (can be overridden via environment variables)
SMTP_HOST = os.getenv('SMTP_HOST', 'localhost')
SMTP_PORT = int(os.getenv('SMTP_PORT', '1025'))
SENDER_EMAIL = 'sales@yourcompany.com'

def _send_single_email(row, idx, total, sender_email, smtp_host, smtp_port):
    """Helper function to send a single email (synchronous)"""
    try:
        # Get recipient email
        recipient = row.get('email', '')
        
        if not recipient:
            return {
                'idx': idx,
                'email_sent': False,
                'sent_at': '',
                'send_status': 'No email address'
            }
        
        # Create email
        msg = MIMEText(row['email_body'], 'plain')
        msg['Subject'] = row['email_subject']
        msg['From'] = sender_email
        msg['To'] = recipient
        
        # Connect and send (fresh connection for each email)
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.sendmail(sender_email, recipient, msg.as_string())
        
        # Update status
        return {
            'idx': idx,
            'email_sent': True,
            'sent_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'send_status': 'Success',
            'recipient': recipient,
            'name': row['name']
        }
        
    except Exception as e:
        return {
            'idx': idx,
            'email_sent': False,
            'sent_at': '',
            'send_status': f'Error: {str(e)}',
            'name': row['name']
        }


async def send_emails_async(input_csv='output/emails_generated.csv', output_csv='output/emails_sent_status.csv'):
    """Read CSV and send emails via MailHog - async version"""
    
    print(f"\n📂 Loading emails from {input_csv}...")
    
    # Load CSV
    df = pd.read_csv(input_csv)
    
    print(f"✅ Loaded {len(df)} emails to send\n")
    
    # Add status columns
    df['email_sent'] = False
    df['email_sender'] = SENDER_EMAIL
    df['sent_at'] = ''
    df['send_status'] = ''
    
    # Send emails in parallel (reconnect for each email to avoid connection drops)
    print(f"🔗 Using MailHog at {SMTP_HOST}:{SMTP_PORT}\n")
    print(f"📤 Sending {len(df)} emails in parallel...\n")
    
    # Create tasks for parallel sending with real-time output
    async def send_with_index(idx, row):
        result = await asyncio.to_thread(
            _send_single_email,
            row,
            idx,
            len(df),
            SENDER_EMAIL,
            SMTP_HOST,
            SMTP_PORT
        )
        return idx, row.get('name', 'Unknown'), result
    
    tasks = []
    for idx, row in df.iterrows():
        tasks.append(send_with_index(idx, row))
    
    # Process results as they complete
    completed_count = 0
    results_dict = {}
    
    for coro in asyncio.as_completed(tasks):
        try:
            idx, name, result = await coro
            completed_count += 1
            
            # Print output immediately
            if result['email_sent']:
                print(f"✅ [{completed_count}/{len(df)}] Sent to {result['name']} ({result.get('recipient', '')})")
            else:
                print(f"❌ [{completed_count}/{len(df)}] Failed for {result.get('name', name)} - {result['send_status']}")
            
            # Store result with original index
            results_dict[idx] = result
            
        except Exception as e:
            completed_count += 1
            print(f"❌ [{completed_count}/{len(df)}] Error sending email: {e}")
            # We can't recover idx/name from exception, skip this entry
    
    # Update dataframe with results
    for idx, result in results_dict.items():
        df.at[idx, 'email_sent'] = result['email_sent']
        df.at[idx, 'sent_at'] = result['sent_at']
        df.at[idx, 'send_status'] = result['send_status']
    
    # Save status CSV
    df.to_csv(output_csv, index=False)
    
    # Summary
    sent_count = df['email_sent'].sum()
    print(f"\n{'='*60}")
    print(f"📊 SUMMARY")
    print(f"{'='*60}")
    print(f"✅ Successfully sent: {sent_count}/{len(df)} emails")
    print(f"❌ Failed: {len(df) - sent_count}")
    print(f"💾 Status saved to: {output_csv}")
    print(f"{'='*60}\n")
    
    return df


def send_emails(input_csv='output/emails_generated.csv', output_csv='output/emails_sent_status.csv'):
    """Read CSV and send emails via MailHog - sync wrapper for backward compatibility"""
    return asyncio.run(send_emails_async(input_csv, output_csv))


if __name__ == "__main__":
    print("="*60)
    print("📧 MAILHOG EMAIL SENDER")
    print("="*60)
    
    asyncio.run(send_emails_async())
    
    print("✨ Done! Check MailHog at http://localhost:8025")