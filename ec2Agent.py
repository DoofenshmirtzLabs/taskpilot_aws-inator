import boto3
import openai
from agents.state_manager import State
import json
from botocore.exceptions import ClientError
from langchain_core.output_parsers import JsonOutputParser
from agents.reuseinputsAgent import reuse_inputs
import streamlit as st

state_v1=State()
class EC2Agent:
    def __init__(self, api_key, ec2_client):
        self.ec2_client = ec2_client
 
        self.client = openai.Client(api_key=api_key)  # Initialize OpenAI client
        self.state = State()
        print("EC2 agent initialized")
    def create_vpc(self,CidrBlock=None):
        vpc_response = self.ec2_client.create_vpc(CidrBlock='10.0.0.0/16')
        vpc_id = vpc_response['Vpc']['VpcId']
        tool_name='create_vpc'
        task='create an vpc'
        result ='create an vpc with vpc_id:{vpc_id}'
        self.store_result(tool_name,task,result)
    
    def create_subnets(self, numSubnets, vpc_id):
        subnets = []  # List to store created subnet IDs
        result=""
        try:
            for i in range(numSubnets):
                # Dynamically adjust the CidrBlock for each subnet
                cidr_block = f"10.0.{i}.0/24"
                
                # Create the subnet
                subnet_response = self.ec2_client.create_subnet(CidrBlock=cidr_block, VpcId=vpc_id)
                subnet_id = subnet_response['Subnet']['SubnetId']
                
                subnets.append(subnet_id)  # Store the created subnet ID
                
                temp="Created subnet {subnet_id} with CidrBlock {cidr_block}"
                result=result+temp+'\n'
            tool_name='create_subnets'
            task='creating {numSubnets} number of subnets with vpc_id:{vpc_id}'
            self.store_result(tool_name,task,result)
        except ClientError as e:
            error_message = f"Error creating key pair: {e}"
            self.store_result("ec2_agent", task, error_message)
            return None
    def create_key_pair(self, key_name):
        task = "create_key_pair"
        try:
            response = self.ec2_client.create_key_pair(KeyName=key_name)
            key_material = response['KeyMaterial']
            result_message = f"Key pair '{key_name}' created successfully."
            self.store_result("ec2_agent", task, result_message)

        except ClientError as e:
            error_message = f"Error creating key pair: {e}"
            self.store_result("ec2_agent", task, error_message)
            return None
          # You can save the key to a file for later use
    def associate_address(self, instance_id, allocation_id):
        task = "associate_address"
        try:
            response = self.ec2_client.associate_address(
                InstanceId=instance_id,
                AllocationId=allocation_id
            )
            result_message = f"Elastic IP associated with instance {instance_id}."
            self.store_result("ec2_agent", task, result_message)
            self.handle_task()
            return response
        except ClientError as e:
            error_message = f"Error associating address: {e}"
            self.store_result("ec2_agent", task, error_message)
            return None

    def create_security_group(self,vpc_id):
        security_group_response = self.ec2_client.create_security_group(
        GroupName='my-security-group',
        Description='My security group',
        VpcId=vpc_id
    )
        security_group_id = security_group_response['GroupId']
        tool_name="create_security_group"
        task="creating an security_group with vpc_id:{vpc_id}"
        result=f'''created an security_group with id:{security_group_id}'''
        self.store_result(tool_name,task,result)
    
    def create_internet_gateway(self):
        task = "create_internet_gateway"
        try:
            response = self.ec2_client.create_internet_gateway()
            igw_id = response['InternetGateway']['InternetGatewayId']
            result_message = f"Internet Gateway created with ID: {igw_id}"
            self.store_result("ec2_agent", task, result_message)
            
            return igw_id
        except ClientError as e:
            error_message = f"Error creating Internet Gateway: {e}"
            self.store_result("ec2_agent", task, error_message)
            return None
    def attach_internet_gateway(self, vpc_id, igw_id):
        task = "attach_internet_gateway"
        try:
            self.ec2_client.attach_internet_gateway(
                InternetGatewayId=igw_id,
                VpcId=vpc_id
            )
            result_message = f"Internet Gateway '{igw_id}' attached to VPC '{vpc_id}' successfully."
            self.store_result("ec2_agent", task, result_message)
            
        except ClientError as e:
            error_message = f"Error attaching Internet Gateway to VPC: {e}"
            self.store_result("ec2_agent", task, error_message)

    def create_route_table(self, vpc_id):
        task = "create_route_table"
        try:
            response = self.ec2_client.create_route_table(VpcId=vpc_id)
            route_table_id = response['RouteTable']['RouteTableId']
            result_message = f"Route Table created with ID: {route_table_id} for VPC '{vpc_id}'."
            self.store_result("ec2_agent", task, result_message)
            
            return route_table_id
        except ClientError as e:
            error_message = f"Error creating Route Table for VPC '{vpc_id}': {e}"
            self.store_result("ec2_agent", task, error_message)
            return None
    def associate_route_table(self, subnet_id, route_table_id):
        task = "associate_route_table"
        try:
            response = self.ec2_client.associate_route_table(
                SubnetId=subnet_id,
                RouteTableId=route_table_id
            )
            association_id = response['AssociationId']
            result_message = f"Route Table '{route_table_id}' associated with Subnet '{subnet_id}' successfully."
            self.store_result("ec2_agent", task, result_message)
            
            return association_id
        except ClientError as e:
            error_message = f"Error associating Route Table '{route_table_id}' with Subnet '{subnet_id}': {e}"
            self.store_result("ec2_agent", task, error_message)
            return None

    def create_instance(self, image_id, instance_type,**kwargs):
        try:
            params = {
        'ImageId': image_id,
        'InstanceType': instance_type,
        'MinCount': 1,
        'MaxCount': 1,
        'TagSpecifications': [
            {
                'ResourceType': 'instance',
                'Tags': [{'Key': 'Name', 'Value': 'my_web_server'}]
            }
        ]
    }
            task="create_instance"
            if(kwargs=='security_group_id'):
                params['security_group_id']=kwargs['security_group_id']
            if(kwargs=='subnet_id'):
                params['subnet_id']=kwargs['subnet_id']
            if(kwargs=='key_name'):
                params['key_name']=kwargs['key_name']
            response = self.ec2_client.run_instances(**params)
            instance_id = response['Instances'][0]['InstanceId']
            result_message = f"EC2 Instance '{instance_id}' created successfully."
            self.store_result("ec2_agent", task,result_message)
            
            
        except ClientError as e:
            error_message = f"Error creating EC2 instance: {e}"
            self.store_result("ec2_agent", task,error_message)
            return None

    def terminate_instance(self, instance_id):
        try:
            task="terminate_instance"
            response = self.ec2_client.terminate_instances(InstanceIds=[instance_id])
            result_message = f"EC2 Instance '{instance_id}' terminated successfully."
            self.store_result("ec2_agent", task,result_message)
            
        except ClientError as e:
            error_message = f"Error terminating EC2 instance: {e}"
            self.store_result("ec2_agent", task,error_message)
            return None

    def describe_instances(self):
        try:
            task='describe_instance'
            response = self.ec2_client.describe_instances()
            instances_info = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_id = instance['InstanceId']
                    instance_type = instance['InstanceType']
                    instances_info.append(f"  - InstanceId: {instance_id}, InstanceType: {instance_type}")
            result_message = "Current EC2 Instances:\n" + "\n".join(instances_info)
            self.store_result("ec2_agent", task,result_message)
          
        except ClientError as e:
            error_message = f"Error describing EC2 instances: {e}"
            self.store_result("ec2_agent", task,error_message)
            return None

    def store_result(self, tool_name, task,message):
        # Store the result in both session state and self.state
        if 'task_history' not in st.session_state:
            st.session_state.task_history = []
        st.session_state.task_history.append(f"{tool_name}: {message}")
        self.state.store('ec2_agent',task, message)

    def handle_task(self,tool_task):
        # Get the state from the state manager

        


        # Create a prompt for the LLM to choose a tool
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
        print('decision_result_ec2',decision_result)
        json_parser = JsonOutputParser()
        try:
            parsed_response = json_parser.parse(decision_result)
            
            print('parsed_response:',parsed_response)
            # Store decision agent result in state
            tool_name = parsed_response['tool']
            inputs=parsed_response['inputs']
            print('parsed response ec2 agent',parsed_response)
            message="require inputs from user"
            self.state.store('ec2_agent',tool_name, message)
            system_status=state_v1.extract_results()
            print('system status in ec2',system_status)
            inputs = check_inputs(self, inputs, tool_name, system_status)
            print('inputs from check_inputs',inputs)
            if inputs==None:
                return 
                        

            # Handle the selected tool and its inputs
            if tool_name == "create_instance":
                image_id = inputs.get("ami_id") or inputs.get("image_id")  #CreateInstance\", \"inputs\": {\"Image_Id\": \"default\", \"instance_type\": \"default\"}}"}]}
                instance_type = inputs.get("instance_type")
                print('imageid',image_id,instance_type)
                self.create_instance(image_id, instance_type)


            elif tool_name == "terminate_instance":#terminate_instance\", \"inputs\": {\"instance_id\": \"required\"}}"}]}
                instance_id = inputs.get("instance_id")
               
                self.terminate_instance(instance_id)


            elif tool_name == "describe_instance":#"role": "assistant", "content": "{\"tool\": \"describe_instance\", \"inputs\": {}}"}]}
                self.describe_instances()
            elif tool_name=="create_vpc":
                self.create_vpc

            elif tool_name == "create_subnetes":
                self.create_subnets(inputs['numSubnets'], inputs['vpc_id'])

            elif tool_name == "create_security_group":
                self.create_security_group(inputs['vpc_id'])

            elif tool_name == "create_route_table":
                self.create_route_table(inputs['vpc_id'])

            elif tool_name == "create_key_pair":
                self.create_key_pair(inputs['key_name'])

            elif tool_name == "create_internet_gateway":
                self.create_internet_gateway()


            else:
                print(f"Unknown tool name: {tool_name}.")
                self.store_result('ec2_agent',tool_name,'unknown tool name')

        except Exception as e:
            result=f"Error parsing JSON response: {e}"
            task='handle_task'
            self.store_result('ec2_agent',task,result)
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
