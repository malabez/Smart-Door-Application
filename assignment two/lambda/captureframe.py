import json
import sys
sys.path.insert(1, '/opt')
import cv2
import boto3
import base64
from botocore.vendored import requests
import random
import time

def lambda_handler(event, context):
    # TODO implement
    #get the kvs stream
    kvs_client = boto3.client('kinesisvideo')
    kvs_datapoint = kvs_client.get_data_endpoint(
    StreamARN = 'arn:aws:kinesisvideo:us-west-2:540692873434:stream/LiveRekognitionVideoAnalysisBlog/1573361946683', # kinesis stream arn
    APIName = 'GET_MEDIA'
    )
    
    print(kvs_datapoint)
    
    endpoint = kvs_datapoint['DataEndpoint']
    kvsVideoClient = boto3.client('kinesis-video-media', endpoint_url=endpoint, region_name='us-west-2') # provide your region
    retRecord = event['Records'][0]
    payload = base64.b64decode(retRecord["kinesis"]["data"])
    payloadObject=json.loads(payload)
    fragNum = payloadObject["InputInformation"]["KinesisVideo"]["FragmentNumber"]
    KVS_Stream = kvsVideoClient.get_media(
        StreamARN='arn:aws:kinesisvideo:us-west-2:540692873434:stream/LiveRekognitionVideoAnalysisBlog/1573361946683', # kinesis stream arn
        StartSelector={'StartSelectorType': 'FRAGMENT_NUMBER', 'AfterFragmentNumber': fragNum} 
    )
    print(KVS_Stream)
    
    #parse the video file and extract a frame to identify the people in the camera
    with open('/tmp/streams.mkv', 'wb') as f:
        streamBody = KVS_Stream['Payload'].read(1024*2048)
        f.write(streamBody)
        # use openCV to get a frame
        cap = cv2.VideoCapture('/tmp/streams.mkv')

        # Check to see if the frame has a recognizable person, using bounding box or median'th frame of the video
        ret, frame = cap.read() 
        cv2.imwrite('/tmp/frame.jpg', frame)
        s3_client = boto3.client('s3')
        s3_client.upload_file(
            '/tmp/frame.jpg',
            'captureframe', # replace with your bucket name
            'frame.jpg'
        )
        cap.release()
        print('Image uploaded')

    
    rekognition = boto3.client('rekognition')
    s3 = boto3.resource(service_name='s3')
    bucket = s3.Bucket('facecollectionhw2')#all the valid faces are kept in this bucket
    targetResponse = requests.get('https://captureframe.s3-us-west-2.amazonaws.com/frame.jpg')
    targetResponseContent = targetResponse.content
    print(targetResponseContent)

    recognizedImageKey = ''
    faceId = ''
    collectionId = 'rekVideoBlog'
    for obj in bucket.objects.all():
        # Compare frame captured from webcam to the image in S3 bucket.
        #print (obj.name)
        recognizedImageKey = obj.key
        print (obj.key)
        url = "https://{0}.s3-us-west-2.amazonaws.com/{1}".format("facecollectionhw2", obj.key)
        print (url)
        sourceResponse = requests.get(url)
        sourceResponseContent = sourceResponse.content
        rekognitionResponse = rekognition.compare_faces(SourceImage={'Bytes': sourceResponseContent}, TargetImage={'Bytes': targetResponseContent}) 

        rekognitionIndexResponse = rekognition.index_faces(CollectionId=collectionId, Image={ 'S3Object': {'Bucket':'facecollectionhw2','Name':recognizedImageKey} })
        for faceRecord in rekognitionIndexResponse['FaceRecords']:
         faceId = faceRecord['Face']['FaceId']

        #print (rekognition_response)
    
    faceMatchConfidence = 0
    
    #this is grabbing the confidence percentage of the person's face with the matches in the s3 bucket
    for eachFaceMatch in rekognitionResponse['FaceMatches']:
        faceMatchConfidence = int(eachFaceMatch['Face']['Confidence'])
    
    #if the confidence is within 70%, then we will accept that the face matches, and send them an OTP
    if faceMatchConfidence and faceMatchConfidence>70:
        print("A facematch exists!")
        otp=""
        for i in range(6):
            otp+=str(random.randint(1,9))
        print ("The One Time Password is: ")
        print (otp)
        expirationTime = time.time() + 300 #5 min TTL

        dynamoClient = boto3.resource('dynamodb')
        otpTable = dynamoClient.Table('passcodes')

        otpTable.put_item(
            Item={
                "uName": "Visitor",
                "faceId" : faceId,
                "otp" : int(otp),
                "expirationTime" : int(expirationTime)} 
        )

        returningVisitor_arn = "arn:aws:sns:us-west-2:540692873434:returningvisitor"
        sns = boto3.client("sns")
        msg = "Your One Time Password is " + str(otp) + " Enter it in this link.  " + "http://visitorui.s3-website-us-west-2.amazonaws.com"
        sub = "Your Smart Gate OTP"
        response = sns.publish(
        TopicArn=returningVisitor_arn,
        Message=msg,
        Subject=sub
        ) 
        print("sns sent" + json.dumps(response))
    
    #if the match confidence is below 70%, then we treat it as no match, i.e. not a valid person
    else:
        print("faces dont MATCHH")
        returningVisitor_arn = "arn:aws:sns:us-west-2:540692873434:newvisitor"
        sns = boto3.client("sns")
        msg = "1 unknown visitor" + "https://captureframe.s3-us-west-2.amazonaws.com/frame.jpg" 
        sub = "Unknown Visitor Alert"
        response = sns.publish(
        TopicArn=returningVisitor_arn,
        Message=msg,
        Subject=sub
        ) 
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!')
    }