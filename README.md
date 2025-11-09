# Workflow Orchestrator

This workflow orchestrates the complete AI-powered Sales Campaign CRM process in two steps.

## Workflow Steps

### Step 1: Lead Analysis → Personalized Email → Send MailHog
1. **Lead Analysis** - Analyzes leads from CSV and generates priority scores
2. **Personalized Email** - Generates personalized emails for each lead
3. **Send MailHog** - Sends emails via MailHog (localhost:1025)

### Step 2: Mail Reply Agent → Response Analysis → Summary Report (Optional)
1. **Mail Reply Agent** - Generates random client replies (for MVP)
2. **Response Analysis** - Classifies and analyzes the replies
3. **Summary Report** - Generates comprehensive campaign report

## Usage

### Running the Workflow

```bash
# From the project root directory
python workflow/main_workflow.py
```

### Requirements

1. **MailHog** must be running for email sending:
   ```bash
   # Install MailHog (if not installed)
   # Then run:
   mailhog
   # Or use Docker:
   docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
   ```

2. **Environment Variables** - Ensure `.env` file contains:
   - `GOOGLE_API_KEY` - Your Google Gemini API key

3. **Input File** - Ensure `dataset/leads.csv` exists with the required columns

## Workflow Behavior

### Step 1 Execution
- Always executes: Lead Analysis → Personalized Email → Send MailHog
- Outputs saved to `output/` directory:
  - `analyzed_leads.csv`
  - `emails_generated.csv`
  - `emails_sent_status.csv`

### User Prompt
After Step 1, the workflow asks:
- **Yes** - Continue with Step 2 (Mail Reply Agent → Response Analysis → Summary Report)
- **No** - Stop workflow (Step 2 will execute after client replies)

**Note:** For MVP, the workflow automatically generates a random response (Yes/No).

### Step 2 Execution (if Yes)
- Processes mail replies
- Analyzes responses
- Generates summary report
- Outputs saved to `output/` directory:
  - `emails_with_replies.csv`
  - `final.csv`
  - `campaign_report.md`

## Output Files

All output files are saved in the `output/` directory:

- `analyzed_leads.csv` - Leads with priority scores and buyer personas
- `emails_generated.csv` - Generated personalized emails
- `emails_sent_status.csv` - Email sending status
- `emails_with_replies.csv` - Emails with client replies (Step 2)
- `final.csv` - Classified responses (Step 2)
- `campaign_report.md` - Comprehensive campaign report (Step 2)

## Notes

- The workflow does not modify any files in the `src/` directory
- All scripts in `src/` are imported and executed as-is
- The workflow handles path resolution automatically
- Ensure MailHog is running before executing Step 1

