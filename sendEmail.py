# import the required libraries
import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import date

datetoday = date.today().strftime("%d-%B-%Y")
#print(datetoday)

# change these as per use
your_email = "pkumarjha0102@gmail.com"
your_password = "qcbi psnl tafy vjxg"

# establishing connection with gmail
import ssl
host = "smtp.gmail.com" 
context = ssl.create_default_context()
server = smtplib.SMTP_SSL(host, 465, context=context)
server.login(your_email, your_password)

# reading the spreadsheet
email_list = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')

# getting the names and the emails
names = email_list['Name']
rolls = email_list['Roll']
emails = email_list['Email']
sent = email_list['Email_Sent']

# Emails should be sent only once. Either present or absent.

# iterate through the records and send email if not sent
cnt = 0
for i in range(len(emails)):
    if sent[i] == False:
        cnt = cnt + 1
        #print(sent[i])
        name = names[i]
        roll = rolls[i]
        email = emails[i]
        # define message
        msg = EmailMessage()
        msg.set_content("Dear " + name + ", your Roll No. is " + roll + ". Your attendance is marked for today " + datetoday + ".\n\nThanks and regards\nTeam FRBAS")
        msg['Subject'] = "Attendance Update of " + name + " " + roll + "."
        msg['From'] = your_email
        msg['To'] = email
        #send message
        server.send_message(msg)
        print("Email Message Sent Successfully to " + email + " for " + name + " " + roll + ".\n")
    #else:
        #print("Email Has Been Sent Already.")
print(str(cnt) + " Email(s) sent successfully.\n")

# Make all false values to true after sendng the emails.
email_list["Email_Sent"] = email_list["Email_Sent"].replace({False : True})
email_list.to_csv(f'Attendance/Attendance-{datetoday}.csv', index = False)

# close the smtp server
server.close()
