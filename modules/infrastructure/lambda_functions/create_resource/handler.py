import json
import os
import boto3

DATASTORE_ID = os.environ.get('DATASTORE_ID')
REGION = os.environ.get('REGION')

healthlake = boto3.client('healthlake', region_name=REGION)

def lambda_handler(event, context):
    try:
        body = event.get('body', {})
        datastore_id = event.get('datastore_id', DATASTORE_ID)
        
        # Aquí iría la lógica para crear el recurso en HealthLake
        
        return {
            'message': 'Resource created successfully',
            'datastore_id': datastore_id,
            'resource': body
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'message': 'Failed to create resource'
        }
