def fetch_ami_catalog():
    return {
        "Ubuntu 18.04 LTS": "ami-07c5ecd8498c59db5", 
        "Amazon Linux 2": "ami-07c5ecd8498c59db5"
    }

def fetch_instance_types():
    return ["t2.micro", "t2.small", "t2.medium"]