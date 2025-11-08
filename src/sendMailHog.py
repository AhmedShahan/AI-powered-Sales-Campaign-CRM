"""
Simple Email Sender for MailHog
Reads CSV and sends personalized emails
"""

import smtplib
from email.mime.text import MIMEText
import pandas as pd
from datetime import datetime

# MailHog SMTP Configuration
SMTP_HOST = 'localhost'
SMTP_PORT = 1025
SENDER_EMAIL = 'sales@yourcompany.com'

def send_emails(input_csv='output/emails_generated.csv', output_csv='output/emails_sent_status.csv'):
    """Read CSV and send emails via MailHog"""
    
    print(f"\n📂 Loading emails from {input_csv}...")
    
    # Load CSV
    df = pd.read_csv(input_csv)
    
    print(f"✅ Loaded {len(df)} emails to send\n")
    
    # Add status columns
    df['email_sent'] = False
    df['sent_at'] = ''
    df['send_status'] = ''
    
    # Send emails (reconnect for each email to avoid connection drops)
    print(f"🔗 Using MailHog at {SMTP_HOST}:{SMTP_PORT}\n")
    
    for idx, row in df.iterrows():
        try:
            # Get recipient email
            recipient = row.get('email', '')
            
            if not recipient:
                print(f"❌ {idx+1}/{len(df)}: No email for {row['name']} - Skipped")
                df.at[idx, 'send_status'] = 'No email address'
                continue
            
            # Create email
            msg = MIMEText(row['email_body'], 'plain')
            msg['Subject'] = row['email_subject']
            msg['From'] = SENDER_EMAIL
            msg['To'] = recipient
            
            # Connect and send (fresh connection for each email)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.sendmail(SENDER_EMAIL, recipient, msg.as_string())
            
            # Update status
            df.at[idx, 'email_sent'] = True
            df.at[idx, 'sent_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            df.at[idx, 'send_status'] = 'Success'
            
            print(f"✅ {idx+1}/{len(df)}: Sent to {row['name']} ({recipient})")
            
        except Exception as e:
            print(f"❌ {idx+1}/{len(df)}: Failed for {row['name']} - {str(e)}")
            df.at[idx, 'send_status'] = f'Error: {str(e)}'
    
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


if __name__ == "__main__":
    print("="*60)
    print("📧 MAILHOG EMAIL SENDER")
    print("="*60)
    
    send_emails()
    
    print("✨ Done! Check MailHog at http://localhost:8025")