import json
import nlpaug.augmenter.word as naw
import random

# Initialize the contextual word embedding augmenter
contextual_aug = naw.ContextualWordEmbsAug(model_path='bert-base-uncased', action="substitute")

# Load the original JSONL dataset
input_file = 'C:\\Users\\user\\TASKPILOT_V2\\finetuning_data\\decision_agent.jsonl'
output_file = 'augmented_dataset_decisionagent.jsonl'

# Template-based augmentation options
templates = [
    "Please {action} the {resource}.",
    "Could you {action} a {resource}?",
    "{action} a {resource} for the new setup.",
    "Initiate {resource} {action}.",
    "I need a {resource} {action}.",
]

# Function to generate augmented prompts
def generate_augmented_prompts(prompt, num_variations=5):
    variations = []
    
    # Contextual-based augmentation
    for _ in range(num_variations // 2):  # Half of the variations
        variations.append(contextual_aug.augment(prompt))
    
    # Template-based augmentation
    for _ in range(num_variations - len(variations)):
        action, resource = prompt.split(" ", 1)  # Splitting by the first space
        template = random.choice(templates)
        variations.append(template.format(action=action.lower(), resource=resource.lower()))
    
    return variations

# Process each line in the dataset
with open(input_file, 'r') as infile, open(output_file, 'w') as outfile:
    for line in infile:
        # Load JSON object
        data = json.loads(line)
        
        # Get the original user prompt
        original_prompt = data["messages"][1]["content"]
        
        # Generate augmented prompts
        augmented_prompts = generate_augmented_prompts(original_prompt)
        
        # Add augmented prompts as separate entries in the output JSONL
        for prompt in augmented_prompts:
            # Create a copy of the original data to modify
            new_data = data.copy()
            new_data["messages"][1]["content"] = prompt  # Replace with augmented prompt
            
            # Write the new entry to the output file
            outfile.write(json.dumps(new_data) + '\n')
