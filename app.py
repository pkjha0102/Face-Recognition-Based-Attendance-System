import cv2
import os
from flask import Flask, request, render_template
from datetime import date
from datetime import datetime
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import pandas as pd
import joblib
import smtplib
from email.message import EmailMessage


#############################################################################################################################################
# Function To Send Email
def sendEmail():
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
################################################################################################################################################


################################################################################################################################################
# Defining Flask App
app = Flask(__name__)

nimgs = 10

datetoday = date.today().strftime("%d-%B-%Y")
#datetoday = date.today().strftime("%d-%B-%Y")

# Initializing VideoCapture object to access WebCam
face_detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')


# If these directories don't exist, create them
if not os.path.isdir('Attendance'):
    os.makedirs('Attendance')
if not os.path.isdir('static'):
    os.makedirs('static')
if not os.path.isdir('static/faces'):
    os.makedirs('static/faces')
if f'Attendance-{datetoday}.csv' not in os.listdir('Attendance'):
    with open(f'Attendance/Attendance-{datetoday}.csv', 'w') as f:
        f.write('Name,Roll,Email,Time,Email_Sent')


# get a number of total registered users
def totalreg():
    return len(os.listdir('static/faces'))


# extract the face from an image
def extract_faces(img):
    try:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        face_points = face_detector.detectMultiScale(gray, 1.2, 5, minSize=(20, 20))
        return face_points
    except:
        return []


# Identify face using ML model
def identify_face(facearray):
    model = joblib.load('static/face_recognition_model.pkl')
    return model.predict(facearray)


# A function which trains the model on all the faces available in faces folder
def train_model():
    faces = []
    labels = []
    userlist = os.listdir('static/faces')
    for user in userlist:
        for imgname in os.listdir(f'static/faces/{user}'):
            img = cv2.imread(f'static/faces/{user}/{imgname}')
            resized_face = cv2.resize(img, (50, 50))
            faces.append(resized_face.ravel())
            labels.append(user)
    faces = np.array(faces)
    knn = KNeighborsClassifier(n_neighbors=5)
    knn.fit(faces, labels)
    joblib.dump(knn, 'static/face_recognition_model.pkl')


# Extract info from today's attendance file in attendance folder
def extract_attendance():
    df = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')
    names = df['Name']
    rolls = df['Roll']
    emails = df['Email']
    times = df['Time']
    l = len(df)
    return names, rolls, emails, times, l


# Add Attendance of a specific user
def add_attendance(name):
    username = name.split('_')[0]
    userid = name.split('_')[1]
    emailid = name.split('_')[2]
    current_time = datetime.now().strftime("%H:%M:%S")

    df = pd.read_csv(f'Attendance/Attendance-{datetoday}.csv')
    if userid not in list(df['Roll']):
        with open(f'Attendance/Attendance-{datetoday}.csv', 'a') as f:
            f.write(f'\n{username},{userid},{emailid},{current_time},{False}')
        # Call sendEmail function immediately
        sendEmail()

## A function to get names and roll numbers of all users
def getallusers():
    userlist = os.listdir('static/faces')
    names = []
    rolls = []
    emails = []
    l = len(userlist)

    for i in userlist:
        name, roll, email = i.split('_')
        names.append(name)
        rolls.append(roll)
        emails.append(email)

    return userlist, names, rolls, emails, l


## A function to delete a user folder 
def deletefolder(duser):
    pics = os.listdir(duser)
    for i in pics:
        os.remove(duser+'/'+i)
    os.rmdir(duser)

##################################################################################################################################################

#################################################### ROUTING FUNCTIONS #########################################################################

# Our main page
@app.route('/')
def home():
    names, rolls, emails, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, emails=emails, times=times, l=l, totalreg=totalreg(), datetoday=datetoday)


## List users page
@app.route('/listusers')
def listusers():
    userlist, names, rolls, emails, l = getallusers()
    return render_template('listusers.html', userlist=userlist, names=names, rolls=rolls, emails=emails, l=l, totalreg=totalreg(), datetoday=datetoday)


## Delete functionality
@app.route('/deleteuser', methods=['GET'])
def deleteuser():
    duser = request.args.get('user')
    deletefolder('static/faces/'+duser)

    ## if all the face are deleted, delete the trained file...
    if os.listdir('static/faces/')==[]:
        os.remove('static/face_recognition_model.pkl')
    
    try:
        train_model()
    except:
        pass

    userlist, names, rolls, emails, l = getallusers()
    return render_template('listusers.html', userlist=userlist, names=names, rolls=rolls, emails=emails, l=l, totalreg=totalreg(), datetoday=datetoday)


# Our main Face Recognition functionality. 
# This function will run when we click on Take Attendance Button.
@app.route('/start', methods=['GET'])
def start():
    names, rolls, emails, times, l = extract_attendance()

    if 'face_recognition_model.pkl' not in os.listdir('static'):
        return render_template('home.html', names=names, rolls=rolls, emails=emails, times=times, l=l, totalreg=totalreg(), datetoday=datetoday, mess='No face is added. Please add a new face to continue.')

    ret = True
    cap = cv2.VideoCapture(0)
    while ret:
        ret, frame = cap.read()
        if len(extract_faces(frame)) > 0:
            (x, y, w, h) = extract_faces(frame)[0]
            cv2.rectangle(frame, (x, y), (x+w, y+h), (86, 32, 251), 1)
            cv2.rectangle(frame, (x, y), (x+w, y-40), (86, 32, 251), -1)
            face = cv2.resize(frame[y:y+h, x:x+w], (50, 50))
            identified_person = identify_face(face.reshape(1, -1))[0]
            add_attendance(identified_person)
            cv2.putText(frame, f'{identified_person}', (x+5, y-5),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.imshow('Attendance', frame)
        #k = cv2.waitKey(1)
        if cv2.waitKey(1) == 13 or cv2.waitKey(1) == 27 or cv2.waitKey(1) == 32:
            break

    cap.release()
    cv2.destroyAllWindows()
    names, rolls, emails, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, emails=emails, times=times, l=l, totalreg=totalreg(), datetoday=datetoday)

# A function to add a new user.
# This function will run when we add a new user.
@app.route('/add', methods=['GET', 'POST'])
def add():
    newusername = request.form['newusername']
    newuserid = request.form['newuserid']
    newemailid = request.form['newemailid']
    userimagefolder = 'static/faces/'+newusername+'_'+str(newuserid)+'_'+newemailid
    if not os.path.isdir(userimagefolder):
        os.makedirs(userimagefolder)
    i, j = 0, 0
    cap = cv2.VideoCapture(0)
    while 1:
        _, frame = cap.read()
        faces = extract_faces(frame)
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 20), 2)
            cv2.putText(frame, f'Images Captured: {i}/{nimgs}', (30, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 20), 2, cv2.LINE_AA)
            if j % 5 == 0:
                name = newusername+'_'+str(i)+'.jpg'
                cv2.imwrite(userimagefolder+'/'+name, frame[y:y+h, x:x+w])
                i += 1
            j += 1
        if j == nimgs*5:
            break
        cv2.imshow('Adding new User', frame)
        if cv2.waitKey(1) == 27 or cv2.waitKey(1) == 13 or cv2.waitKey(1) == 32:
            break
    cap.release()
    cv2.destroyAllWindows()
    print('Training Model')
    train_model()
    names, rolls, emails, times, l = extract_attendance()
    return render_template('home.html', names=names, rolls=rolls, emails=emails, times=times, l=l, totalreg=totalreg(), datetoday=datetoday)


# Our main function which runs the Flask App
if __name__ == '__main__':
    app.run(debug=True)

######################################################################################################################################################