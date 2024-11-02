from langchain.prompts import BasePromptTemplate
from agents.ec2Agent import EC2Agent
from agents.s3Agent import S3Agent

from agents.apigatewayAgent import APIGatewayAgent
from agents.cloudfromationAgent import CloudFromation
from agents.cloudfront import CloudFront
from agents.rdsAgent import RDSAgent
from agents.lambdaAgent import LambdaAgent
from agents.ELBAgent import ELBAgent

import boto3
import openai
from agents.state_manager import State
import streamlit as st
import json


openai_apikey = ''
client = openai.Client(api_key=openai_apikey)

class DecisionAgent:
    
    def __init__(self, aws_access_key, aws_secret_key, region_name):
        self.session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name,
        )
        self.ec2_client = self.session.client('ec2')
        self.s3_client = self.session.client('s3')
        self.rds_client = self.session.client('rds')
        self.cloudfromation_client = self.session.client('cloudformation')
        self.cloudfront_client = self.session.client('cloudfront')

        self.apigateway_client= self.session.client('apigateway')
        self.lambda_client=self.session.client('lambda')
        self.elb_client=self.session.client('elb')
        self.ec2_agent = EC2Agent(api_key=openai_apikey, ec2_client=self.ec2_client)
        self.s3_agent = S3Agent(api_key=openai_apikey, s3_client=self.s3_client)
        self.rds_agent = RDSAgent(api_key=openai_apikey, rds_client=self.rds_client)
        self.apigateway_agent = APIGatewayAgent(api_key=openai_apikey, apigateway_client=self.apigateway_client)
        self.cloudfromation_agent = CloudFromation(api_key=openai_apikey, cloudfromation_client=self.cloudfromation_client)
        self.cloudfront_agent = CloudFront(api_key=openai_apikey, cloudfront_client=self.cloudfront_client)

        self.lambda_agent = LambdaAgent(api_key=openai_apikey, lambda_client=self.lambda_client)
        self.elb_agent=ELBAgent(api_key=openai_apikey,elb_client=self.elb_client)
        
       
        self.state = State()
        print("Decision agent initialized")

    def process_user_prompt(self, user_input):
        prompt = f'''{user_input}'''




        try:
            messages = [
            {"role": "system", "content": "You are an AWS decision agent. If a user requests an unknown or unsupported AWS service or tool, respond with the following JSON structure exactly: {\"service\": null, \"tool_task\": null, \"message\": \"Request not recognized\"}"},
            {"role": "user", "content": prompt}
    ]
            response = client.chat.completions.create(
                model="ft:gpt-4o-2024-08-06:personal:taskpilot-aws-decision-agent-v3:ANzksRzm",
                messages=messages, # Pass user_input as a string
                temperature=1,
                max_tokens=2048,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
                user="no-cache"
            
            )
            # Extract the JSON response
            decision_result = response.choices[0].message.content.strip()
            

            # Store decision agent result in state
            

            # Print out the global state to verify it's stored correctly
            print('decision_agent_response',decision_result)


            # Parse decision result to determine the appropriate service
            services_and_tools= self.extract_services_and_tool_tasks(decision_result)
            for i in range(0,len(services_and_tools)):
                service_name=services_and_tools[i]['service']
                tool_task=services_and_tools[i]['tool_task']
                self.state.store("decision_agent", service_name, tool_task)
            # Handle the task based on the determined service
                if tool_task=="null" and service_name=="null":
                    message = f"Unsupported AWS service: {service_name}"
                    self.state.store('decision_agent', tool_task, message)
                    return
                if service_name == "ec2":
                    self.ec2_agent.handle_task(tool_task)
                elif service_name == "s3":
                    print('calling s3 agent')
                    self.s3_agent.handle_task(tool_task)
                elif service_name =="cloudfront":
                    self.cloudfront_agent.handle_task(tool_task)
                elif service_name=="rds":
                    self.rds_agent.handle_task(tool_task)
                elif service_name=="apigateway":
                    self.apigateway_agent.handle_task(tool_task)
                elif service_name=="lambda":
                    self.lambda_agent.handle_task(tool_task)
                elif service_name=="elastic_load_balancer":
                    self.elb_agent.handle_task(tool_task)
                else:
                    # Handle unrecognized tools
                    message = f"Unsupported AWS service or tool: {service_name} with task '{tool_task}'"
                    self.state.store("decision_agent", tool_task, message)
                    print(message)
                    return
                    
                    
        
              
                    
                    
        except KeyError as e:
                    error_message = f"KeyError - Missing expected key: {e}"
                    print(error_message)
                    self.state.store("decision_agent_error", "KeyError", error_message)

        except json.JSONDecodeError as e:
                    error_message = f"JSONDecodeError - Invalid JSON response: {e}"
                    print(error_message)
                    self.state.store("decision_agent_error", "JSONDecodeError", error_message)
        except Exception as e:
                    print('ecpection caught')
                    error_message = f"General Error: {e}"
                    print(error_message)
                    self.state.store("decision_agent_error", "Exception", error_message)   

    def extract_services_and_tool_tasks(self,json_response):
        try:
            # Parse the JSON response
            parsed_data = json.loads(json_response)
            
            # Initialize an empty list to store results
            extracted_tasks = []

            # Recursive function to handle nested structures
            def extract_from_item(item):
                print('item',item)
                if isinstance(item, dict): 
                    # If it's a dict, check if it contains 'service' and 'tool_task' fields
                    if 'service' in item and 'tool_task' in item:
                        extracted_tasks.append({
                            'service': item['service'],
                            'tool_task': item['tool_task']
                        })
                elif isinstance(item, list):
                    # If it's a list, recursively extract from each element
                    for elem in item:
                        extract_from_item(elem)

            # Start extraction from the top level of the parsed data
            extract_from_item(parsed_data)

            return extracted_tasks

        except json.JSONDecodeError:
            print("Invalid JSON format")
            return None

    def store_result(self, tool_name, task,message):
        # Store the result in both session state and self.state
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}\n")
        self.state.store('decision_agent',tool_name,task, message)
# Example usage:
# decision_agent = DecisionAgent('<aws_access_key>', '<aws_secret_key>', '<region_name>')
# response = decision_agent.process_user_prompt("I need to store some files and access them globally.")

