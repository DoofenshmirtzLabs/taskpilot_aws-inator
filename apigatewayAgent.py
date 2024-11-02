import boto3
import openai
from agents.state_manager import State
from botocore.exceptions import ClientError
from langchain_core.output_parsers import JsonOutputParser
from agents.reuseinputsAgent import reuse_inputs
import json
import streamlit as st
state_v1=State()
class APIGatewayAgent:
    def __init__(self, api_key, apigateway_client):
        self.apigateway_client = apigateway_client
        self.client = openai.Client(api_key=api_key)
        self.state = State()
        print("API Gateway agent initialized")

    def create_rest_api(self, api_name):
        task = "create_rest_api"
        try:
            response = self.apigateway_client.create_rest_api(
                name=api_name
            )
            result_message = f"API Gateway REST API '{api_name}' created successfully."
            self.store_result("api_gateway_agent", task, result_message)
            self.eot_agent.handle_task()
        except ClientError as e:
            error_message = f"Error creating REST API: {e}"
            self.store_result("api_gateway_agent", task, error_message)
            return None
    def create_resource(self, rest_api_id, parent_resource_id, path_part):
            task = "create_resource"
            try:
                response = self.apigateway_client.create_resource(
                    restApiId=rest_api_id,
                    parentId=parent_resource_id,
                    pathPart=path_part
                )
                result_message = f"Resource '{path_part}' created in API '{rest_api_id}'."
                self.store_result("api_gateway_agent", task, result_message)
                self.handle_task()
                return response
            except ClientError as e:
                error_message = f"Error creating resource: {e}"
                self.store_result("api_gateway_agent", task, error_message)
                return None
    def put_method(self, rest_api_id, resource_id, http_method, authorization_type='NONE'):
        task = "put_method"
        try:
            response = self.apigateway_client.put_method(
                restApiId=rest_api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType=authorization_type
            )
            result_message = f"Method '{http_method}' added to resource '{resource_id}' in API '{rest_api_id}'."
            self.store_result("api_gateway_agent", task, result_message)

        except ClientError as e:
            error_message = f"Error adding method: {e}"
            self.store_result("api_gateway_agent", task, error_message)
            return None
    def create_deployment(self, rest_api_id, stage_name):
        task = "create_deployment"
        try:
            response = self.api_gateway.create_deployment(
                restApiId=rest_api_id,
                stageName=stage_name
            )
            result_message = f"rest_api_id:'{rest_api_id}' deployed to stage '{stage_name}'."
            self.store_result("api_gateway_agent", task, result_message)

        except ClientError as e:
            error_message = f"Error deploying API: {e}"
            self.store_result("api_gateway_agent", task, error_message)
            return None


    def store_result(self, tool_name, task, message):
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}")
        self.state.store('api_gateway_agent', task, message)

    def handle_task(self, tool_task):
        # Create a prompt for the LLM to choose an API Gateway tool
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
            self.state.store('api_gateway_agent', tool_name, "require inputs from user")
            
            # Check system status and update inputs if needed
            system_status = self.state.extract_results()
            inputs = self.check_inputs( inputs, tool_name, system_status)
            
            # Return if inputs are incomplete or missing
            if inputs is None:
                return

            # Execute the API Gateway task based on the tool name
            if tool_name == "create_rest_api":
                api_name = inputs.get("api_name")
                self.create_rest_api(api_name)

            elif tool_name == "create_resource":
                rest_api_id = inputs.get("rest_api_id")
                parent_resource_id = inputs.get("parent_resource_id")
                path_part = inputs.get("path_part")
                self.create_resource(rest_api_id, parent_resource_id, path_part)

            elif tool_name == "put_method":
                rest_api_id = inputs.get("rest_api_id")
                resource_id = inputs.get("resource_id")
                http_method = inputs.get("http_method")
                authorization_type = inputs.get("authorization_type", "NONE")
                self.put_method(rest_api_id, resource_id, http_method, authorization_type)

            elif tool_name == "create_deployment":
                rest_api_id = inputs.get("rest_api_id")
                stage_name = inputs.get("stage_name")
                self.create_deployment(rest_api_id, stage_name)

            else:
                print(f"Unknown tool name: {tool_name}.")
                self.store_result('api_gateway_agent', tool_name, 'unknown tool name')

        except Exception as e:
            error_message = f"Error parsing JSON response: {e}"
            task = 'handle_task'
            self.store_result('api_gateway_agent', task, error_message)
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