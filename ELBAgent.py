import boto3
import openai
from agents.state_manager import State
from botocore.exceptions import ClientError
from langchain_core.output_parsers import JsonOutputParser
from agents.reuseinputsAgent import reuse_inputs
import json
import streamlit as st
state_v1=State()
class ELBAgent:
    def __init__(self, api_key, elb_client):
        self.elb_client = elb_client
        self.client = openai.Client(api_key=api_key)
        self.state = State()
        print("Elastic Load Balancer agent initialized")

    def create_load_balancer(self, name, subnets, security_groups):
        task = "create_load_balancer"
        try:
            response = self.elb_client.create_load_balancer(
                Name=name,
                Subnets=subnets,
                SecurityGroups=security_groups,
                Scheme='internet-facing'
            )
            result_message = f"Load Balancer '{name}' created successfully."
            self.store_result("elb_agent", task, result_message)
            self.eot_agent.handle_task()
        except ClientError as e:
            error_message = f"Error creating Load Balancer: {e}"
            self.store_result("elb_agent", task, error_message)
            return None
    def create_listener(self, load_balancer_arn, target_group_arn, protocol='HTTP', port=80):
        task = "create_listener"
        try:
            response = self.elb_client.create_listener(
                LoadBalancerArn=load_balancer_arn,
                Protocol=protocol,
                Port=port,
                DefaultActions=[{
                    'Type': 'forward',
                    'TargetGroupArn': target_group_arn
                }]
            )
            result_message = f"Listener created for Load Balancer '{load_balancer_arn}'."
            self.store_result("elb_agent", task, result_message)

        except ClientError as e:
            error_message = f"Error creating listener: {e}"
            self.store_result("elb_agent", task, error_message)
            return None
    def register_targets(self, target_group_arn, instance_ids):
        task = "register_targets"
        try:
            targets = [{'Id': instance_id} for instance_id in instance_ids]
            response = self.elb_client.register_targets(
                TargetGroupArn=target_group_arn,
                Targets=targets
            )
            result_message = f"Instances {instance_ids} registered to Target Group '{target_group_arn}'."
            self.store_result("elb_agent", task, result_message)

        except ClientError as e:
            error_message = f"Error registering targets: {e}"
            self.store_result("elb_agent", task, error_message)
            return None

    def store_result(self, tool_name, task, message):
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}")
        self.state.store('elb_agent', task, message)

    def handle_task(self, tool_task):
        # Create a prompt for the LLM to choose a tool
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
            self.state.store('elb_agent', tool_name, "require inputs from user")
            system_status = state_v1.extract_results()
            inputs = self.check_inputs( inputs, tool_name, system_status)
            
            if inputs is None:
                return

            # Handle the selected tool and its inputs for ELB
            if tool_name == "create_load_balancer":
                name = inputs.get("name")
                subnets = inputs.get("subnets")
                security_groups = inputs.get("security_groups")
                self.create_load_balancer(name, subnets, security_groups)

            elif tool_name == "create_listener":
                load_balancer_arn = inputs.get("load_balancer_arn")
                target_group_arn = inputs.get("target_group_arn")
                protocol = inputs.get("protocol", "HTTP")
                port = inputs.get("port", 80)
                self.create_listener(load_balancer_arn, target_group_arn, protocol, port)

            elif tool_name == "register_targets":
                target_group_arn = inputs.get("target_group_arn")
                instance_ids = inputs.get("instance_ids")
                self.register_targets(target_group_arn, instance_ids)

            else:
                print(f"Unknown tool name: {tool_name}.")
                self.store_result('elb_agent', tool_name, 'unknown tool name')

        except Exception as e:
            error_message = f"Error parsing JSON response: {e}"
            task = 'handle_task'
            self.store_result('elb_agent', task, error_message)

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
