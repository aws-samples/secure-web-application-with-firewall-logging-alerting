"""
Deploy Lambda RestApi stack and WafAcl stack with a nested stack of alerting
"""

#!/usr/bin/env python3
#import os
#import aws_cdk as cdk
from aws_cdk import App, Environment
from cdk_waf.LambdaApi import LambdaApi
from cdk_waf.cdk_waf_stack import CdkWafStack

app = App()

environment_type = app.node.try_get_context("environmentType")
environment_context = app.node.try_get_context(environment_type)
region = environment_context["region"]
account = app.node.try_get_context("account")
tags = environment_context["tags"]
stack_name = f'{app.node.try_get_context("prefix")}-{environment_type}'

lambda_stack = LambdaApi(
    app,
    stack_name,
    env = Environment(
        account = account,
        region = region
    ),
    tags=tags
)

api_arn = lambda_stack.api_arn_output.value

CdkWafStack(
    app,
    "CdkWafStack", 
    api_arn = lambda_stack.api_arn_output.value,
    env = Environment(
        account = account,
        region = region
    ),
    tags=tags
)

app.synth()
