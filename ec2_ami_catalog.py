import boto3
import streamlit as st
from fetchoptions import fetch_ami_catalog,fetch_instance_types

# Function to fetch EC2 image catalog (AMIs)
aws_access_key = ''
aws_secret_key = ''
region_name = ''
session = boto3.Session(
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=region_name,
        )
ec2_client = session.client('ec2')

def fetch_limited_ec2_image_catalog(owner='self', filters=None, max_results=10):
    
    try:
        paginator = ec2_client.get_paginator('describe_images')
        page_iterator = paginator.paginate(
            Owners=[owner],  # 'self' for AMIs owned by your account, or 'amazon' for public AMIs
            Filters=filters,
            PaginationConfig={
                'MaxItems': max_results,  # Limit the number of total AMIs to return
                'PageSize': max_results  # Number of AMIs per page
            }
        )
        
        # Collecting the results
        images = []
        for page in page_iterator:
            images.extend(page.get('Images', []))
            if len(images) >= max_results:
                break

        return images[:max_results]  # Return only the max_results count

    except Exception as e:
        st.error(f"Error fetching AMI catalog: {e}")
        return []

# Streamlit frontend to display the AMI catalog
def show_ami_catalog():
    st.title("EC2 AMI Catalog")

    # User can choose the owner (self-owned AMIs or public AMIs from Amazon)
    owner = st.selectbox("Select AMI Owner", ['self', 'amazon'])

    # Example filters (user can modify these in the frontend if necessary)
    architecture = st.selectbox("Select Architecture", ['x86_64', 'arm64'])
    platform = st.selectbox("Select Platform", ['windows', 'linux'])

    filters = [
        {'Name': 'architecture', 'Values': [architecture]},
        {'Name': 'platform', 'Values': [platform]}
    ]

    # Fetch the EC2 image catalog using selected filters
    image_catalog = fetch_limited_ec2_image_catalog(owner=owner, filters=filters)

    # Display the fetched AMIs
    if image_catalog:
        st.subheader(f"Available AMIs ({len(image_catalog)} found):")
        for image in image_catalog:
            st.write(f"**Image ID**: {image['ImageId']}, **Name**: {image['Name']}, **Architecture**: {image['Architecture']}")
    else:
        st.write("No AMIs found with the selected criteria.")

# Streamlit entry point
if __name__ == "__main__":
    show_ami_catalog()
