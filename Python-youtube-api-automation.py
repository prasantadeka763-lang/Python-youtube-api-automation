import os
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
from googleapiclient.http import MediaFileUpload

# Define the scope required for uploading videos
SCOPES = ["https://googleapis.com"]

def get_authenticated_service():
    """Handles the OAuth2 authentication flow."""
    # Ensure client_secrets.json is in your current directory
    client_secrets_file = "client_secrets.json"
    
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        client_secrets_file, SCOPES
    )
    
    # Opens your browser to authenticate
    credentials = flow.run_local_server(port=0)
    
    return googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials
    )

def initialize_upload(youtube, options):
    """Prepares and executes the resumable media upload."""
    body = {
        "snippet": {
            "title": options.get("title", "Test Title"),
            "description": options.get("description", "Uploaded via Python"),
            "tags": options.get("tags", []),
            "categoryId": options.get("category_id", "22") # 22 is People & Blogs
        },
        "status": {
            "privacyStatus": options.get("privacy_status", "private"), # public, private, unlisted
            "selfDeclaredMadeForKids": False
        }
    }

    # Call the API's videos.insert method to create the upload request
    insert_request = youtube.videos().insert(
        part=",".join(body.keys()),
        body=body,
        media_body=MediaFileUpload(
            options["file"], 
            chunksize=-1, # -1 means standard upload size, or set specific bytes
            resumable=True
        )
    )

    print("Uploading file...")
    resumable_upload(insert_request)

def resumable_upload(request):
    """Executes the video upload chunks and tracks progress."""
    response = None
    error = None
    retry = 0
    
    while response is None:
        try:
            status, response = request.next_chunk()
            if response is not None:
                if "id" in response:
                    print(f"\nSuccess! Video uploaded.")
                    print(f"Video ID: {response['id']}")
                    print(f"Watch Link: https://youtube.com{response['id']}")
                else:
                    exit(f"The upload failed with an unexpected response: {response}")
            elif status:
                print(f"Uploaded {int(status.progress() * 100)}%...")
        except googleapiclient.errors.HttpError as e:
            if e.resp.status in:
                print(f"Temporary server error {e.resp.status}. Retrying...")
            else:
                raise e

if __name__ == "__main__":
    # 1. Authenticate with Google
    youtube_client = get_authenticated_service()

    # 2. Configure video details
    video_details = {
        "file": "my_video.mp4",              # Path to local video file
        "title": "My Automatic Upload",       # Video Title
        "description": "This is a test description.", # Video Description
        "tags": ["python", "automation"],    # Video Tags
        "category_id": "22",                 # 22 is Entertainment/Blogs
        "privacy_status": "private"          # 'private', 'public', or 'unlisted'
    }

    # 3. Start upload
    if os.path.exists(video_details["file"]):
        initialize_upload(youtube_client, video_details)
    else:
        print(f"Error: Could not find the file '{video_details['file']}' in this directory.")
