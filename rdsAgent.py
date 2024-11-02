import boto3
import openai
from agents.state_manager import State
import json
from botocore.exceptions import ClientError
from langchain_core.output_parsers import JsonOutputParser
from agents.reuseinputsAgent import reuse_inputs
import streamlit as st

state_v1=State()
class RDSAgent:
    def __init__(self, api_key, rds_client):
        self.rds_client = rds_client
       
        self.client = openai.Client(api_key=api_key)  # Initialize OpenAI client
        self.state = State()
        print("RDS agent initialized")

    def create_rds_instance(self, db_instance_identifier, db_instance_class, engine, master_username, master_password):
        task = "create_rds_instance"
        try:
            response = self.rds_client.create_db_instance(
                DBInstanceIdentifier=db_instance_identifier,
                DBInstanceClass=db_instance_class,
                Engine=engine,
                MasterUsername=master_username,
                MasterUserPassword=master_password,
                AllocatedStorage=20  # Default storage for this example
            )
            result_message = f"RDS Instance '{db_instance_identifier}' created successfully."
            self.store_result("rds_agent", task, result_message)
            
        except ClientError as e:
            error_message = f"Error creating RDS instance: {e}"
            self.store_result("rds_agent", task, error_message)
            return None
    def delete_rds_instance(self, db_instance_identifier, skip_final_snapshot=True):
            task = "delete_rds_instance"
            try:
                response = self.rds.delete_db_instance(
                    DBInstanceIdentifier=db_instance_identifier,
                    SkipFinalSnapshot=skip_final_snapshot
                )
                result_message = f"RDS instance '{db_instance_identifier}' deleted successfully."
                self.store_result("rds_agent", task, result_message)
                self.handle_task()
                return response
            except ClientError as e:
                error_message = f"Error deleting RDS instance: {e}"
                self.store_result("rds_agent", task, error_message)
                return None
    def create_db_snapshot(self, db_instance_identifier, snapshot_name):
        task = "create_db_snapshot"
        try:
            response = self.rds_client.create_db_snapshot(
                DBSnapshotIdentifier=snapshot_name,
                DBInstanceIdentifier=db_instance_identifier
            )
            result_message = f"RDS snapshot '{snapshot_name}' for instance '{db_instance_identifier}' created successfully."
            self.store_result("rds_agent", task, result_message)
            
            return response
        except ClientError as e:
            error_message = f"Error creating RDS snapshot: {e}"
            self.store_result("rds_agent", task, error_message)
            return None
    def restore_db_instance_from_snapshot(self, snapshot_name):
        task = "restore_db_instance_from_snapshot"
        try:
            response = self.rds_client.restore_db_instance_from_db_snapshot(
                DBSnapshotIdentifier=snapshot_name,
                DBInstanceIdentifier=f"restored-{snapshot_name}"
            )
            result_message = f"RDS instance restored from snapshot '{snapshot_name}'."
            self.store_result("rds_agent", task, result_message)
            
            return response
        except ClientError as e:
            error_message = f"Error restoring RDS from snapshot: {e}"
            self.store_result("rds_agent", task, error_message)
            return None


    def list_rds_instances(self):
        task = "list_rds_instances"
        try:
            response = self.rds_client.describe_db_instances()
            instances_info = []
            for db_instance in response['DBInstances']:
                db_instance_id = db_instance['DBInstanceIdentifier']
                db_instance_class = db_instance['DBInstanceClass']
                instances_info.append(f"  - DBInstanceIdentifier: {db_instance_id}, DBInstanceClass: {db_instance_class}")
            result_message = "Current RDS Instances:\n" + "\n".join(instances_info)
            self.store_result("rds_agent", task, result_message)
            
        except ClientError as e:
            error_message = f"Error listing RDS instances: {e}"
            self.store_result("rds_agent", task, error_message)
            return None

    def modify_rds_instance(self, db_instance_identifier, db_instance_class):
        task = "modify_rds_instance"
        try:
            response = self.rds_client.modify_db_instance(
                DBInstanceIdentifier=db_instance_identifier,
                DBInstanceClass=db_instance_class,
                ApplyImmediately=True  # Modify immediately
            )
            result_message = f"RDS Instance '{db_instance_identifier}' modified to class '{db_instance_class}' successfully."
            self.store_result("rds_agent", task, result_message)
            
        except ClientError as e:
            error_message = f"Error modifying RDS instance: {e}"
            self.store_result("rds_agent", task, error_message)
            return None

    def store_result(self, tool_name, task, message):
        # Store the result in both session state and self.state
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}")
        self.state.store('rds_agent', task, message)

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
            self.state.store('rds_agent', tool_name, "require inputs from user")
            system_status = state_v1.extract_results()
            inputs = check_inputs(self, inputs, tool_name, system_status)
            
            if inputs is None:
                return

            # Handle the selected tool and its inputs for RDS
            if tool_name == "create_rds_instance":
                db_instance_identifier = inputs.get("db_instance_identifier")
                db_instance_class = inputs.get("db_instance_class")
                engine = inputs.get("engine")
                master_username = inputs.get("master_username")
                master_password = inputs.get("master_password")
                self.create_rds_instance(db_instance_identifier, db_instance_class, engine, master_username, master_password)

            elif tool_name == "delete_rds_instance":
                db_instance_identifier = inputs.get("db_instance_identifier")
                skip_final_snapshot = inputs.get("skip_final_snapshot", True)
                self.delete_rds_instance(db_instance_identifier, skip_final_snapshot)

            elif tool_name == "create_db_snapshot":
                db_instance_identifier = inputs.get("db_instance_identifier")
                snapshot_name = inputs.get("snapshot_name")
                self.create_db_snapshot(db_instance_identifier, snapshot_name)

            elif tool_name == "restore_db_instance_from_snapshot":
                snapshot_name = inputs.get("snapshot_name")
                self.restore_db_instance_from_snapshot(snapshot_name)

            elif tool_name == "list_rds_instances":
                self.list_rds_instances()

            elif tool_name == "modify_rds_instance":
                db_instance_identifier = inputs.get("db_instance_identifier")
                db_instance_class = inputs.get("db_instance_class")
                self.modify_rds_instance(db_instance_identifier, db_instance_class)

            else:
                print(f"Unknown tool name: {tool_name}.")
                self.store_result('rds_agent', tool_name, 'unknown tool name')

        except Exception as e:
            error_message = f"Error parsing JSON response: {e}"
            task = 'handle_task'
            self.store_result('rds_agent', task, error_message)


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
