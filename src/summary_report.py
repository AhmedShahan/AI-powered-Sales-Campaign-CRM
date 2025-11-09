"""
Email Campaign Report Generator using LangChain and Gemini AI
This script analyzes email campaign data and generates a comprehensive markdown report
"""

import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.llms import HuggingFaceEndpoint
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def load_and_analyze_csv(file_path):
    """Load CSV and extract key metrics"""
    df = pd.read_csv(file_path)
    
    # Calculate campaign metrics
    total_contacts = len(df)
    emails_sent = df['email_sent'].sum() if 'email_sent' in df.columns else 0
    emails_successful = len(df[df['send_status'] == 'Success']) if 'send_status' in df.columns else 0
    
    # Reply analysis
    replies_received = df['reply'].notna().sum() if 'reply' in df.columns else 0
    positive_replies = 0
    negative_replies = 0
    neutral_replies = 0
    
    if 'reply' in df.columns:
        for reply in df['reply'].dropna():
            if reply.lower() == 'yes':
                positive_replies += 1
            elif reply.lower() == 'no':
                negative_replies += 1
            else:
                neutral_replies += 1
    
    # Industry breakdown
    industry_distribution = df['industry'].value_counts().to_dict() if 'industry' in df.columns else {}
    
    # Company size breakdown
    company_size_dist = df['company_size'].value_counts().to_dict() if 'company_size' in df.columns else {}
    
    # Priority score analysis
    avg_priority = df['priority_score'].mean() if 'priority_score' in df.columns else 0
    high_priority = len(df[df['priority_score'] >= 70]) if 'priority_score' in df.columns else 0
    
    # Location breakdown
    location_dist = df['location'].value_counts().to_dict() if 'location' in df.columns else {}
    
    return {
        'total_contacts': total_contacts,
        'emails_sent': emails_sent,
        'emails_successful': emails_successful,
        'replies_received': replies_received,
        'positive_replies': positive_replies,
        'negative_replies': negative_replies,
        'neutral_replies': neutral_replies,
        'response_rate': round((replies_received / emails_successful * 100), 2) if emails_successful > 0 else 0,
        'positive_rate': round((positive_replies / replies_received * 100), 2) if replies_received > 0 else 0,
        'industry_distribution': industry_distribution,
        'company_size_distribution': company_size_dist,
        'avg_priority_score': round(avg_priority, 2),
        'high_priority_leads': high_priority,
        'location_distribution': location_dist,
        'success_rate': round((emails_successful / emails_sent * 100), 2) if emails_sent > 0 else 0
    }

def generate_campaign_report(csv_file_path):
    """Generate comprehensive campaign report using LangChain and Gemini"""
    
    # Load API key from environment
    google_api_key = os.getenv("GOOGLE_API_KEY")
    
    if not google_api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment variables. Please add it to your .env file.")
    
    # Use Google's Gemini Pro model
    model = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.7,
        top_p=0.95,
        top_k=40,
        max_output_tokens=2048,
        google_api_key=google_api_key,
        convert_system_message_to_human=True,
    )
    
    # Load and analyze data
    metrics = load_and_analyze_csv(csv_file_path)
    
    # Create prompt template
    prompt_template = """
    You are an expert data analyst specializing in email marketing campaigns. 
    
    Generate a comprehensive, enterprise-level campaign report in markdown format based on the following metrics:
    
    **Campaign Metrics:**
    - Total Contacts in Database: {total_contacts}
    - Emails Sent: {emails_sent}
    - Successfully Delivered: {emails_successful}
    - Email Delivery Success Rate: {success_rate}%
    - Replies Received: {replies_received}
    - Response Rate: {response_rate}%
    - Positive Responses: {positive_replies}
    - Negative Responses: {negative_replies}
    - Neutral/Inquiry Responses: {neutral_replies}
    - Positive Reply Rate: {positive_rate}%
    - Average Priority Score: {avg_priority_score}
    - High Priority Leads (Score ≥70): {high_priority_leads}
    
    **Segmentation Data:**
    - Industry Distribution: {industry_distribution}
    - Company Size Distribution: {company_size_distribution}
    - Location Distribution: {location_distribution}
    
    Please create a detailed report with the following sections:
    1. Executive Summary (key highlights and overall campaign performance)
    2. Campaign Overview (total emails, delivery rates, response metrics)
    3. Response Analysis (breakdown of positive, negative, neutral responses with insights)
    4. Audience Segmentation (industry, company size, location insights)
    5. Lead Quality Assessment (priority scores and lead classification)
    6. Key Findings and Insights
    7. Strategic Recommendations (actionable next steps)
    8. Conclusion
    
    Use professional language, include percentages, and provide actionable insights.
    Format the report in clean markdown with proper headers, tables where appropriate, and bullet points.
    """
    
    prompt = PromptTemplate(
        input_variables=[
            "total_contacts", "emails_sent", "emails_successful", "success_rate",
            "replies_received", "response_rate", "positive_replies", "negative_replies",
            "neutral_replies", "positive_rate", "avg_priority_score", "high_priority_leads",
            "industry_distribution", "company_size_distribution", "location_distribution"
        ],
        template=prompt_template
    )
    
    # Create output parser
    parser = StrOutputParser()
    
    # Create chain using LCEL: prompt | model | parser
    chain = prompt | model | parser
    
    # Generate report by invoking the chain
    report = chain.invoke(metrics)
    
    return report

# Example usage
if __name__ == "__main__":
    # Replace with your actual file path
    CSV_FILE_PATH = "output/emails_with_replies.csv"
    
    try:
        print("🔄 Analyzing campaign data...")
        report = generate_campaign_report(CSV_FILE_PATH)
        
        print("\n" + "="*80)
        print("📊 CAMPAIGN REPORT GENERATED")
        print("="*80 + "\n")
        print(report)
        
        # Optionally save to file
        with open("output/campaign_report.md", "w", encoding="utf-8") as f:
            f.write(report)
        print("\n✅ Report saved to 'campaign_report.md'")
        
    except Exception as e:
        print(f"❌ Error generating report: {str(e)}")
        print("\nPlease ensure:")
        print("1. Your .env file contains GOOGLE_API_KEY")
        print("2. The CSV file path is correct")
        print("3. You have installed required packages:")