import streamlit as st

# Simulated functions to fetch catalog options or selections
def fetch_ami_catalog():
    return {
        "Ubuntu 18.04 LTS": "ami-0abcdef1234567890", 
        "Amazon Linux 2": "ami-0fedcba9876543210"
    }

def fetch_instance_types():
    return ["t2.micro", "t2.small", "t2.medium"]

# Mapping of functions to fetch options for specific fields
OPTION_FETCHERS = {
    "ami_id": fetch_ami_catalog,
    "instance_type": fetch_instance_types,
}

def get_input_field(input_name: str, current_value: str = None) -> str:
    """
    Display input field based on whether options exist in OPTION_FETCHERS.
    Shows the current value pre-selected if available.
    
    Args:
    - input_name: Name of the input field.
    - current_value: Current value to pre-fill the field if available.
    
    Returns:
    - User's input value.
    """
    fetch_options = OPTION_FETCHERS.get(input_name, None)
    
    if fetch_options:
        options = fetch_options()
        if isinstance(options, dict):  # Handle catalog dictionaries
            option_list = list(options.keys())  # Get keys for display
            value_list = list(options.values())  # Get values to match current_value
            index = value_list.index(current_value) if current_value in value_list else 0
            selected_option = st.selectbox(f"Select {input_name}", options=option_list, index=index)
            return options[selected_option]
        elif isinstance(options, list):  # Handle simple list options
            index = options.index(current_value) if current_value in options else 0
            return st.selectbox(f"Select {input_name}", options=options, index=index)
    else:
        return st.text_input(f"Please provide a value for {input_name}:", value=current_value if current_value else "")

def get_user_inputs(required_inputs: dict, auto_selected_inputs: dict) -> dict:
    """
    Display input fields in Streamlit based on required fields specified in the subagent's output.
    
    Args:
    - required_inputs: Dictionary of input names and whether they are required.
    - auto_selected_inputs: Dictionary of inputs auto-selected by the subagent.
    
    Returns:
    - Dictionary of user inputs for required fields.
    """
    user_inputs = {}
    
    st.write("### Review and Adjust Inputs")
    for input_name, requirement in required_inputs.items():
        is_required = (requirement == "required")
        current_value = auto_selected_inputs.get(input_name, None)
        
        # Show the current input field with pre-filled value if available
        user_input = get_input_field(input_name, current_value=current_value)
        
        if is_required and not user_input:
            st.warning(f"{input_name} is required.")
        else:
            user_inputs[input_name] = user_input
    
    if st.button("Confirm and Deploy"):
        if all(user_inputs.values()):
            st.write("Inputs confirmed:", user_inputs)
            # Proceed with deployment here
        else:
            st.warning("Please fill in all required fields before deploying.")
    
    return user_inputs

# Example usage
def main():
    # Example output from subagent for required fields
    required_inputs = {
        "ami_id": "optional", 
        "instance_type": "required", 
        "vpc_id": "optional", 
        "name": "required"
    }
    
    # Example auto-selected inputs from system state
    auto_selected_inputs = {
        "ami_id": "ami-0abcdef1234567890",  # This should match a value from fetch_ami_catalog
        "vpc_id": "vpc-1234abcd"
    }
    
    # Collect and review inputs from user
    get_user_inputs(required_inputs, auto_selected_inputs)

if __name__ == "__main__":
    main()
