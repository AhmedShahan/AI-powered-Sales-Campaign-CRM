import os
import pandas as pd
from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
import time

# Load API key
load_dotenv()

# Initialize LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.9)

# JSON classification prompt
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
df = pd.read_csv("/home/shahanahmed/AI-powered-Sales-Campaign-CRM/output/emails_with_replies.csv")
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

df.to_csv("output/final.csv", index=False)
print("Finished! Classified CSV saved to output/final.csv")
