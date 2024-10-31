AWS Multi-Agent Infrastructure Deployment System
Overview
This project is a Python-based AWS infrastructure deployment system that uses a multi-agent structure to automate the creation, management, and deletion of AWS resources. Designed to simplify complex infrastructure requests, this system allows users to specify their requirements via natural language prompts. Using AWS services like EC2, S3, RDS, Lambda, API Gateway, CloudFront, CloudFormation, and Elastic Load Balancing (ELB), the system can deploy multiple infrastructure components in a single operation.
![{5709AF97-CA95-4C21-903A-C53802A23754}](https://github.com/user-attachments/assets/ef3b9c28-8c5d-4337-923e-32b38afd6840)
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
CloudFront: Set up content distribution with custom settings.
Example Usage
"Deploy all infrastructure required for my web app with an EC2 web server, S3 storage, RDS database, and ELB load balancing.
//learning from the project:
1)fine tuned models are too unstable for production
