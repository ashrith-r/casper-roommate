"""Email delivery is available only with explicit server configuration."""
from email.message import EmailMessage
import os
import smtplib
import ssl

def email_ready():
    return all(os.environ.get(k) for k in ('EMAIL_USER','EMAIL_PASS','CASPER_ADMIN_PASSWORD'))

def compose(to_email, participant_id, roommate_id, room=None):
    if not to_email or '\n' in to_email or '\r' in to_email:
        raise ValueError('A valid recipient address is required.')
    msg=EmailMessage()
    msg['To']=to_email;msg['Subject']='CASPER pairing for review'
    msg['From']=os.environ.get('EMAIL_USER','')
    body=f'Your participant ID: {participant_id}\nProposed roommate ID: {roommate_id}\n'
    if room:body+=f'Room: {room}\n'
    body+='\nPlease review this proposed pairing with the allocation coordinator.\n'
    msg.set_content(body)
    return msg

def send_email(message):
    if not email_ready(): raise RuntimeError('Email and administrator credentials are not configured.')
    host=os.environ.get('SMTP_HOST','smtp.gmail.com')
    port=int(os.environ.get('SMTP_PORT','465'))
    with smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=20) as server:
        server.login(os.environ['EMAIL_USER'],os.environ['EMAIL_PASS'])
        server.send_message(message)
