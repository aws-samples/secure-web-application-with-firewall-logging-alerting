import json
from aws_cdk import Stack
from aws_cdk import aws_wafv2 as waf
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_kinesisfirehose as firehose
from aws_cdk import aws_iam as iam
from aws_cdk import aws_kms as kms
from constructs import Construct
from .AlertStack import AlertStack


class CdkWafStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, api_arn, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        kms_key = kms.Key(self, "FirehoseKmsKey",
            alias="alias/firehoseKmsKey",
            description="KMS Key for encrypting Firehose data",
            enable_key_rotation=True
        )

        log_bucket = s3.Bucket(self, "WafLogsBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,  # Enable S3 managed encryption
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL  # Block public access
        )

        # Define the bucket policy to enforce SSL
        bucket_policy = iam.PolicyStatement(
            actions=["s3:*"],
            effect=iam.Effect.DENY,
            principals=[iam.StarPrincipal()],
            resources=[
                log_bucket.bucket_arn,
                f"{log_bucket.bucket_arn}/*"
            ],
            conditions={
                "Bool": {"aws:SecureTransport": "false"}
            }
        )

        log_bucket.add_to_resource_policy(bucket_policy)

        # Create an IAM role for Firehose with restricted permissions
        firehose_role = iam.Role(self, "FirehoseDeliveryRole",
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
            inline_policies={
                "RootPolicy": iam.PolicyDocument(statements=[
                iam.PolicyStatement(
                    actions=["s3:Abort*", "s3:PutObject", "s3:ListBucket"],
                    resources=[log_bucket.bucket_arn, log_bucket.arn_for_objects("*")],
                    effect=iam.Effect.ALLOW
                    ),
                iam.PolicyStatement(
                    actions=[
                        "kms:Decrypt",
                        "kms:Encrypt",
                        "kms:GenerateDataKey"
                        ],
                    resources=[kms_key.key_arn],
                    effect=iam.Effect.ALLOW
                    )
                ])
            }
        )

        log_delivery_stream = firehose.CfnDeliveryStream(
            self, "WafLogDeliveryStream",
            delivery_stream_name="aws-waf-logs-" + construct_id,
            delivery_stream_type="DirectPut",
            s3_destination_configuration=(
                firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                    bucket_arn=log_bucket.bucket_arn,
                    buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                        interval_in_seconds=300,
                        size_in_m_bs=5
                        ),
                    compression_format="GZIP",
                    role_arn=firehose_role.role_arn,
                    encryption_configuration=firehose.CfnDeliveryStream.EncryptionConfigurationProperty(
                        kms_encryption_config=firehose.CfnDeliveryStream.KMSEncryptionConfigProperty(
                        awskms_key_arn=kms_key.key_arn
                            )
                        )
                    )
            )
        )

        # Load configurations from JSON file
        with open('waf-rules.json', 'r', encoding='utf-8') as file:
            config = json.load(file)

        # Define the IP Set for blocking specific IPs
        ip_set = waf.CfnIPSet(
            self, "MyIPSet",
            addresses=config["blockedIPs"],
            ip_address_version="IPV4",
            scope="REGIONAL",
            name="BlockedIPs"
        )

        # Initialize the list of rules
        waf_rules = []

        # Iterate over rules defined in the JSON file
        for rule_key, rule_details in config["rules"].items():
            if rule_key == "IPBlockRule":
                # Create rule to block the specified IPs
                statement = waf.CfnWebACL.StatementProperty(
                    ip_set_reference_statement=waf.CfnWebACL.IPSetReferenceStatementProperty(
                        arn=ip_set.attr_arn
                    )
                )
                action_prop = waf.CfnWebACL.RuleActionProperty(block={})
                metric_name = rule_details["metricName"]
                priority = rule_details["priority"]
                waf_rules.append(waf.CfnWebACL.RuleProperty(
                name=rule_key,
                priority=priority,
                action=action_prop,
                statement=statement,
                visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                    cloud_watch_metrics_enabled=True,
                    metric_name=metric_name,
                    sampled_requests_enabled=True
                )
            ))
            else:
                # Managed rule configuration
                excluded_rules = [
                    waf.CfnWebACL.ExcludedRuleProperty(name=rule_name)
                    for rule_name in rule_details["excludedRules"]
                    ]
                statement = waf.CfnWebACL.StatementProperty(
                    managed_rule_group_statement=waf.CfnWebACL.ManagedRuleGroupStatementProperty(
                        vendor_name=rule_details["vendorName"],
                        name=rule_details["name"],
                        excluded_rules=excluded_rules
                    )
                )
                metric_name = rule_details["metricName"]
                priority = rule_details["priority"]
                waf_rules.append(waf.CfnWebACL.RuleProperty(
                name=rule_key,
                priority=priority,
                override_action=waf.CfnWebACL.OverrideActionProperty(none={}),
                statement=statement,
                visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                    cloud_watch_metrics_enabled=True,
                    metric_name=metric_name,
                    sampled_requests_enabled=True
                )
            ))

        web_acl_name = "CdkWebACL"

        # Create the Web ACL
        web_acl = waf.CfnWebACL(
            self, "CdkWebACL",
            scope="REGIONAL",
            default_action=waf.CfnWebACL.DefaultActionProperty(allow={}),
            visibility_config=waf.CfnWebACL.VisibilityConfigProperty(
                cloud_watch_metrics_enabled=True,
                metric_name='WebACLMetrics',
                sampled_requests_enabled=True
            ),
            rules=waf_rules,
            name= web_acl_name
        )

        waf.CfnWebACLAssociation(
           self, "WebACLAssociation",
           resource_arn=api_arn,
           web_acl_arn=web_acl.attr_arn
        )

        waf.CfnLoggingConfiguration(
            self, "WafLoggingConfiguration",
            log_destination_configs=[log_delivery_stream.attr_arn],
            resource_arn=web_acl.attr_arn
        )

        AlertStack(
            self,
            "AlertStack", 
            web_acl_name = web_acl_name
        )
