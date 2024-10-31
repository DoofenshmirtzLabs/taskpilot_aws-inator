
import streamlit as st
from fetchoptions import fetch_ami_catalog, fetch_instance_types

OPTION_FETCHERS = {
    "ami_id": fetch_ami_catalog,
    "instance_type": fetch_instance_types,
}
def get_input_field(input_name: str, current_value: str = None) -> str:
    fetch_options = OPTION_FETCHERS.get(input_name, None)
    if fetch_options:
        options = fetch_options()
        if isinstance(options, dict):
            option_list = list(options.keys())
            value_list = list(options.values())
            index = value_list.index(current_value) if current_value in value_list else 0
            selected_option = st.selectbox(f"Select {input_name}", options=option_list, index=index)
            return options[selected_option]
        elif isinstance(options, list):
            index = options.index(current_value) if current_value in options else 0
            return st.selectbox(f"Select {input_name}", options=options, index=index)
    else:
        return st.text_input(f"Please provide a value for {input_name}:", value=current_value if current_value else "")

def get_user_inputs(required_inputs: dict, auto_selected_inputs: dict) -> dict:
    user_inputs = {}
    
    st.write("### Review and Adjust Inputs")  # Header for inputs section
    for input_name, requirement in required_inputs.items():
        is_required = (requirement == "required")
        current_value = auto_selected_inputs.get(input_name, None)
        
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
    print('user_inputs in get inputs',user_inputs)
    return user_inputs    
required_inputs = {
    "image_id": "required",
    "instance_type": "required"
}
auto_selected_inputs = {}

user_inputs=get_user_inputs(required_inputs,auto_selected_inputs)
print('user_inputs',user_inputs)