import os.path
import pandas as pd
import pickle
import io
from flask import Flask, render_template_string, send_file, request
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from flask import make_response

SCOPES = ['https://www.googleapis.com/auth/drive']
app = Flask(__name__)

def get_credentials():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return creds

@app.route('/download_revision/<string:file_id>/<string:revision_id>')
def download_revision(file_id, revision_id):
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    mime_type = request.args.get('mime_type')
    
    # Get the file's metadata to obtain the original file name
    file_metadata = service.files().get(fileId=file_id).execute()
    original_filename = file_metadata.get('name', f'{file_id}_{revision_id}')  # Default to file_id_revision_id if name is not available
    
    export_mimes = {
        'application/vnd.google-apps.document': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.google-apps.spreadsheet': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.google-apps.presentation': 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    }
    
    if mime_type in export_mimes:
        g_request = service.files().export(fileId=file_id, mimeType=export_mimes[mime_type])
        extension = '.docx' if mime_type == 'application/vnd.google-apps.document' else '.xlsx'
    else:
        g_request = service.revisions().get_media(fileId=file_id, revisionId=revision_id)
        extension = ''  # You may need to handle other file types and extensions here
    
    # Correctly form the download filename by only appending the correct extension
    download_filename = f'{original_filename}{extension}'
    
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, g_request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
    fh.seek(0)
    
    # Determine the MIME type for the response
    response_mime_type = export_mimes.get(mime_type, 'application/octet-stream')
    
    return send_file(
        fh,
        mimetype=response_mime_type,
        as_attachment=True,
        download_name=download_filename
    )



@app.route('/make_xlsx')
def make_xlsx():
    _, data, _ = generate_html_and_excel()
    df = pd.DataFrame(data, columns=['Folder', 'File', 'Type', 'Filetype', 'Revision', 'Timestamp', 'Modified by', 'Full Path'])
    excel_path = 'Drive_Structure.xlsx'
    df.to_excel(excel_path, index=False)
    return send_file(excel_path, as_attachment=True)

def generate_html_and_excel(service=None, folder_id='root', folder_name='ROOT', path='', counters=None):
    if counters is None:
        counters = {"folders": 0, "files": 0, "revisions": 0}
    folder_structure = ''
    root_files = ''
    data = []
    counters['folders'] += 1
    if not service:
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
    folder_structure += f"<div class='folder'><div class='folder-header' onclick='toggleContent(this)'>📁 {folder_name}</div><div class='folder-content'>"
    results = service.files().list(q=f"'{folder_id}' in parents", pageSize=1000, fields="nextPageToken, files(id, name, mimeType)").execute()
    items = results.get('files', [])
    for item in items:
        if item['mimeType'] != 'application/vnd.google-apps.folder':
            counters['files'] += 1
            file_id = item['id']
            file_name = item['name']
            mime_type = item['mimeType']
            filetype, icon = get_filetype_and_icon(mime_type)
            root_files += f"<div class='file'><div class='file-header'>{icon} {filetype} {file_name}</div>"
            revisions = service.revisions().list(fileId=file_id, fields="revisions(id,modifiedTime,lastModifyingUser)").execute().get('revisions', [])
            for rev in revisions:
                counters['revisions'] += 1
                modified_by = rev['lastModifyingUser']['displayName'] if 'lastModifyingUser' in rev else 'Unknown'
                root_files += f"<div class='revision'>Revision: {rev['id']} | Timestamp: {rev['modifiedTime']} | Modified by: {modified_by} | <a href='/download_revision/{file_id}/{rev['id']}?mime_type={mime_type}' target='_blank'>Download</a></div>"
                data.append([folder_name, file_name, mime_type, filetype, rev['id'], rev['modifiedTime'], modified_by, f"{path}/{file_name}"])
            root_files += "</div>"
    folder_structure += root_files
    for item in items:
        if item['mimeType'] == 'application/vnd.google-apps.folder':
            sub_folder_structure, sub_data, _ = generate_html_and_excel(service, item['id'], item['name'], f"{path}/{item['name']}", counters)
            folder_structure += sub_folder_structure
            data.extend(sub_data)
    folder_structure += "</div></div>"
    return folder_structure, data, counters

def get_filetype_and_icon(mime_type):
    icons = {
        'application/vnd.google-apps.document': '📄',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '📄',
        'application/vnd.google-apps.spreadsheet': '📊',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '📊',
        'application/vnd.google-apps.presentation': '📽',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': '📽',
        'application/pdf': '📋'
    }
    filetypes = {
        'application/vnd.google-apps.document': '[Google Docs]',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '[Word]',
        'application/vnd.google-apps.spreadsheet': '[Google Sheets]',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '[Excel]',
        'application/vnd.google-apps.presentation': '[Google Slides]',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation': '[PowerPoint]',
        'application/pdf': '[PDF]'
    }
    return filetypes.get(mime_type, '[Unknown]'), icons.get(mime_type, '❓')

@app.route('/')
def index():
    folder_structure, data, counters = generate_html_and_excel()
    html_structure = f"""
    <html>
    <head>
        <title>Google Drive Structure</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                background-color: #f5f5f5;
                color: #333;
            }}
            h1, h3 {{
                text-align: center;
            }}
            hr {{
                margin: 20px 0;
            }}
            .folder, .file {{
                border: 1px solid #ccc;
                border-radius: 4px;
                margin: 10px;
                padding: 10px;
                background-color:
                #fff;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            .folder-content, .file-content {{
                display: none;
                margin-left: 20px;
            }}
            .folder-header, .file-header {{
                cursor: pointer;
                font-weight: bold;
            }}
            .revision {{
                margin-left: 10px;
                font-size: 0.9em;
                color: #777;
            }}
            .counters {{
                text-align: center;
                font-size: 1.2em;
                margin-bottom: 20px;
            }}
            .counters strong {{
                color: #333;
            }}
            .counters span {{
                color: #777;
                margin-right: 20px;
            }}
            button {{
                cursor: pointer;
                padding: 8px 16px;
                background-color: #007bff;
                color: #fff;
                border: none;
                border-radius: 4px;
                font-size: 1em;
            }}
        </style>
        <script>
            function toggleContent(element) {{
                let content = element.nextElementSibling;
                if(content.style.display === 'none' || content.style.display === '') {{
                    content.style.display = 'block';
                }} else {{
                    content.style.display = 'none';
                }}
            }}
        </script>
    </head>
    <body>
        <h1>Google Drive Revisions</h1>
        <h3>- by Tina Vea</h3>
        <hr>
        <div class="counters">
            <span><strong>Folders:</strong> {counters['folders']}</span>
            <span><strong>Files:</strong> {counters['files']}</span>
            <span><strong>Revisions:</strong> {counters['revisions']}</span>
        </div>
        <div style="text-align: center;">
            <a href='/make_xlsx' download><button>Make .xlsx</button></a>
        </div>
        {folder_structure}
    </body>
    </html>
    """
    return render_template_string(html_structure, data=data)

if __name__ == '__main__':
    app.run(debug=True)
