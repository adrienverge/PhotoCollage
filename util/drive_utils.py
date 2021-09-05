from googleapiclient.errors import Error
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive
from joblib import Parallel, delayed
import os
from yearbook.Yearbook import Yearbook
from retrying import retry

"""
This method is necessary to download and process the corpus from the Google Drive for now
This is a custom method which only integrates with Google Drive for now.
We will have to implement more integrations in the future, like Shutterfly or something else for example.
"""


def download_yearbook_corpus(yearbook: Yearbook, output_dir, processed_corpus):
    if not os.path.exists(output_dir):
        os.mkdir(output_dir)

    # Request permissions from Google auth for now.
    gauth = GoogleAuth()
    gauth.LocalWebserverAuth()  # client_secrets.json need to be in the same directory as the script
    drive = GoogleDrive(gauth)

    # View all folders and file in your Google Drive
    # Since we're using the event name as part of the tuple, there's a chance that we'll
    # make duplicate copies and download the same folder multiple times
    # This is going to be acceptable for the time being as we'll create a page per event
    folders_with_event_name = yearbook.get_drive_folders_with_event_name()

    print("Will download from ")
    print(folders_with_event_name)

    Parallel(n_jobs=12)(
        delayed(__download_folder__)(yearbook, drive, folder_with_event[0], folder_with_event[1], output_dir,
                                     processed_corpus)
        for folder_with_event in folders_with_event_name)


@retry(stop_max_attempt_number=3)
def __download_folder__(yearbook: Yearbook, drive, folder, event_name, output_dir, processed_corpus):
    try:
        print('Processing folder %s for %s' % (folder, event_name))
        files_in_folder = drive.ListFile({'q': "'%s' in parents and trashed=false" % folder}).GetList()

        out_folder = os.path.join(output_dir, event_name)

        if not os.path.exists(out_folder):
            os.mkdir(out_folder)

        all_faces_in_images = [__download_file_and_recognize_faces__(yearbook, drive, file, out_folder, event_name) for
                               file
                               in files_in_folder]

        with open(processed_corpus, 'w') as file_handle:
            for string in all_faces_in_images:
                if string is not None:
                    file_handle.write('%s' % string)

        # print("Total number of files downloaded from folder: %s is %s" % (folder, sum(count_downloads)))
    except RuntimeError as e:
        print("Running into issues downloading from %s" % folder)


@retry(stop_max_attempt_number=3)
def __download_file_and_recognize_faces__(yearbook: Yearbook, drive, file, output_dir, event_name):
    print('Title: %s, ID: %s, MimeType: %s, CreatedDate: %s' % (
        file['title'], file['id'], file['mimeType'], file['createdDate']))

    try:
        mime_type = file['mimeType']
        if mime_type.startswith('image'):
            print('processing %s from folder %s' % (file['id'], event_name))

            # TODO: This needs to come from a library or a global mapping
            if mime_type.endswith('jpeg'):
                extension = ".jpg"
            elif mime_type.endswith('png'):
                extension = ".png"

            file_path = os.path.join(output_dir, file['id'] + extension)
            if os.path.exists(file_path):
                print("Skipping download ...")
            else:
                file_temp = drive.CreateFile({'id': file['id']})
                file_temp.GetContentFile(file_path)

            faces = yearbook.multiCNNFaceRecognizer.process(file_path)

            if faces:
                faces_with_scores = list(map(lambda x: (
                    x.top_prediction.label, str(x.top_prediction.confidence), ",".join(map(lambda y: str(y), x.bb))),
                                             faces))
                out_str = file['id'] + extension + "\t" + ";".join(map(lambda x: x[0] + ":" + x[1] + ":" + x[2],
                                                                       sorted(faces_with_scores, key=lambda x: x[1],
                                                                              reverse=True))) \
                          + "\t" + event_name + "\n"

                return out_str
            else:
                print("No faces found in %s and event %s\n" % (file['id'], event_name))
                return ""
    except Error as e:
        print('Skipping file %s due to errors' % file['title'])
        return ""
    except RuntimeError as e:
        return ""
