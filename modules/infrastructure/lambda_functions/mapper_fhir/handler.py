import json
import os
import boto3

DATASTORE_ID = os.environ.get('DATASTORE_ID')
REGION = os.environ.get('REGION')
CREATE_RESOURCE_LAMBDA = os.environ.get('CREATE_RESOURCE_LAMBDA')
MODIFY_RESOURCE_LAMBDA = os.environ.get('MODIFY_RESOURCE_LAMBDA')

lambda_client = boto3.client('lambda', region_name=REGION)

def lambda_handler(event, context):
    http_method = event.get('httpMethod', '')
    
    try:
        if http_method == 'POST':
            body = json.loads(event.get('body', '{}'))
            
            response = lambda_client.invoke(
                FunctionName=CREATE_RESOURCE_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps({'body': body, 'datastore_id': DATASTORE_ID})
            )
            
            result = json.loads(response['Payload'].read())
            
            return {
                'statusCode': 201,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps(result)
            }
        
        elif http_method == 'PUT':
            body = json.loads(event.get('body', '{}'))
            
            response = lambda_client.invoke(
                FunctionName=MODIFY_RESOURCE_LAMBDA,
                InvocationType='RequestResponse',
                Payload=json.dumps({'body': body, 'datastore_id': DATASTORE_ID})
            )
            
            result = json.loads(response['Payload'].read())
            
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps(result)
            }
        
        elif http_method == 'GET':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'message': 'Mapper FHIR - GET', 'datastore': DATASTORE_ID})
            }
        
        elif http_method == 'DELETE':
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': json.dumps({'message': 'DELETE operation'})
            }
        
        elif http_method == 'OPTIONS':
            return {
                'statusCode': 200,
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET,POST,PUT,DELETE,OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                },
                'body': ''
            }
        
        else:
            return {
                'statusCode': 405,
                'headers': {
                    'Content-Type': 'application/json',
                    'Access-Control-Allow-Origin': '*'
                },
                'body': json.dumps({'error': 'Method not allowed'})
            }
    
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({'error': str(e)})
        }
