"""
Main Workflow Orchestrator
Executes the complete sales campaign workflow in two steps:
Step 1: Lead Analysis -> Personalized Email -> Send MailHog
Step 2 (optional): Mail Reply Agent -> Response Analysis -> Summary Report
"""

import sys
import os
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src directory to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

# Import functions from src modules
from lead_analysis import process_leads
from personalized_email import generate_all_emails
from sendMailHog import send_emails
from mail_reply_agent import process_emails_with_types
from summary_report import generate_campaign_report

# Import response analysis components (avoid importing the module directly due to module-level execution)
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

import pandas as pd

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET_DIR = os.path.join(BASE_DIR, 'dataset')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')
REPORT_DIR = os.path.join(BASE_DIR, 'report')

# Email configuration (from sendMailHog.py)
SENDER_EMAIL = 'sales@yourcompany.com'

# Ensure directories exist
os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(REPORT_DIR, exist_ok=True)


def step1_lead_to_email():
    """Step 1: Lead Analysis -> Personalized Email -> Send MailHog"""
    print("\n" + "="*80)
    print("STEP 1: LEAD ANALYSIS → PERSONALIZED EMAIL → SEND MAILHOG")
    print("="*80 + "\n")
    
    # Change to base directory for relative paths to work
    original_cwd = os.getcwd()
    os.chdir(BASE_DIR)
    
    try:
        # 1. Lead Analysis
        print("\n[1/3] Starting Lead Analysis...")
        print("-" * 80)
        leads_csv = os.path.join(DATASET_DIR, 'leads.csv')
        if not os.path.exists(leads_csv):
            raise FileNotFoundError(f"Leads CSV not found at: {leads_csv}")
        
        process_leads(leads_csv)
        analyzed_leads_csv = os.path.join(OUTPUT_DIR, 'analyzed_leads.csv')
        print(f"✅ Lead Analysis Complete: {analyzed_leads_csv}\n")
        
        # 2. Personalized Email Generation
        print("\n[2/3] Generating Personalized Emails...")
        print("-" * 80)
        emails_generated_csv = os.path.join(OUTPUT_DIR, 'emails_generated.csv')
        generate_all_emails(analyzed_leads_csv, emails_generated_csv)
        print(f"✅ Email Generation Complete: {emails_generated_csv}\n")
        
        # Display emails in the requested format (before sending)
        display_emails(emails_generated_csv)
        
        # 3. Send Emails via MailHog
        print("\n[3/3] Sending Emails via MailHog...")
        print("-" * 80)
        emails_sent_csv = os.path.join(OUTPUT_DIR, 'emails_sent_status.csv')
        send_emails(emails_generated_csv, emails_sent_csv)
        print(f"✅ Email Sending Complete: {emails_sent_csv}\n")
        
        print("\n" + "="*80)
        print("✅ STEP 1 COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return emails_sent_csv
    finally:
        os.chdir(original_cwd)


def step2_reply_to_report():
    """Step 2: Mail Reply Agent -> Response Analysis -> Summary Report"""
    print("\n" + "="*80)
    print("STEP 2: MAIL REPLY AGENT → RESPONSE ANALYSIS → SUMMARY REPORT")
    print("="*80 + "\n")
    
    # Change to base directory for relative paths to work
    original_cwd = os.getcwd()
    os.chdir(BASE_DIR)
    
    try:
        emails_sent_csv = os.path.join(OUTPUT_DIR, 'emails_sent_status.csv')
        if not os.path.exists(emails_sent_csv):
            raise FileNotFoundError(f"Emails sent CSV not found at: {emails_sent_csv}")
        
        # 1. Mail Reply Agent
        print("\n[1/3] Processing Mail Replies...")
        print("-" * 80)
        emails_with_replies_csv = os.path.join(OUTPUT_DIR, 'emails_with_replies.csv')
        process_emails_with_types(emails_sent_csv, emails_with_replies_csv)
        print(f"✅ Mail Reply Processing Complete: {emails_with_replies_csv}\n")
        
        # 2. Response Analysis
        print("\n[2/3] Analyzing Responses...")
        print("-" * 80)
        # Process to temp file first
        temp_final_csv = os.path.join(OUTPUT_DIR, 'final.csv')
        analyze_responses(emails_with_replies_csv, temp_final_csv)
        print(f"✅ Response Analysis Complete: {temp_final_csv}\n")
        
        # Save final.csv to report folder
        final_csv = os.path.join(REPORT_DIR, 'final.csv')
        df_final = pd.read_csv(temp_final_csv)
        df_final.to_csv(final_csv, index=False)
        print(f"✅ Final CSV saved to report folder: {final_csv}\n")
        
        # 3. Summary Report
        print("\n[3/3] Generating Summary Report...")
        print("-" * 80)
        # Use absolute path for the CSV file
        if not os.path.isabs(emails_with_replies_csv):
            emails_with_replies_csv = os.path.join(BASE_DIR, emails_with_replies_csv)
        report = generate_campaign_report(emails_with_replies_csv)
        
        # Save campaign_report.md to report folder
        report_path = os.path.join(REPORT_DIR, 'campaign_report.md')
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"✅ Summary Report Generated: {report_path}\n")
        
        print("\n" + "="*80)
        print("✅ STEP 2 COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
        return report_path
    finally:
        os.chdir(original_cwd)


def analyze_responses(input_csv, output_csv):
    """
    Response analysis function
    Recreates the classify_reply logic from response_analysis module
    """
    # Use absolute path for input
    if not os.path.isabs(input_csv):
        input_csv = os.path.join(BASE_DIR, input_csv)
    if not os.path.isabs(output_csv):
        output_csv = os.path.join(BASE_DIR, output_csv)
    
    # Initialize LLM (same as response_analysis.py)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.9)
    
    # JSON classification prompt (same as response_analysis.py)
    prompt = ChatPromptTemplate.from_template(
        """You are a classifier for customer email replies.
Return a JSON object:
{{"class": "<one_of: SKIP | INTERESTED | NOT_INTERESTED | NEEDS_FOLLOW_UP | UNCLEAR>","reason":"<short rationale>"}}

Text:
{reply}"""
    )
    parser = JsonOutputParser()
    chain = prompt | llm | parser
    
    allowed_labels = {"SKIP", "INTERESTED", "NOT_INTERESTED", "NEEDS_FOLLOW_UP", "UNCLEAR"}
    
    def classify_reply(text):
        """Classify a reply text"""
        text = str(text).strip() if text else ""
        if not text:
            return {"class": "NO_REPLY", "reason": "Empty content"}
        try:
            res = chain.invoke({"reply": text})
            label = res.get("class", "").upper()
            if label not in allowed_labels:
                label = "UNCLEAR"
            return {"class": label, "reason": res.get("reason", "")}
        except Exception as e:
            return {"class": "UNCLEAR", "reason": f"Error: {e}"}
    
    # Load CSV
    df = pd.read_csv(input_csv)
    
    if "reply_mail_body" not in df.columns:
        raise ValueError("Column 'reply_mail_body' not found")
    
    # Process with batch delay
    results = []
    for i, reply in enumerate(df["reply_mail_body"], 1):
        print(f"Processing {i}/{len(df)}...")
        results.append(classify_reply(reply))
        time.sleep(0.5)  # small delay to avoid hitting rate limits
    
    df["reply_class"] = [r["class"] for r in results]
    df["reply_reason"] = [r["reason"] for r in results]
    
    df.to_csv(output_csv, index=False)
    print(f"Finished! Classified CSV saved to {output_csv}")


def display_emails(emails_csv):
    """
    Display all emails in the requested format:
    Mail To:
    Mail From:
    Subject:
    Email Body:
    """
    if not os.path.exists(emails_csv):
        return
    
    df = pd.read_csv(emails_csv)
    
    print("\n" + "="*80)
    print("📧 GENERATED EMAILS")
    print("="*80)
    
    # Display all emails
    for idx, row in df.iterrows():
        recipient_email = row.get('email', 'N/A')
        # Use sender email from CSV if available, otherwise use default
        sender_email = row.get('email_sender', SENDER_EMAIL)
        subject = row.get('email_subject', 'N/A')
        body = row.get('email_body', 'N/A')
        
        print(f"\n{'='*80}")
        print(f"Mail To: {recipient_email}")
        print(f"Mail From: {sender_email}")
        print(f"Subject: {subject}")
        print(f"Email Body:")
        print("-" * 80)
        print(body)
        print(f"{'='*80}\n")


def ask_user_continue():
    """
    Ask user if they want to continue to step 2
    """
    print("\n" + "="*80)
    print("STEP 1 COMPLETED - READY FOR STEP 2")
    print("="*80)
    print("\nThe agent will generate some random responses.")
    print("Should I continue with Step 2 (Mail Reply Agent → Response Analysis → Summary Report)?")
    print("\nOptions:")
    print("  Yes - Continue with Step 2")
    print("  No  - Stop workflow (Step 2 will execute after client replies)")
    print("\n" + "-" * 80)
    
    user_input = input("\nEnter your choice (Yes/No): ").strip()
    print(f"\n✅ User selection = {user_input}\n")
    
    return user_input.lower() in ['yes', 'y']


def main():
    """Main workflow orchestrator"""
    print("\n" + "="*80)
    print("🚀 AI-POWERED SALES CAMPAIGN CRM - WORKFLOW ORCHESTRATOR")
    print("="*80)
    
    try:
        # Step 1: Lead Analysis → Personalized Email → Send MailHog
        step1_lead_to_email()
        
        # Ask user if they want to continue
        should_continue = ask_user_continue()
        
        if should_continue:
            # Step 2: Mail Reply Agent → Response Analysis → Summary Report
            step2_reply_to_report()
            print("\n" + "="*80)
            print("🎉 WORKFLOW COMPLETED SUCCESSFULLY!")
            print("="*80)
            print("\nFinal reports saved in the 'report' directory:")
            print("  - final.csv")
            print("  - campaign_report.md")
            print("="*80 + "\n")
        else:
            print("\n" + "="*80)
            print("⏸️  WORKFLOW PAUSED")
            print("="*80)
            print("\nStep 1 completed successfully.")
            print("Step 2 (Mail Reply Agent → Response Analysis → Summary Report)")
            print("will be executed after the client replies.")
            print("="*80 + "\n")
    
    except Exception as e:
        print("\n" + "="*80)
        print("❌ ERROR IN WORKFLOW")
        print("="*80)
        print(f"\nError: {str(e)}")
        print("\nPlease check:")
        print("  1. All required files exist in the dataset directory")
        print("  2. MailHog is running (for email sending)")
        print("  3. Environment variables are set (.env file)")
        print("  4. All dependencies are installed")
        print("="*80 + "\n")
        raise


if __name__ == "__main__":
    main()

