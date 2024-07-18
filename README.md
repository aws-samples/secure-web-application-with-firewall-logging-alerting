**Secure Web Applications with WAF Logging and Monitoring**

**Summary**

Securing public facing web applications is critical for business. 
This solution includes reusable stacks that can be customized for specific implementation to secure public facing web applications. It includes the following components: 
1) WafAcl reading rule configuration from a json file. The configuration file can be customized for specific requirements, such as managed rules, excluded rules, block list and etc. The idea is to limit code change when there is a need to change rule configuration. This standardizes and expedites the deployment. 
2) Logging with Kinesis Firehose and S3 bucket. 
3) Alerting on unusual blocks that need human investigation. 
4) A parallel stack to deploy API gateway for testing, which can be replaced by AppSync, CloudFront, or ALB.

**Prerequisites and limitations**

1)	Work with customer on the requirement and specification of Waf rules. This artifact provides a sample Waf stack and rule configuration file – waf-rules.json for WafAcl with default action of “allow”. That can be modified based on specific customer requirements. 
2)	Work with customer on the requirement and specification of alerting, such as threshold and recipients. This artifact provides a sample alerting stack and configuration, which can be modified for specific requirements.
3)	Create a CDK project and add app configuration. This artifact provides a sample CDK project that creates a Waf stack with rules and logging configurations, a nested alerting stack and a parallel testing stack. That can be reused and customized for specific requirements.
4)	Install code qualification tools and qualify the code. This artifact provides requirement.dev.txt for the installation and passed quality checks. You may add more qualification checks here for specific requirements
5)	Build CI/CD to deploy the stacks, or deploy with command line. This artifact provides a sample buildspec and can be deployed to multiple accounts and regions. Account and region are input from environment context.

**Target technology stack**
1) AWS WAF
2) Amazon API Gateway
3) AWS Lambda
4) Amazon Kinesis Data Firehose
5) Amazon S3
6) Amazon CloudWatch
7) Alarm
9) Amazon SNS
10) IAM
11) AWS KMS

**Epics**
1) WAF rule requirement and specification
    Define WAF rules in the format of json. Customize waf-rules.json in the artifact

2) Alerting requirement and specification
    Define alerting threshold and recipient. Customize the alert stack and ckd.json in the artifact

3) Create the CDK project (linux, python)

    mkdir cdk_waf && cd cdk_waf
    cdk init sample-app --language python
    python3 -m venv .venv
    source .venv/bin/activate
    pip3 install -r requirements.txt

4) Add app configuration

    Add stack code
    Cdk_waf_stack.py
    AlertStack.py
    LambdaApi.py

    Add lambda function code
    Handler.py

    Add waf-fule.json

    Modify cdk.json

    Modify app.py

5) Qualify the code
    Add pylint and safety
    pip3 install -r requirements-dev.txt

    Run pylint

    pylint --generate-rcfile > .pylintrc
    python3 -m pylint cdk_waf
    python3 -m pylint app.py

    Run dependency checks

    safety check -r requirements.txt
    safety check -r requirements-dev.txt

    Install cfn_nag

    sudo yum install ruby
    gem install cfn-nag

    Run security checks on stacks

    cdk synth -c account=$ACCOUNT -c environmentType=qa  CdkWafStack >> template.yaml
    cfn_nag_scan --input-path template.yaml 

6) Deploy

    export REGION=$(aws configure get region)
    export ACCOUNT=$(aws sts get-caller-identity | jq -r .Account)

    cdk bootstrap aws://$ACCOUNT/$REGION -c account=$ACCOUNT -c environmentType=qa

    cdk deploy -c account=$ACCOUNT -c environmentType=qa --all
