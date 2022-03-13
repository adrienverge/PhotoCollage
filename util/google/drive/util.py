from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

gauth = GoogleAuth()
drive = GoogleDrive(gauth)


def upload_pdf_file(parent_folder_id: str, full_path_pdf: str):
    gfile = drive.CreateFile({'parents': [{'id': parent_folder_id}]})
    # Read file and set it as the content of this instance.
    gfile.SetContentFile(full_path_pdf)
    gfile.Upload()  # Upload the file.
    gfile.clear()
