import io
import json
import os

import httplib2
import google_auth_httplib2
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload
from docx import Document

_SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]

_drive_service = None
_docs_service = None


def _authorized_http():
    # Disable SSL verification to handle self-signed certs in sandbox environments
    creds = _credentials()
    return google_auth_httplib2.AuthorizedHttp(
        creds, http=httplib2.Http(disable_ssl_certificate_validation=True)
    )


def _credentials():
    info = json.loads(os.environ["GOOGLE_SERVICE_ACCOUNT_JSON"])
    return service_account.Credentials.from_service_account_info(info, scopes=_SCOPES)


def get_drive_service():
    global _drive_service
    if _drive_service is None:
        _drive_service = build("drive", "v3", http=_authorized_http())
    return _drive_service


def get_docs_service():
    global _docs_service
    if _docs_service is None:
        _docs_service = build("docs", "v1", http=_authorized_http())
    return _docs_service


def download_docx_text(file_id: str) -> str:
    """Download or export a file from Drive and return its plain text content.

    Handles both native Google Docs (exported as docx) and binary .docx files.
    """
    drive = get_drive_service()
    meta = drive.files().get(fileId=file_id, fields="mimeType").execute()
    mime = meta.get("mimeType", "")

    if mime == "application/vnd.google-apps.document":
        # Google Doc — export as docx
        request = drive.files().export_media(
            fileId=file_id,
            mimeType="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    else:
        # Binary .docx or other file — download directly
        request = drive.files().get_media(fileId=file_id)

    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    buf.seek(0)
    doc = Document(buf)
    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def find_file_in_folder(folder_id: str, name: str) -> str | None:
    """Return the file ID of the first file with the given name in the folder, or None."""
    drive = get_drive_service()
    safe_name = name.replace("'", "\\'")
    q = f"'{folder_id}' in parents and name = '{safe_name}' and trashed = false"
    result = drive.files().list(q=q, fields="files(id)").execute()
    files = result.get("files", [])
    return files[0]["id"] if files else None


def read_text_file_in_folder(folder_id: str, name: str) -> str:
    """Read a plain-text file by name from a Drive folder. Returns '' if not found."""
    drive = get_drive_service()
    file_id = find_file_in_folder(folder_id, name)
    if not file_id:
        return ""
    request = drive.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8")


def write_text_file_in_folder(folder_id: str, name: str, content: str) -> None:
    """Write (create or update) a plain-text file by name in a Drive folder."""
    drive = get_drive_service()
    file_id = find_file_in_folder(folder_id, name)
    buf = io.BytesIO(content.encode("utf-8"))
    media = MediaIoBaseUpload(buf, mimetype="text/plain")
    if file_id:
        drive.files().update(fileId=file_id, media_body=media).execute()
    else:
        metadata = {"name": name, "parents": [folder_id]}
        drive.files().create(body=metadata, media_body=media).execute()


def read_json_staging(folder_id: str, name: str) -> list:
    """Read the LinkedIn staging JSON file. Returns [] if missing or empty."""
    content = read_text_file_in_folder(folder_id, name)
    if not content.strip():
        return []
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return []


def clear_json_staging(folder_id: str, name: str) -> None:
    """Reset the LinkedIn staging file to an empty array."""
    write_text_file_in_folder(folder_id, name, "[]")


def upload_docx(folder_id: str, filename: str, docx_bytes: bytes) -> str:
    """Upload a .docx file to Drive and return its file ID."""
    drive = get_drive_service()
    buf = io.BytesIO(docx_bytes)
    media = MediaIoBaseUpload(
        buf,
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    metadata = {"name": filename, "parents": [folder_id]}
    file = drive.files().create(body=metadata, media_body=media, fields="id").execute()
    return file["id"]


def get_or_create_briefing_doc(folder_id: str, name: str) -> str:
    """Return the Google Doc ID for the Daily Briefing, creating it if it doesn't exist."""
    drive = get_drive_service()
    file_id = find_file_in_folder(folder_id, name)
    if file_id:
        return file_id
    metadata = {
        "name": name,
        "parents": [folder_id],
        "mimeType": "application/vnd.google-apps.document",
    }
    file = drive.files().create(body=metadata, fields="id").execute()
    return file["id"]


def prepend_to_doc(doc_id: str, text: str) -> None:
    """Insert text at the top of a Google Doc (newest entry first)."""
    docs = get_docs_service()
    docs.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {
                    "insertText": {
                        "location": {"index": 1},
                        "text": text + "\n\n",
                    }
                }
            ]
        },
    ).execute()


if __name__ == "__main__":
    # Quick auth + resume read test
    from config import MASTER_RESUME_ID
    text = download_docx_text(MASTER_RESUME_ID)
    print("Resume read OK. First 200 chars:")
    print(text[:200])
