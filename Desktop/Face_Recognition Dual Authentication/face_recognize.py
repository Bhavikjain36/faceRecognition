#Prepared For: Team Stealth
#Facial Recognition using opencv and AWS Rekognition
#Receives image from S3 and recognizes using api and
#captures image using open cv to store in folder
import time
import boto3
import cv2
import csv
import mysql.connector

from datetime import datetime

#AWS Authentications
client = boto3.client('rekognition', aws_access_key_id='********',
                      aws_secret_access_key='*******', region_name='ca-central-1')
#Collection where faces are added.
collection = 'myfaces'


def connectToDatabase(fobidparam):
    mydb = mysql.connector.connect(
                host="facerecognitiondb.cxd8buh2v95q.ca-central-1.rds.amazonaws.com",
                username="root",
                password="****",
                database="face_recognition"
            )
    mycursor = mydb.cursor()
    sql = """Select s.image from student s inner join accesskey a on s.stud_access_id = a.access_id where a.access_fob_id=%s"""
    mycursor.execute(sql,(fobidparam,))
    myresult = mycursor.fetchone()
    if myresult is None:
        print("ID NOT ASSIGNED TO STUDENT......")
    else:
        for x in myresult:
            x
        id = x.rsplit('/',1)[-1]
        fobid = id.rsplit('.',1)[0]
        #print("User ID:",fobid)
        return fobid
    


def getUserDetails(para):
    mydb = mysql.connector.connect(
                host="facerecognitiondb.cxd8buh2v95q.ca-central-1.rds.amazonaws.com",
                username="root",
                password="*****",
                database="face_recognition"
            )
    mycursor = mydb.cursor()
    sql = """Select Concat(s.first_name,' ', s.last_name) from student s inner join accesskey a on s.stud_access_id = a.access_id where a.access_fob_id=%s"""
    mycursor.execute(sql,(para,))
    myresult = mycursor.fetchone()
    for x in myresult:
        x
    print("Hey there, ",x)
    currentime = datetime.now()
    accessed = currentime.strftime("%d/%m/%Y %H:%M:%S")
    print("System Accessed Time: ",accessed)

#Function to recognize Personb returns the response of the face detetection
def personRecognizer(client, image, collectionId):
    matches = False
    with open(image, 'rb') as file:
        
        #Search the image in the storage if face is detected in the video stream.
        result = client.search_faces_by_image(CollectionId=collectionId, Image={'Bytes': file.read()}, MaxFaces=1,
                                              FaceMatchThreshold=75)
        if (not result['FaceMatches']):
            matches = False
        else:
            matches = result
    return matches, result


#Function to detect face using haarcascade method and capture image using opencv
def faceDetector(frame, face_cascade):
    face_present = False
    faces = face_cascade.detectMultiScale(frame,1.1,5,minSize=(30, 30),flags=cv2.CASCADE_SCALE_IMAGE)
    name = 'Test.png'
    userimage = '/home/pi/Documents/Face_Recognition Dual Authentication/Images/'+name
    if len(faces) > 0:
        face_present = True
        cv2.imwrite(userimage, frame)
        
    return face_present, userimage


#Counts the total faces present in the S3 bucket
def getTotalFaces(collectionId):
    maxResults = 1
    faces_count = 0
    tokens = True

    response = client.list_faces(CollectionId=collectionId, MaxResults=maxResults)
    while tokens:

        faces = response['Faces']
        for i in faces:
            faces_count += 1
        if 'NextToken' in response:
            nextToken = response['NextToken']
            response = client.list_faces(CollectionId=collectionId,
                                         NextToken=nextToken, MaxResults=maxResults)
        else:
            tokens = False
    return faces_count

#Main method to detect the person from the storage and provide the output.
def main():
    tagId = ""
    tagId = input()
    
    if tagId != "":
        RFidRegistered = False
        with open("Database.csv") as csvfile:
            reader = csv.DictReader(csvfile)
            
            
            for row in reader:
                if row["RFid"] == tagId:
                    RFidRegistered = True
                    
        if RFidRegistered == False:
            print("RFid tag is not registered")
    
    if RFidRegistered == True:
    #Cascade classifier to detect object in the live stream.
        cascade = cv2.CascadeClassifier(
            '/home/pi/Documents/Face_Recognition/haarcascade_frontalface_alt.xml')

        #Starts video capture using webcam
        video_capture = cv2.VideoCapture(0)
        #To stop the buffer in the stream
        video_capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        video_capture.set(cv2.CAP_PROP_FPS, 2);

        while True:
            
            #Takes every single frame of the stream..
            ret, frame = video_capture.read()

            #Compares every single frame and train it using haarcascade to check if
                #face is present in the stream.
            face_present, image = faceDetector(frame, cascade)
            #totalfaces = getTotalFaces(collection)
            
            #If face is detected in the stream then continue else wait.
            if (face_present):

                #If face is present the use the response from the personRecognizer() function
                 #store response in variable
                face, response = personRecognizer(client, image, collection)
                if face:
                    #Display the name of the user with whom the image matches.
                    
                        store = (response['FaceMatches'][0]['Face']['ExternalImageId'])
                        user = store.rsplit('.',1)[0]
                        getfob = connectToDatabase(tagId)
                        if getfob != user:
                            
                             print('UnAuthorized Person Present')
                             video_capture.release()
                             main()
                             break
                        else:
                            print("Access Granted")
                            getUserDetails(tagId)
                            video_capture.release()
                            main()
                            break
                else:
                    #If person is not present in the storage.
                    print('UnAuthorized Person Present')
                    video_capture.release()
                    main()
                    break

            if cv2.waitKey(20) & 0xFF == ord('q'):
                break

        #release the stream
        video_capture.release()
        cv2.destroyAllWindows()

main()
