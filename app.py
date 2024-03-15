import json
import boto3
import os
import mimetypes

# Initialize the Boto3 S3 client
s3_client = boto3.client('s3')

# Set the local directory containing the files to upload
local_directory = './static_site'

# set bucket name and create bucket
bucket_name = YOUR_BUCKET_NAME_HERE
s3_client.create_bucket(
    Bucket=bucket_name,
    CreateBucketConfiguration={
        'LocationConstraint': 'us-east-2',
    }
)

# Upload React app code to S3 bucket
print('Uploading files...')
for root, dirs, files in os.walk(local_directory):
    print(f'\n\nroot:{root}\ndirs:{dirs}\nfiles{files}')
    for file in files:
        local_file_path = os.path.join(root,file)

        # We need to preserve the folder structure while uploading for that the following: -
        # To preserve the relative path of the files and as when serving the site
        # it looks for static/css or /js hence we replace the \ with /.
        # Also without os.path.join(local_repo_path, 'build') and extra prefix of build\ is 
        # added to the s3 object key.
        s3_object_key = os.path.relpath(local_file_path, local_directory).replace('\\', '/')

        # Determine content type based on file extension
        content_type, _ = mimetypes.guess_type(local_file_path)
        if content_type is None:
            content_type = 'application/octet-stream'
        

        try:
            s3_client.upload_file(
                    local_file_path, 
                    bucket_name, 
                    s3_object_key,
                    ExtraArgs={'ContentType': content_type}
                )
            print(f"Uploaded {local_file_path} to S3 bucket {bucket_name} with key {s3_object_key}")
        except Exception as e:
            print(f"Error uploading {local_file_path} to S3 bucket: {e}")

# Enable static website hosting for the bucket
try:
    s3_client.put_bucket_website(
        Bucket=bucket_name,
        WebsiteConfiguration={
            'IndexDocument': {'Suffix': 'index.html'}
        }
    )
    print(f"Static website hosting enabled for S3 bucket {bucket_name}")
except Exception as e:
    print(f"Error enabling static website hosting for S3 bucket: {e}")

# Define the bucket policy to grant read access to everyone
bucket_policy = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": "*",
            "Action": [
                    "s3:GetObject"
                ],
            "Resource": f"arn:aws:s3:::{bucket_name}/*"
        }
    ]
}

# Convert the policy to a JSON string
bucket_policy_json = json.dumps(bucket_policy)

# Apply the bucket policy
s3_client = boto3.client('s3')
s3_client.put_bucket_policy(Bucket=bucket_name, Policy=bucket_policy_json)
print(f"Bucket policy applied successfully for bucket {bucket_name}")

# Get a list of all objects in the bucket
response = s3_client.list_objects_v2(Bucket=bucket_name)

for obj in response['Contents']:
    object_key = obj['Key']
    try:
        s3_client.put_object_acl(
            ACL='public-read',
            Bucket=bucket_name,
            Key=object_key
        )
        print(f"{object_key} is now public and readable by everyone.")
    except Exception as e:
        print(f"Error making object public: {e}")

