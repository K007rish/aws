AWS ECS Frontend & Backend

Flask backend and frontend deployed as Docker containers on Amazon ECS Fargate. Images are stored in Amazon ECR. ECS tasks run in private subnets and traffic is handled through security groups and an Application Load Balancer.

URLs

Frontend: https://fr-6d38e511685743ccb8a4b3448685e434.ecs.ap-south-1.on.aws/

Backend API: http://52.66.238.11:8000/api

Architecture

Internet
   |
   v
Application Load Balancer
   |
   +----------------------+
   |                      |
   v                      v
Frontend ECS           Backend ECS
:3000                  :8000
   |                      |
   +------ API ------------+

ECS tasks are placed in private subnets. The ALB is placed in public subnets.

Prerequisites

AWS CLI and Docker should be installed and configured.

aws --version
docker --version
aws sts get-caller-identity
aws configure

Set the region:

aws configure set region ap-south-1

Get the AWS account ID:

aws sts get-caller-identity --query Account --output text

Docker Images

Backend

cd backend

docker build -t backend -f Dockerfile.backend .

docker run -d --name backend -p 8000:8000 backend

docker ps
docker logs backend

curl http://localhost:8000/api

Frontend

cd ../frontend

docker build -t frontend .

docker run -d --name frontend -p 3000:3000 frontend

docker ps
docker logs frontend

After local testing:

docker stop backend frontend
docker rm backend frontend

ECR

Create the repositories:

aws ecr create-repository --repository-name backend --region ap-south-1
aws ecr create-repository --repository-name frontend --region ap-south-1

Login to ECR:

aws ecr get-login-password --region ap-south-1 | docker login --username AWS --password-stdin <AWS_ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com

Set the registry value for the following commands:

export AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
export ECR_REGISTRY=$AWS_ACCOUNT_ID.dkr.ecr.ap-south-1.amazonaws.com

Backend image

docker tag backend:latest $ECR_REGISTRY/backend:latest
docker push $ECR_REGISTRY/backend:latest

Frontend image

docker tag frontend:latest $ECR_REGISTRY/frontend:latest
docker push $ECR_REGISTRY/frontend:latest

Check the images:

aws ecr list-images --repository-name backend --region ap-south-1
aws ecr list-images --repository-name frontend --region ap-south-1

ECS

Create the cluster:

aws ecs create-cluster   --cluster-name frontend-backend-cluster   --region ap-south-1

Check it:

aws ecs list-clusters --region ap-south-1

VPC and Subnets

The deployment uses the following layout:

VPC
|
+-- Public Subnet
|     |
|     +-- Application Load Balancer
|
+-- Private Subnet 1
|     |
|     +-- Frontend ECS Task
|     +-- Backend ECS Task
|
+-- Private Subnet 2
      |
      +-- ECS tasks when required

For Fargate tasks in private subnets:

assignPublicIp = DISABLED

Private subnet routing must provide the required outbound connectivity. Depending on the setup, this can be through a NAT Gateway and/or VPC endpoints.

Security Groups

The security groups are separated so that containers are not directly exposed unnecessarily.

ALB security group:

HTTP  80   -> 0.0.0.0/0
HTTPS 443  -> 0.0.0.0/0

Frontend ECS security group:

TCP 3000 -> ALB security group

Backend ECS security group:

TCP 8000 -> Frontend ECS security group

Example rules:

aws ec2 authorize-security-group-ingress   --group-id <FRONTEND_SG_ID>   --protocol tcp   --port 3000   --source-group <ALB_SG_ID>   --region ap-south-1

aws ec2 authorize-security-group-ingress   --group-id <BACKEND_SG_ID>   --protocol tcp   --port 8000   --source-group <FRONTEND_SG_ID>   --region ap-south-1

ECS Task Definitions

The task definitions contain the ECR image and container port.

Backend:

Image: <AWS_ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/backend:latest
Container port: 8000

Frontend:

Image: <AWS_ACCOUNT_ID>.dkr.ecr.ap-south-1.amazonaws.com/frontend:latest
Container port: 3000

Register a task definition:

aws ecs register-task-definition   --cli-input-json file://task-definition.json   --region ap-south-1

ECS Services

Run the services in the private subnets with public IP assignment disabled.

Frontend:

aws ecs create-service   --cluster frontend-backend-cluster   --service-name frontend-service   --task-definition frontend-task   --desired-count 1   --launch-type FARGATE   --network-configuration "awsvpcConfiguration={subnets=[<PRIVATE_SUBNET_1>,<PRIVATE_SUBNET_2>],securityGroups=[<FRONTEND_SG_ID>],assignPublicIp=DISABLED}"   --region ap-south-1

Backend:

aws ecs create-service   --cluster frontend-backend-cluster   --service-name backend-service   --task-definition backend-task   --desired-count 1   --launch-type FARGATE   --network-configuration "awsvpcConfiguration={subnets=[<PRIVATE_SUBNET_1>,<PRIVATE_SUBNET_2>],securityGroups=[<BACKEND_SG_ID>],assignPublicIp=DISABLED}"   --region ap-south-1

Check the services:

aws ecs list-services   --cluster frontend-backend-cluster   --region ap-south-1

aws ecs describe-services   --cluster frontend-backend-cluster   --services frontend-service backend-service   --region ap-south-1

Check running tasks:

aws ecs list-tasks   --cluster frontend-backend-cluster   --desired-status RUNNING   --region ap-south-1

Load Balancer

The ALB handles public access while the ECS tasks remain in private subnets.

Recommended listener/target-group setup:

ALB :80
 |
 +-- /       -> frontend target group -> :3000
 |
 +-- /api/*  -> backend target group  -> :8000

With this setup the frontend does not need to know the backend task's private or public IP.

The frontend can use:

/api

instead of:

http://<backend-public-ip>:8000/api

Updating an Image

Build and push the changed image:

docker build -t backend -f backend/Dockerfile.backend backend
docker tag backend:latest $ECR_REGISTRY/backend:latest
docker push $ECR_REGISTRY/backend:latest

Deploy it:

aws ecs update-service   --cluster frontend-backend-cluster   --service backend-service   --force-new-deployment   --region ap-south-1

For the frontend:

docker build -t frontend frontend
docker tag frontend:latest $ECR_REGISTRY/frontend:latest
docker push $ECR_REGISTRY/frontend:latest

aws ecs update-service   --cluster frontend-backend-cluster   --service frontend-service   --force-new-deployment   --region ap-south-1

Troubleshooting

Check ECS service events:

aws ecs describe-services   --cluster frontend-backend-cluster   --services frontend-service backend-service   --region ap-south-1   --query 'services[].events[0:10]'

Check task details:

aws ecs describe-tasks   --cluster frontend-backend-cluster   --tasks <TASK_ARN>   --region ap-south-1

Check CloudWatch log groups:

aws logs describe-log-groups --region ap-south-1

When a task is unhealthy, check these in order:

ECR image
   ↓
Task definition
   ↓
ECS task status
   ↓
Container logs
   ↓
Security groups
   ↓
Private subnet routing
   ↓
Target group health
   ↓
ALB listener/rules

Testing

Frontend:

https://fr-6d38e511685743ccb8a4b3448685e434.ecs.ap-south-1.on.aws/

Backend:

http://52.66.238.11:8000/api

curl http://52.66.238.11:8000/api

Cost Check

Before leaving the environment running, check:

ECS services/tasks
Load balancers
NAT Gateways
Elastic IPs
ECR images
CloudWatch logs
EC2 instances
EBS volumes