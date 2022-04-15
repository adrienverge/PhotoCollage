from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaFileUpload

import os
from timeit import default_timer as timer

gauth = GoogleAuth()
drive = GoogleDrive(gauth)

SCOPES = ['https://www.googleapis.com/auth/drive']


def get_url_from_file_id(file_id: str):
    return "https://drive.google.com/file/d/%s/view?usp=sharing" % file_id


def get_file_id_from_url(url: str):
    if url is None:
        return None

    return url.split("/")[-2]


def check_file_exists(real_folder_id, file_id):
    try:
        service = build('drive', 'v3', credentials=get_credentials())
        g_file = service.files().get(fileId=file_id, fields='parents').execute()
        print(g_file)
        return True
    except HttpError as error:
        print(F'An error occurred: {error}')
        return False


def upload_with_item_check(real_folder_id, pdf_file, file_id):
    try:
        if file_id is not None:
            service = build('drive', 'v3', credentials=get_credentials())
            g_file = service.files().get(fileId=file_id, fields='parents').execute()

            if g_file is not None:
                print("File exists, skipping upload PHEW!! %s " % g_file)
                return file_id
        else:
            print("File does not exist, uploading %s !!" % pdf_file)
            return upload_to_folder(real_folder_id, pdf_file)
    except HttpError as error:
        print(F'An error occurred: {error}')
        return None


def upload_to_folder(real_folder_id, pdf_file):
    """Upload a file to the specified folder and prints file ID, folder ID
    Args: Id of the folder
    Returns: ID of the file uploaded
    Load pre-authorized user credentials from the environment.
    TODO(developer) - See https://developers.google.com/identity
    for guides on implementing OAuth2 for the application.
    """
    start = timer()
    try:
        # create gmail api client
        service = build('drive', 'v3', credentials=get_credentials())
        filename = os.path.basename(pdf_file)

        file_metadata = {
            'name': filename,
            'parents': [real_folder_id]
        }
        media = MediaFileUpload(pdf_file,
                                mimetype='application/pdf', resumable=True)
        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, media_body=media,
                                      fields='id').execute()
        print(F'File with ID: "{file.get("id")}" has added to the folder with '
              F'ID "{real_folder_id}".')

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None

    end = timer()
    print("Time in seconds to upload %s" % str(end - start))
    return file.get('id')


def read_files():
    try:
        service = build('drive', 'v3', credentials=get_credentials())

        # Call the Drive v3 API
        results = service.files().list(
            pageSize=10, fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])

        if not items:
            print('No files found.')
            return
        print('Files:')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))

    except HttpError as error:
        # TODO(developer) - Handle errors from drive API.
        print(f'An error occurred: {error}')


def get_credentials():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return creds
