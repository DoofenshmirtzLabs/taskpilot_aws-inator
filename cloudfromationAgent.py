import openai
from agents.state_manager import State
from botocore.exceptions import ClientError
import streamlit as st
from agents.reuseinputsAgent import reuse_inputs
import json
from langchain_core.output_parsers import JsonOutputParser
state_v1=State()
class CloudFromation:
    def __init__(self, api_key, cloudfromation_client):
        self.cloudformation_client = cloudfromation_client
        self.client = openai.Client(api_key=api_key)
        self.state = State()
        print("CloudFront agent initialized")

    def create_stack(self, stack_name, template_body):
        task = "create_cloudfront_stack"
        try:
            response = self.cloudformation_client.create_stack(
                StackName=stack_name,
                TemplateBody=template_body
            )
            result_message = f"CloudFront stack '{stack_name}' created successfully."
            self.store_result("cloudfront_agent", task, result_message)
            self.eot_agent.handle_task()
        except ClientError as e:
            error_message = f"Error creating CloudFront stack: {e}"
            self.store_result("cloudfront_agent", task, error_message)
            return None
    def delete_stack(self, stack_name):
        task = "delete_stack"
        try:
            response = self.cloudformation_client.delete_stack(
                StackName=stack_name
            )
            result_message = f"CloudFormation stack '{stack_name}' deleted successfully."
            self.store_result("cloudformation_agent", task, result_message)

        except ClientError as e:
            error_message = f"Error deleting CloudFormation stack '{stack_name}': {e}"
            self.store_result("cloudformation_agent", task, error_message)
            return None

    def store_result(self, tool_name, task, message):
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}")
        self.state.store('cloudfront_agent', task, message)

    def handle_task(self, tool_task):
        # Create a prompt for the LLM to choose a CloudFormation tool
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
            self.state.store('cloudformation_agent', tool_name, "require inputs from user")
            
            # Check system status and update inputs if needed
            system_status = self.state.extract_results()
            inputs = self.check_inputs( inputs, tool_name, system_status)
            
            # Return if inputs are incomplete or missing
            if inputs is None:
                return

            # Execute the CloudFormation task based on the tool name
            if tool_name == "create_stack":
                stack_name = inputs.get("stack_name")
                template_body = inputs.get("template_body")
                
                # Call the stack creation method with provided inputs
                self.create_stack(
                    stack_name=stack_name,
                    template_body=template_body
                )

            elif tool_name == "delete_stack":
                stack_name = inputs.get("stack_name")
                
                # Call the stack deletion method with provided inputs
                self.delete_stack(stack_name)

            else:
                print(f"Unknown tool name: {tool_name}.")
                self.store_result('cloudformation_agent', tool_name, 'unknown tool name')

        except Exception as e:
            error_message = f"Error parsing JSON response: {e}"
            task = 'handle_task'
            self.store_result('cloudformation_agent', task, error_message)

        # Similar to EC2 and RDS agents' handle_task logic
        # Using OpenAI to decide the next step and parse inputs
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
        
# Example usage
