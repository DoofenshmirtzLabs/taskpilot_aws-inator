import boto3
import openai
from agents.state_manager import State
from botocore.exceptions import ClientError
from langchain_core.output_parsers import JsonOutputParser
from agents.reuseinputsAgent import reuse_inputs
import json
import streamlit as st
state_v1=State()
class CloudFront:
    def __init__(self, api_key, cloudfront_client):
        self.cloudfornt_client = cloudfront_client
        self.client = openai.Client(api_key=api_key)
        self.state = State()
        print("CloudFront agent initialized")

    def create_cloudfront_distribution(self,domain_name: str, s3_bucket_name: str,
                                   viewer_protocol_policy: str = "redirect-to-https",
                                   min_ttl: int = 3600, max_ttl: int = 86400,
                                   default_ttl: int = 86400) -> str:


    

        distribution_config = {
            'DistributionConfig': {
                'Aliases': {
                    'Quantity': 1,
                    'Items': [
                        domain_name
                    ]
                },
                'DefaultCacheBehavior': {
                    'TargetOriginId': f'S3-{s3_bucket_name}',
                    'ViewerProtocolPolicy': viewer_protocol_policy,
                    'MinTTL': min_ttl,
                    'MaxTTL': max_ttl,
                    'DefaultTTL': default_ttl
                },
                'Origins': {
                    'Quantity': 1,
                    'Items': [
                        {
                            'Id': f'S3-{s3_bucket_name}',
                            'DomainName': f'{s3_bucket_name}.s3.amazonaws.com',
                            'OriginPath': '/'
                        }
                    ]
                },
                'ViewerCertificate': {
                    'CloudFrontDefaultCertificate': True
                }
            }
        }

        response = self.cloudfornt_client.create_distribution(DistributionConfig=distribution_config)
        tool_name='cloudfromation'
        task='Creates a CloudFront distribution with the specified configuration.'
        self.store_result(tool_name,task,response)


    def store_result(self, tool_name, task, message):
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}")
        self.state.store('cloudfront_agent', task, message)

    def handle_task(self, tool_task):
        # Create a prompt for the LLM to choose a CloudFront tool
        messages = [
            {"role": "user", "content": tool_task}
        ]

        model_id = "ft:gpt-4o-2024-08-06:personal:subagent-v2:ANzlFPtn"

        # Call the OpenAI API to get a response for the tool and inputs
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            max_tokens=100,
            temperature=0,
            stop=None
        )

        # Parse the JSON response to determine the tool and inputs
        decision_result = response.choices[0].message.content.strip()
        json_parser = JsonOutputParser()

        try:
            parsed_response = json_parser.parse(decision_result)
            tool_name = parsed_response['tool']
            inputs = parsed_response['inputs']
            
            # Store the decision status
            self.state.store('cloudfront_agent', tool_name, "require inputs from user")
            
            # Check system status and update inputs if needed
            system_status = self.state.extract_results()
            inputs = self.check_inputs( inputs, tool_name, system_status)
            
            # Return if inputs are incomplete or missing
            if inputs is None:
                return

            # Execute the CloudFront task based on the tool name
            if tool_name == "create_cloudfront_distribution":
                domain_name = inputs.get("domain_name")
                s3_bucket_name = inputs.get("s3_bucket_name")
                viewer_protocol_policy = inputs.get("viewer_protocol_policy", "redirect-to-https")
                min_ttl = inputs.get("min_ttl", 3600)
                max_ttl = inputs.get("max_ttl", 86400)
                default_ttl = inputs.get("default_ttl", 86400)
                
                # Call the distribution creation method with provided inputs
                self.create_cloudfront_distribution(
                    domain_name=domain_name,
                    s3_bucket_name=s3_bucket_name,
                    viewer_protocol_policy=viewer_protocol_policy,
                    min_ttl=min_ttl,
                    max_ttl=max_ttl,
                    default_ttl=default_ttl
                )

            else:
                print(f"Unknown tool name: {tool_name}.")
                self.store_result('cloudfront_agent', tool_name, 'unknown tool name')

        except Exception as e:
            error_message = f"Error parsing JSON response: {e}"
            task = 'handle_task'
            self.store_result('cloudfront_agent', task, error_message)

    def check_inputs(self, inputs, tool_name, system_status):
        from app import get_user_inputs
        
        print('Inputs:', inputs)
        print('Tool:', tool_name)
        
        required_inputs = {}
        auto_selected_inputs = {}
        flag = 0
        
        # Process inputs to separate required, recent, and default values
        for key, value in inputs.items():
            print("Key:", key)
            print("Value:", value)
            
            if value in ('required', 'recent'):  # Mark required/recent inputs
                required_inputs[key] = value
                flag = 1  # Indicate that user input may be required
            elif value == 'default':  # Automatically set default values
                if key == 'Image_Id':
                    auto_selected_inputs[key] = 'ami-00f251754ac5da7f0'
                elif key == 'instance_type':
                    auto_selected_inputs[key] = 't2.micro'
                else:
                    auto_selected_inputs[key] = value
            else:
                print(f"{key}: {value}")  # Other cases are logged

        # If no required inputs are found, return the inputs as-is
        if flag == 0:
            return {**inputs, **auto_selected_inputs}
        
        # Call reuse_inputs to retrieve inputs based on system state
        user_inputs, flag = reuse_inputs(system_status, tool_name, inputs)
        print('userinputs_v1',user_inputs)
        print('flag',flag)
        if isinstance(user_inputs, str):
            
            try:
                user_inputs = json.loads(user_inputs)
            except json.JSONDecodeError:
                print("Error decoding JSON from user inputs.")
                user_inputs = {}
        required_inputs.update({k: 'required' for k, v in user_inputs.get('inputs', {}).items() if v == 'required'})
        print('required_inputs_v1',required_inputs)
        print('flag_v2',flag)
        # If required inputs are still missing, get user inputs
        if flag is True:
            print('flag was true hences inside')
            user_inputs = get_user_inputs(required_inputs, auto_selected_inputs)
            print('user inputs after taking inputs',user_inputs)
            for input_name, _ in required_inputs.items():
                inputs[input_name] = user_inputs[input_name]
        print('inputs before returning',inputs)
        return {**inputs, **auto_selected_inputs}    
# Example usage
