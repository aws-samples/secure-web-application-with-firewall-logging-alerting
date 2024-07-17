import json

def lambda_handler(event, context):
    return {
        'statusCode': 200,
        'body': json.dumps(
            'From Cdk stacks for security automation - '
            'Lambda RestApi enabled with WafACL with rules specified in json config file,'
            'enabled with logging, and alerting on potential exploitation.'
            )
    }
