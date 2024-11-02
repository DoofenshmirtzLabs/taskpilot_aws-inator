import boto3
import openai
from agents.state_manager import State
import json
from botocore.exceptions import ClientError
from langchain_core.output_parsers import JsonOutputParser
from agents.reuseinputsAgent import reuse_inputs
import streamlit as st
state_v1=State()
class S3Agent:
    def __init__(self, api_key, s3_client):
        self.s3_client = s3_client
        self.client = openai.Client(api_key=api_key)  # Initialize OpenAI client
        self.state = State()
 
        print("S3 agent initialized")

    def create_bucket(self, bucket_name):
        try:
            task="create_bucket"
            print('called create bucket')
            response = self.s3_client.create_bucket(Bucket=bucket_name)
            message = f"Bucket '{bucket_name}' created successfully."
            self.store_result('s3_agent',task, message)
            self.eot_agent.handle_task()
            print('called eot agent in s3')
        except ClientError as e:
            message = f"Error creating bucket: {e}"
            self.store_result('s3_agent',task, message)
            return None

    def upload_file(self, bucket_name, file_path):
        try:
            task='upload_file'
            file_name = file_path.split('/')[-1]
            self.s3_client.upload_file(file_path, bucket_name, file_name)
            
            message = f"File '{file_name}' uploaded to bucket '{bucket_name}' successfully."
            self.store_result('s3_agent', task,message)
            self.eot_agent.handle_task()
        except ClientError as e:
            message = f"Error uploading file: {e}"
            self.store_result('s3_agent', message)

    def delete_object(self, bucket_name, object_key):
        try:
            task='delete_object'
            response = self.s3_client.delete_object(Bucket=bucket_name, Key=object_key)
            message = f"Object '{object_key}' deleted from bucket '{bucket_name}' successfully."
            
            self.store_result('s3_agent',task, message)
            
        except ClientError as e:
            message = f"Error deleting object: {e}"
            self.store_result('s3_agent',task, message)
            return None

    def list_buckets(self):
        try:
            task='list_buckets'
            response = self.s3_client.list_buckets()
            message = "Existing buckets:"
            bucket_list = []
            for bucket in response['Buckets']:
                bucket_list.append(bucket['Name'])
            
            message += '\n' + '\n'.join([f"  - {name}" for name in bucket_list])
            self.store_result('s3_agent', task,message)
            
        except ClientError as e:
            message = f"Error listing buckets: {e}"
            self.store_result('s3_agent', message)
            return None

    def store_result(self, agent_name,task, message):
        # Store the result in both session state and self.state
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{agent_name}: {message}")
        self.state.store('s3_agent', task,message)

    def handle_task(self,tool_task):
        # Get the state from the state manager
        messages = [
            {"role": "user", "content": tool_task}
    ]
        model_id = "ft:gpt-4o-2024-08-06:personal:subagent-v2:ANzlFPtn"

        # User input for testing
   

        # Call the OpenAI API
        response = self.client.chat.completions.create(
            model=model_id,  # Use your fine-tuned model's ID here
            messages=messages, # Send the user input
            max_tokens=100,  # Adjust the token limit according to your needs
            temperature=0,  # Adjust for more or less creativity
            stop=None  # You can set stop sequences if needed
        )
        


        # Extract the JSON response
        decision_result = response.choices[0].message.content.strip()
        print('\n decision result',decision_result)
        json_parser = JsonOutputParser()
        try:
            parsed_response = json_parser.parse(decision_result)
            print("\nParsed Response:", parsed_response)

            tool_name = parsed_response.get("tool", None)  # Safely get tool_name
            
            system_status=state_v1.extract_results()
            print('system status in ec2',system_status)
            inputs =self.check_inputs(inputs, tool_name, system_status)
            print('inputs from check_inputs',inputs)
            if inputs==None:
                return 
            
            print("Selected Tool Name:", tool_name)
            if tool_name =='create_bucket':
                bucket_name = inputs.get("bucket_name")
                if bucket_name != "ask user for it":
                    print('calling create_bucket')
                    self.create_bucket(bucket_name)
                else:
                    message = "BucketName is required for CreateBucket."
                    self.store_result('s3_agent', message)

            elif tool_name == "UploadFile":
                bucket_name = inputs.get("bucket_name")
                file_path = inputs.get("file_path")
                if bucket_name != "ask user for it" and file_path != "ask user for it":
                    self.upload_file(bucket_name, file_path)
                else:
                    message = "Both BucketName and FilePath are required for UploadFile."
                    self.store_result('s3_agent', message)

            elif tool_name == "delete_object":###i need to remove delete_object and listbuckets and replace it with delete bucket funciton
                bucket_name = inputs.get("bucket_name")
                object_key = inputs.get("ObjectKey")
                if bucket_name != "ask user for it" and object_key != "ask user for it":
                    self.delete_object(bucket_name, object_key)
                else:
                    message = "Both BucketName and ObjectKey are required for DeleteObject."
                    self.store_result('s3_agent', message)

            elif tool_name == "ListBuckets":
                self.list_buckets()

            else:
                message = f"Unknown tool name: {tool_name}."
                self.store_result('s3_agent', message)

                # Extract the selected tool and inputs
                tool_name = parsed_response["tool_name"]
                inputs = parsed_response["inputs"]
                print("Selected Tool Name:", tool_name)
                # Process the selected tool further as needed
        except Exception as e:
            message = f"Error parsing JSON response: {e}"
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
    

#****todo: to make sure all the agents can communicate with frontend using streamlit session state
