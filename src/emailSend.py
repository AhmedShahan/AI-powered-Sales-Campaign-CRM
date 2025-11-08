import smtplib
from email.mime.text import MIMEText

# MailHog SMTP server
SMTP_HOST = 'localhost'
SMTP_PORT = 1025

# Sender
sender = 'test@example.com'

# List of 20 recipients
recipients = [
    'person1@example.com', 'person2@example.com', 'person3@example.com',
    'person4@example.com', 'person5@example.com', 'person6@example.com',
    'person7@example.com', 'person8@example.com', 'person9@example.com',
    'person10@example.com', 'person11@example.com', 'person12@example.com',
    'person13@example.com', 'person14@example.com', 'person15@example.com',
    'person16@example.com', 'person17@example.com', 'person18@example.com',
    'person19@example.com', 'person20@example.com'
]

# Mail content
subject = 'Hello from Python via MailHog'
body_template = 'Hello {name},\n\nThis is a test email sent via MailHog!'

# Connect to SMTP server
with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
    for recipient in recipients:
        # Customize the body for each recipient (optional)
        body = body_template.format(name=recipient.split('@')[0])
        
        # Create message
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] = sender
        msg['To'] = recipient

        # Send email
        server.sendmail(sender, recipient, msg.as_string())
        print(f"Mail sent to {recipient}")

print("All mails sent successfully!")
