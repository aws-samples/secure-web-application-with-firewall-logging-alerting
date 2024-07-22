from datetime import datetime
from constructs import Construct
from aws_cdk import Stack, RemovalPolicy, CfnOutput, Fn, Aws
from aws_cdk.aws_lambda import Function, Runtime, Code, Alias, VersionOptions
from aws_cdk.aws_apigateway import LambdaRestApi, StageOptions
from aws_cdk.aws_cloudwatch import Alarm, ComparisonOperator
from aws_cdk.aws_codedeploy import LambdaDeploymentGroup, LambdaDeploymentConfig

class LambdaApi(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        environment_type = self.node.try_get_context("environmentType")
        context = self.node.try_get_context(environment_type)
        self.alias_name = context["lambda"]["alias"]
        self.stage_name = context["lambda"]["stage"]
        current_date =  datetime.today().strftime('%d-%m-%Y')

        my_lambda = Function(
            scope = self,
            id = "MyFunction",
            function_name= context["lambda"]["name"],
            handler = "handler.lambda_handler",
            runtime = Runtime.PYTHON_3_11,
            code = Code.from_asset("lambda"),
            current_version_options = VersionOptions(
                description = f'Version deployed on {current_date}',
                removal_policy = RemovalPolicy.RETAIN
            )
        )

        new_version = my_lambda.current_version
        new_version.apply_removal_policy(RemovalPolicy.RETAIN)

        alias = Alias(
            scope = self,
            id = "FunctionAlias",
            alias_name = self.alias_name,
            version = new_version
        )

        api = LambdaRestApi(
            scope = self,
            id = "RestAPI",
            handler = alias,
            deploy_options = StageOptions(stage_name=self.stage_name)
        )

        failure_alarm = Alarm(
            scope = self,
            id = "FunctionFailureAlarm",
            metric = alias.metric_errors(),
            threshold = 1,
            evaluation_periods = 1,
            alarm_description = "The latest deployment errors > 0",
            alarm_name = f'{self.stack_name}-alarm',
            comparison_operator = ComparisonOperator.GREATER_THAN_OR_EQUAL_TO_THRESHOLD,
        )

        LambdaDeploymentGroup(
            scope = self,
            id = "ALLOnceDeployment",
            alias = alias,
            deployment_config = LambdaDeploymentConfig.ALL_AT_ONCE,
            alarms = [failure_alarm]
        )

        api_arn = Fn.sub(
            "arn:aws:apigateway:${Region}::/restapis/${ApiId}/stages/${StageName}",
            {
                "Region": Aws.REGION,
                "ApiId": api.rest_api_id,
                "StageName": self.stage_name
            }
        )

        self.api_arn_output = CfnOutput(self, "ApiGatewayArn", value=api_arn)
