# CloudWatch Alarms (API Gateway / ALB / Lambda / RDS)

This CloudFormation template creates an SNS topic and alarms for common service metrics.

- API Gateway 5XX (sum over 5 minutes)
- ALB 5XX (sum over 5 minutes)
- Lambda Errors (sum over 5 minutes)
- RDS CPU Utilization & DB connections

## Deploy

```bash
aws cloudformation deploy \
  --template-file infra/cloudwatch/alarms-apigw-alb-rds.yaml \
  --stack-name seedtest-alarms \
  --parameter-overrides \
    AlertEmail=you@example.com \
    Stack=seedtest \
    UseAPIGateway=true ApiGatewayStage=prod ApiGatewayRestApiId=<rest-api-id> \
    UseALB=false AlbFullName= \
    LambdaFunctionName=<pdf-lambda-name> \
    RdsIdentifier=<db-instance-id> \
  --capabilities CAPABILITY_IAM
```

Set `UseAPIGateway` or `UseALB` per your entrypoint. You can deploy multiple stacks if you have both.
