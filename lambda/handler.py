import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(
            'From Cdk stacks for security automation - '
            'Enabled WafACL with rules specified in a json config file.'
            'Enabled logging with Kinesis Firehose and S3. '
            'Alert on potential exploitation.'
            )
    }
