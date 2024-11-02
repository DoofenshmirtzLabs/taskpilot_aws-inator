import pandas as pd
class State:
    state_data = {}

    @classmethod
    def store(cls, agent_name, task, result):
        if agent_name not in cls.state_data:
            cls.state_data[agent_name] = []
        # Append the task and result as a dictionary to the agent's list
        cls.state_data[agent_name].append({"task": task, "result": result})

    @classmethod
    def get_state(cls, agent_name):
        return cls.state_data.get(agent_name, [])

    @classmethod
    def get_all_states(cls):
        return cls.state_data

    @classmethod
    def dump_to_file(cls, file_path):
        # Flatten the state_data dictionary for easier file writing
        flattened_data = []
        for agent, tasks in cls.state_data.items():
            for entry in tasks:
                flattened_data.append({
                    "agent_name": agent,
                    "task": entry["task"],
                    "result": entry["result"]
                })

        # Convert to DataFrame and write to file
        df = pd.DataFrame(flattened_data)

        # Check if the file already exists
        try:
            # Append data to existing file
            df.to_csv(file_path, mode='a', header=False, index=False)
        except FileNotFoundError:
            # If the file does not exist, write it for the first time
            df.to_csv(file_path, index=False)

    @classmethod
    def extract_results(cls):
        results_lines = []
        for agent, tasks in cls.state_data.items():
            for task in tasks:
                # Extracting the result as a string
                result_line = f"{task['result']}"
                results_lines.append(result_line)
        # Concatenate the results with new line characters
        return "\n".join(results_lines)
