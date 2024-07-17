from aws_cdk import NestedStack, Duration, Aws
from aws_cdk import aws_kms as kms
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sns_subscriptions as subscriptions
from aws_cdk import aws_cloudwatch as cloudwatch
from aws_cdk.aws_cloudwatch_actions import SnsAction
from constructs import Construct

class AlertStack(NestedStack):
    def __init__(self, scope: Construct, construct_id: str, web_acl_name, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create a KMS key for encrypting SNS messages and CloudWatch logs
        sns_kms_key = kms.Key(self, "SnsKmsKey",
            description="KMS Key for encrypting SNS messages and CloudWatch logs",
            enable_key_rotation=True
        )

        # Allow CloudWatch to use this KMS key
        sns_kms_key.add_to_resource_policy(iam.PolicyStatement(
            actions=[
                "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
                "kms:GenerateDataKey*", "kms:DescribeKey"
                ],
            principals=[iam.ServicePrincipal("cloudwatch.amazonaws.com")],
            resources=["*"]
        ))

        # Similarly, you may need to allow other services or specific roles to use this key
        sns_kms_key.add_to_resource_policy(iam.PolicyStatement(
            actions=[
                "kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*",
                "kms:GenerateDataKey*", "kms:DescribeKey"
                ],
            principals=[iam.ServicePrincipal("sns.amazonaws.com")],  # For SNS
            resources=["*"]
        ))

        # Create an encrypted SNS topic
        topic = sns.Topic(self, "EncryptedSnsTopic",
            display_name="My Encrypted SNS Topic",
            master_key=sns_kms_key  # Assign the KMS key for encryption
        )

        # Subscribe an email address to the encrypted topic
        email = self.node.try_get_context("email")
        topic.add_subscription(subscriptions.EmailSubscription(email))

        # Setup a CloudWatch alarm to notify via the encrypted SNS topic
        alarm = cloudwatch.Alarm(self, "WafBlockedRequestsAlarm",
            metric=cloudwatch.Metric(
                namespace="AWS/WAFV2",
                metric_name="BlockedRequests",
                dimensions_map={
                    "Region": Aws.REGION,
                    "WebACL": web_acl_name
                },
                statistic="Average",
                period=Duration.minutes(5)
            ),
            threshold=1,
            evaluation_periods=1,
            comparison_operator=cloudwatch.ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
            treat_missing_data=cloudwatch.TreatMissingData.NOT_BREACHING,
            alarm_description= (
                "Alert requests blocked by WAF, potential exploitation."
                "Please investigate the sources."
            )
        )

        # Add SNS topic as the alarm action
        alarm.add_alarm_action(SnsAction(topic))
