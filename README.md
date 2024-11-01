AWS Multi-Agent Infrastructure Deployment System
Overview
This project is a Python-based AWS infrastructure deployment system that uses a multi-agent structure to automate the creation, management, and deletion of AWS resources. Designed to simplify complex infrastructure requests, this system allows users to specify their requirements via natural language prompts. Using AWS services like EC2, S3, RDS, Lambda, API Gateway, CloudFront, CloudFormation, and Elastic Load Balancing (ELB), the system can deploy multiple infrastructure components in a single operation.
System Archi:
![{204AE712-ECF7-4DC5-9E09-A9D330D506C0}](https://github.com/user-attachments/assets/3d996dcb-a10d-434e-b01d-f3104af6458c)



This project leverages:

LangChain for language model management,
Boto3 for AWS service integration, and
Streamlit for an intuitive web interface.
Key Features
Multi-Agent System: Uses separate agents for each AWS service, managed by a master decision agent.
AWS Service Integration: Supports EC2, S3, RDS, Lambda, API Gateway, CloudFront, CloudFormation, and ELB, with customizable configurations.
System State Management: Tracks and stores resource IDs and configurations, allowing seamless reuse of components across requests.
Federated Authentication: Uses AWS Cognito for user authentication, enabling users to log in with AWS or social identity providers.
Frontend Interface: Provides an interactive interface built with Streamlit for user input and resource status visualization.
AWS Services and Tools
Supported Services and Tools
EC2: Create VPCs, subnets, security groups, and instances.
S3: Create buckets, upload files, and delete objects.
RDS: Create and modify database instances.
Lambda: Deploy serverless functions.
API Gateway: Set up REST APIs.
CloudFormation: Deploy entire stacks based on JSON or YAML templates.
Elastic Load Balancer (ELB): Manage traffic with load balancing.
Output:

![{1DE77D53-1037-4532-B11A-63610ED3869D}](https://github.com/user-attachments/assets/f5e22427-b3ca-4172-bd10-ec295d89f17a)
1)got bored after this,fine tuned model is not good enough,ending the project GG.

CloudFront: Set up content distribution with custom settings.
Example Usage
"Deploy all infrastructure required for my web app with an EC2 web server, S3 storage, RDS database, and ELB load balancing.
#future scope
1)fine tuned models are too unstable for production
2)bigger finetuning dataset
3)alot of testing
4)include other aws products 
