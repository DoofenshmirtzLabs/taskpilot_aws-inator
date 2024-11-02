import boto3
import openai
from agents.state_manager import State
from botocore.exceptions import ClientError
from langchain_core.output_parsers import JsonOutputParser
from agents.reuseinputsAgent import reuse_inputs
import json
import streamlit as st

class LambdaAgent:
    def __init__(self, api_key, lambda_client):
        self.lambda_client = lambda_client
        self.client = openai.Client(api_key=api_key)
        self.state = State()
        print("Lambda agent initialized")

    def create_function(self, function_name, runtime, role, handler, zip_file_path):
        task = "create_lambda_function"
        try:
            with open(zip_file_path, 'rb') as zip_file:
                zip_bytes = zip_file.read()
                
            response = self.lambda_client.create_function(
                FunctionName=function_name,
                Runtime=runtime,
                Role=role,
                Handler=handler,
                Code={'ZipFile': zip_bytes},
                Publish=True
            )
            result_message = f"Lambda function '{function_name}' created successfully."
            self.store_result("lambda_agent", task, result_message)
            
        except ClientError as e:
            error_message = f"Error creating Lambda function: {e}"
            self.store_result("lambda_agent", task, error_message)
            return None
    def update_function_code(self, function_name, zip_file_path):
        task = "update_function_code"
        try:
            with open(zip_file_path, 'rb') as zip_file:
                response = self.lambda_client.update_function_code(
                    FunctionName=function_name,
                    ZipFile=zip_file.read()
                )
            result_message = f"Lambda function '{function_name}' code updated successfully."
            self.store_result("lambda_agent", task, result_message)
            
            return response
        except ClientError as e:
            error_message = f"Error updating Lambda function '{function_name}' code: {e}"
            self.store_result("lambda_agent", task, error_message)
            return None
    def invoke_function(self, function_name, payload):
        task = "invoke_function"
        try:
            response = self.lambda_client.invoke(
                FunctionName=function_name,
                Payload=payload
            )
            result_message = f"Lambda function '{function_name}' invoked successfully."
            self.store_result("lambda_agent", task, result_message)
            
            return response
        except ClientError as e:
            error_message = f"Error invoking Lambda function '{function_name}': {e}"
            self.store_result("lambda_agent", task, error_message)
            return None


    def store_result(self, tool_name, task, message):
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}")
        self.state.store('lambda_agent', task, message)

    def handle_task(self,tool_task):
        # Get the state from the state manager
        messages = [
            {"role": "user", "content": tool_task}
    ]
        model_id = "ft:gpt-4o-2024-08-06:personal:aws-tool-selector-v2:AHXaD6pl"

        # Similar to EC2 and RDS agents' handle_task logic
        # Using OpenAI to decide the next step and parse inputs

# Example usage
    def check_inputs( inputs, tool_name, system_status):
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
    
