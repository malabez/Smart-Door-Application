import json
import boto3
from botocore.vendored import requests
import time
import random

def lambda_handler(event, context):
    personName = event['name']
    personPhoneNumber = event['number']

    collectionId = 'rekVideoBlog'
    frameName = "frame.jpg"

    rekognition = rekognition = boto3.client('rekognition')
    try:
        rekognitionIndexResponse = rekognition.index_faces(CollectionId=collectionId, 
                                    Image={'S3Object': {'Bucket':'uploadbucket123','Name':frameName}},
                                    ExternalImageId=frameName,
                                    MaxFaces=1,
                                    QualityFilter="AUTO",
                                    DetectionAttributes=['ALL'])
    except:
        return {
        'statusCode': 500,
        'body': 'Internal Server Error'
        }

    faceId = ''
    for eachFaceRecord in rekognitionIndexResponse['FaceRecords']:
         faceId = eachFaceRecord['Face']['FaceId']
    
    print(faceId)
    
    dynamoClient = boto3.resource('dynamodb')
    visitorTable = dynamoClient.Table('visitors')    

    #Create a photos array with person information
    rekognitionBucket = "rekognitionbucket11"
    photos = []
    photoDictionary = {}
    object_key = str(faceId) + str(personName) + ".jpg"
    createdTimeStamp = int(time.time())
    photoDictionary["objectKey"] = object_key
    photoDictionary["bucket"] = buckrekognitionBucketet
    photoDictionary["createdTimeStamp"] = createdTimeStamp
    
    photos.append(photoDictionary)

    #append the visitor to the visitors dynamoDB
    visitorTable.put_item(
        Item={
                "name": personName,
                "faceId" : faceId,
                "phoneNumber" : personPhoneNumber,
                "photos" : photos
            } 
    )

    s3 = boto3.resource('s3')
    copySrc = {
      'Bucket': 'uploadbucket123',
      'Key': frameName
    }
    known_visitors_bucket = s3.Bucket('rekognitionbucket11')
    known_visitors_bucket.copy(
            copySrc, object_key
        )

    otp = generateOTP(faceId, int(time.time()+30))
    sendSNS(otp)

    return {
        'statusCode': 200,
        'body': json.dumps('Success')
    }

#generate a 6 digit otp
def generateOTP(faceId, expirationTime):
    dynamo_client = boto3.resource('dynamodb')
    otpTable = dynamo_client.Table('passcodes')

    otp=""
    for i in range(6):
        otp+=str(random.randint(1,9))

    otpTable.put_item(
        Item={
            "uName": "Visitor",
            "faceId" : faceId,
            "otp" : otp,
            "expirationTime" : int(expirationTime)} 
    )

    return otp

def sendSNS(otp):
    returning_visitor_arn = "arn:aws:sns:us-west-2:410179727992:returning_visitor"
    sns = boto3.client("sns")
    msg = "Your One Time Password is " + str(otp) + " Enter it in this link.  " + "http://visitorui.s3-website-us-west-2.amazonaws.com"
    sub = "Your Smart Gate OTP"
    response = sns.publish(
    TopicArn=returning_visitor_arn,
    Message=msg,
    Subject=sub
    ) 
    print("sns sent" + json.dumps(response))