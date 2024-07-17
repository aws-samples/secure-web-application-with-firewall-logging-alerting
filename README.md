
# Welcome to CDK for security automation - Waf, logging and alerting

Securing public facing web applications is critical for business. This solution includes the following components:
•	Deploy WafAcl with a Jason configuration file. The configuration file can be customized for customer specification, such as managed rules, excluded rules, internal CIDR, block list and etc. There is no need to change the code when changing rules and configuration. This standardizes and expedites the deployment.
•	Deploy logging with Kinesis Firehose and S3 bucket
•	Deploy alerting when potential exploitation happens

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .venv
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .venv/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .venv\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

## Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
