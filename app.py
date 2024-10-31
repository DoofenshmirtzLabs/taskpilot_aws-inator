import streamlit as st
from agents.decision_agent import DecisionAgent
from agents.state_manager import State
from fetchoptions import fetch_ami_catalog, fetch_instance_types
import datetime

# Initialize the DecisionAgent
aws_access_key = ''
aws_secret_key = ''
region_name = 'us-west-2'
agent_name='Task_pilot_aws'
task='help users deploy aws infra'
result="how can i help you?"
State.state_data = {}
State.store(agent_name,task,result)
decision_agent = DecisionAgent(aws_access_key, aws_secret_key, region_name)

# Updated CSS with more compact chat container
custom_css = """
    <style>
    .main > div {
        padding-top: 0 !important;
    }
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    [data-testid="stHorizontalBlock"] {
        height: 100vh;
        padding: 1rem;
        gap: 1rem;
    }
    [data-testid="column"] {
        background: white;
        padding: 1.5rem !important;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .chat-container {
        display: flex;
        flex-direction: column;
        background: white;
        border-radius: 10px;
        margin-bottom: 1rem;
    }
    .chat-messages {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        max-height: 400px;
        overflow-y: auto;
        padding: 0.5rem;
    }
    .message {
        max-width: 80%;
        padding: 0.6rem 0.8rem;
        border-radius: 15px;
        margin: 0.2rem 0;
        font-size: 0.9rem;
        word-wrap: break-word;
    }
    .user-message {
        background-color: #007bff;
        color: white;
        align-self: flex-end;
        border-bottom-right-radius: 5px;
    }
    .system-message {
        background-color: #f0f2f5;
        color: black;
        align-self: flex-start;
        border-bottom-left-radius: 5px;
    }
        <style>
     .main > div {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Remove default Streamlit margins */
    .block-container {
        padding: 0 !important;
        max-width: 100% !important;
    }
    
    /* Ensure columns take full height */
    [data-testid="stHorizontalBlock"] {
        height: calc(100vh - 80px);
        padding: 1rem;
        gap: 1rem;
    }
    
    /* Style the columns */
    [data-testid="column"] {
        background: white;
        padding: 1.5rem !important;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    
    /* Terminal container */
    .terminal-container {
        background-color: #1e1e1e;
        border-radius: 8px;
        height: 45vh;
        overflow-y: auto;
        margin-bottom: 1rem;
        padding: 1rem;
        border: 1px solid #333;
    }
    
    /* Terminal text */
    .terminal-text {
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
        line-height: 1.5;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    
    /* Task history container */
    .task-history {
        background-color: #f5f5f5;
        border-radius: 8px;
        height: 45vh;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
    }
    
    /* Headers */
    .status-header {
        color: #00ff00;
        border-bottom: 1px solid #00ff00;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        position: sticky;
        top: 0;
        background-color: #1e1e1e;
    }
    
    /* Custom scrollbar */
    .terminal-container::-webkit-scrollbar,
    .task-history::-webkit-scrollbar {
        width: 8px;
    }
    
    .terminal-container::-webkit-scrollbar-track,
    .task-history::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
    }
    
    .terminal-container::-webkit-scrollbar-thumb {
        background: #333;
        border-radius: 4px;
    }
    
    .task-history::-webkit-scrollbar-thumb {
        background: #999;
        border-radius: 4px;
    }
    
    /* Input field styling */

    
    /* Submit button styling */
    .stButton button {
        background-color: #0066cc;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
        font-size: 1rem;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    
    .stButton button:hover {
        background-color: #0052a3;
    }
    
    /* Task container specific styles */
    .task-container {
        background-color: #f5f5f5;
        border-radius: 8px;
        height: 45vh;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
        font-family: 'Inter', sans-serif;
    }
    
    .task-header {
        color: #2c3e50;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        position: sticky;
        top: 0;
        background-color: #f5f5f5;
        font-weight: bold;
    }
    
    .task-item {
        background-color: white;
        border-radius: 6px;
        padding: 0.8rem;
        margin-bottom: 0.8rem;
        border-left: 4px solid #3498db;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    

    
    .task-content {
        color: #2c3e50;
        font-size: 0.9rem;
    }
    
.terminal-text {
        color: #00ff00;
        font-family: 'Courier New', Courier, monospace;
        font-size: 14px;
        line-height: 1.5;
        white-space: pre-wrap;
        word-wrap: break-word;
    }
    .task-history {
        background-color: #f5f5f5;
        border-radius: 8px;
        height: 40vh;
        overflow-y: auto;
        padding: 1rem;
        border: 1px solid #ddd;
    }
    .status-header {
        color: #00ff00;
        border-bottom: 1px solid #00ff00;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
        font-size: 1.2rem;
        position: sticky;
        top: 0;
        background-color: #1e1e1e;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
        padding: 0.5rem 1rem;
    }
    button[kind="secondary"] {
        border-radius: 20px;
    }
    
    .task-status-success {
        border-left-color: #2ecc71;
    }
    
    .task-status-error {
        border-left-color: #e74c3c;
    }
    
    .task-status-pending {
        border-left-color: #f1c40f;
    }
    </style>
"""
def initialize_session_state():
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'task_history' not in st.session_state:
        st.session_state.task_history = []

def render_terminal_output(content):
    terminal_html = f"""
        <div class="terminal-container">
            <div class="status-header">Machine Status</div>
            <div class="terminal-text">{content}</div>
        </div>
    """
    return st.markdown(terminal_html, unsafe_allow_html=True)

def render_task_history(message):
    st.subheader("Task History")
    st.markdown(f"""
               <div class="task-history">>
                    <div class="message">{message}</div>
                </div>
            """, unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)



def add_message(content, is_user=True):
    st.session_state.messages.append({
        'content': content,
        'is_user': is_user,
    })

def add_task_to_history(task, result):
    new_task = {
        'task': task,
        'result': result,
    }
    st.session_state.task_history.append(new_task)
def render_chat_messages():
    chat_html = "<div class='chat-messages'>"
    if not st.session_state.messages:
        chat_html += "<div class='empty-chat-message'>No messages yet. Start a conversation!</div>"
    else:
        for msg in st.session_state.messages:
            class_name = "user-message" if msg['is_user'] else "system-message"
            chat_html += f"<div class='message {class_name}'>{msg['content']}</div>"
    chat_html += "</div>"
    st.markdown(chat_html, unsafe_allow_html=True)
OPTION_FETCHERS = {
    "ami_id": fetch_ami_catalog,
    "image_id":fetch_ami_catalog,
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
    agent='user_inputs'
    task='take inputs from user'
    result=user_inputs
    State.store(agent,task,result)
    return user_inputs  
def main():
    st.set_page_config(layout="wide", page_title="AWS_TASKPILOT")
    st.markdown(custom_css, unsafe_allow_html=True)
    initialize_session_state()
    
    col1, col2 = st.columns([1, 1])

    with col1:
        st.title("AWS Infrastructure Deployment with AI Agents")
        
        # Chat container with messages
       
        render_chat_messages()
        
        
        # Input area
        with st.container():
            
            
                
                user_input = st.text_input("", placeholder="Enter your prompt...", key="user_input")
             
               
                st.markdown("<div class='chat-container'>", unsafe_allow_html=True)
                
            
                if st.button("Send", key="send_button"):
                    if user_input:
                        add_message(user_input, is_user=True)
                        
                        try:
                            decision_agent.process_user_prompt(user_input)
                            
    
                        except Exception as e:
                            error_message = str(e)
                            add_message(f"Error: {error_message}", is_user=False)
                            add_task_to_history(user_input, f"Error: {error_message}")
                            st.error(f"Error processing request: {error_message}")
        
                st.markdown("</div>", unsafe_allow_html=True)

    
       
    with col2:
        # Machine Status
        file_path = "datastore.csv"
        State.dump_to_file(file_path)
        state_content = State.get_all_states()
        print('state_content',state_content)
        render_terminal_output(state_content)
        
        # Task History
        if st.session_state.task_history:
            render_task_history(st.session_state.task_history)

if __name__ == "__main__":
    main()