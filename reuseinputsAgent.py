import openai
from agents.state_manager import State
import json


openai_apikey = ''
client = openai.Client(api_key=openai_apikey)
assistant_id="asst_SVuYIrSOq0tEyLmV65lxnNyB"

thread = client.beta.threads.create()


def reuse_inputs(system_state, tool, function_requirements):
    print('system_state_reuse',system_state,tool,function_requirements)
    prompt = f"""
    System State: {system_state}
    
    Required Inputs for Tool:
    {tool}
    
    The following JSON object represents required inputs for the `create_instance` tool of the EC2 service:
    {function_requirements}
    """
    print('prompt', prompt)

    try:
        # Send the initial prompt
        client.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=prompt
        )
        
        # Run and poll for the assistant's response
        run = client.beta.threads.runs.create_and_poll(
            thread_id=thread.id,
            assistant_id=assistant_id,
            instructions=(
                "You are a helpful assistant responsible for analyzing the current AWS infrastructure state "
                "and determining the necessary inputs for deploying resources. You should check the system state "
                "for existing values related to VPC ID, subnet ID, and security group ID, etc. If values are present, "
                "replace the 'required' placeholders in the function requirements with those values. "
                "Always return a valid JSON object reflecting the inputs needed for the specified AWS service and tool, "
                "without any additional text."
            )
        )

        # Check if the run completed and retrieve messages
        if run.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )
            
            # Extract the assistant's response text content
            assistant_message = messages.data[0]  # First message from the assistant
            text_content = assistant_message.content[0].text.value  # Extract text from content block

            # Clean and parse JSON response
            json_str = text_content.strip("```json\n").strip("```")
            parsed_data = json.loads(json_str)
            print('parsed_data_infunction', parsed_data)
            parsed_data.get('inputs',{})
            
            # Check if any required placeholders remain
            flag = any(value == 'required' for value in parsed_data.values())
            
            return parsed_data, flag
        else:
            print('Run status:', run.status)
            return None, True  # Return None and flag indicating incomplete run

    except Exception as e:
        result = f"Error parsing JSON response: {e}"
        task = 'handle_task'
        State.store('reuseagent', task, result)
        return None, True
