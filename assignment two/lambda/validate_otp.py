import json
import boto3
from boto3.dynamodb.conditions import Key, Attr


def lambda_handler(event, context):
    # TODO implement
    otp_dynamodb = 'passcodes'
    app_region = 'us-west-2'
    dynamodb= boto3.resource('dynamodb',region_name=app_region)
    dynamodb_otp_table= dynamodb.Table(otp_dynamodb)
    print(event['message'])
    responseData = dynamodb_otp_table.query(IndexName="otp-index", KeyConditionExpression=Key('otp').eq(str(event['message'])))
    #print(responseData)
    items = responseData.get("Items")
    personName = ""
    faceId = ""
    theResponse = {}

    
    for each_item in items:
        personName = str(each_item["uName"])
        faceId = str(each_item["faceId"])
    
    #if there is more than one response in responseData then we take the username and faceid, and return them
    if responseData and len(responseData['Items']) >= 1:
        visitor_name = getVisitorName(faceId)
        theResponse['name'] = personName
        response_body['visitorName'] = visitor_name
        
        #json_data = json.dumps(theResponse)
        #return the username and faceid
        return {
        'statusCode': 200,
        #'body': json_data
        'body': response_body
        }
    
    #Otherwise, if there is no response for name/id, the OTP is wrong
    return {
        'statusCode': 400,
        'body': "Invalid OTP"
    }

def getVisitorName(faceId):
    visitor_table_name = 'visitors'
    app_region = 'us-west-2'
    dynamodb = boto3.resource('dynamodb',region_name=app_region)
    print(faceId)
    visitor_table = dynamodb.Table(visitor_table_name)
    visitorResponseData = visitor_table.query(KeyConditionExpression=Key('faceId').eq(faceId))
    print (visitorResponseData)
    visitorResponseItems = visitorResponseData["Items"]
    
    visitorData = visitorResponseItems[0]
    visitorName = visitorData["name"]
    return visitorName   
