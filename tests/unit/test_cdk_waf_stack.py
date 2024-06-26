import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_waf.cdk_waf_stack import CdkWafStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_waf/cdk_waf_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkWafStack(app, "cdk-waf")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
