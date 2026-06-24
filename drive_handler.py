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
    info = json.loads(os.environ["JOB_AGENT_JSON_KEY"])
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


def reset_services() -> None:
    """Clear cached service clients so the next call rebuilds them with a fresh connection."""
    global _drive_service, _docs_service
    _drive_service = None
    _docs_service = None


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


def list_staging_files(folder_id: str, prefix: str) -> list[dict]:
    """Return [{id, name}, ...] for all non-trashed files in folder whose name
    starts with *prefix* and ends with '.txt', sorted by name."""
    drive = get_drive_service()
    q = f"'{folder_id}' in parents and name contains '{prefix}' and trashed = false"
    result = drive.files().list(q=q, fields="files(id, name)").execute()
    files = [
        f for f in result.get("files", [])
        if f["name"].startswith(prefix) and f["name"].endswith(".txt")
    ]
    return sorted(files, key=lambda f: f["name"])


def read_file_by_id(file_id: str) -> str:
    """Download a plain-text file by ID and return its content as a string."""
    drive = get_drive_service()
    request = drive.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue().decode("utf-8")


def delete_file(file_id: str) -> None:
    """Permanently delete a Drive file by ID."""
    drive = get_drive_service()
    drive.files().delete(fileId=file_id).execute()



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


def read_doc_text(doc_id: str) -> str:
    """Return the plain text content of a Google Doc."""
    docs = get_docs_service()
    doc = docs.documents().get(documentId=doc_id).execute()
    parts = []
    for element in doc.get("body", {}).get("content", []):
        if "paragraph" in element:
            for pe in element["paragraph"].get("elements", []):
                if "textRun" in pe:
                    parts.append(pe["textRun"]["content"])
    return "".join(parts)


def overwrite_google_doc(doc_id: str, text: str) -> None:
    """Replace all content in a Google Doc with *text*."""
    docs = get_docs_service()
    doc = docs.documents().get(documentId=doc_id).execute()
    end_index = doc["body"]["content"][-1]["endIndex"]

    requests = []
    # Delete existing body content, preserving the mandatory final paragraph marker.
    if end_index > 2:
        requests.append({
            "deleteContentRange": {
                "range": {"startIndex": 1, "endIndex": end_index - 1}
            }
        })
    if text.strip():
        requests.append({
            "insertText": {
                "location": {"index": 1},
                "text": text,
            }
        })
    if requests:
        docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()


def _build_doc_requests(text: str) -> list[dict]:
    """Convert markdown-hinted text to Docs API batchUpdate requests.

    Handles # Heading, ## Heading, and - / • / * bullets.
    Returns an insertText request followed by paragraph-style requests.
    """
    paragraphs = []
    for line in text.split("\n"):
        s = line.strip()
        if s.startswith("## "):
            paragraphs.append((s[3:] + "\n", "HEADING_2"))
        elif s.startswith("# "):
            paragraphs.append((s[2:] + "\n", "HEADING_1"))
        elif s.startswith(("- ", "• ", "* ")):
            paragraphs.append((s[2:] + "\n", "BULLET"))
        else:
            paragraphs.append(((s + "\n") if s else "\n", "NORMAL_TEXT"))

    full_text = "".join(p[0] for p in paragraphs)
    if not full_text.strip():
        return []

    requests = [{"insertText": {"location": {"index": 1}, "text": full_text}}]

    idx = 1
    for content, style in paragraphs:
        end = idx + len(content)
        if style == "HEADING_1":
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": idx, "endIndex": end},
                    "paragraphStyle": {"namedStyleType": "HEADING_1"},
                    "fields": "namedStyleType",
                }
            })
        elif style == "HEADING_2":
            requests.append({
                "updateParagraphStyle": {
                    "range": {"startIndex": idx, "endIndex": end},
                    "paragraphStyle": {"namedStyleType": "HEADING_2"},
                    "fields": "namedStyleType",
                }
            })
        elif style == "BULLET":
            requests.append({
                "createParagraphBullets": {
                    "range": {"startIndex": idx, "endIndex": end},
                    "bulletPreset": "BULLET_DISC_CIRCLE_SQUARE",
                }
            })
        idx = end

    return requests


def create_google_doc(folder_id: str, name: str, text: str) -> str:
    """Create a new Google Doc in *folder_id*, populate it with formatted *text*, return doc ID."""
    drive = get_drive_service()
    metadata = {
        "name": name,
        "parents": [folder_id],
        "mimeType": "application/vnd.google-apps.document",
    }
    file = drive.files().create(body=metadata, fields="id").execute()
    doc_id = file["id"]
    if text.strip():
        docs = get_docs_service()
        requests = _build_doc_requests(text)
        if requests:
            docs.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()
    return doc_id


if __name__ == "__main__":
    # Quick auth + resume read test
    from config import MASTER_RESUME_ID
    text = download_docx_text(MASTER_RESUME_ID)
    print("Resume read OK. First 200 chars:")
    print(text[:200])
