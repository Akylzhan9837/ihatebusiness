from io import BytesIO
from uuid import uuid4

from PIL import Image
from pypdf import PdfReader

from app.api.errors import ApiError
from app.models import Document, DocumentKind


MAX_FILE_BYTES = 8 * 1024 * 1024
MAX_PDF_PAGES = 5
MAX_IMAGE_PIXELS = 16_000_000
FORMATS = {
    "PDF": ("application/pdf", "pdf"),
    "JPEG": ("image/jpeg", "jpg"),
    "PNG": ("image/png", "png"),
}


def pdf_pages(content: bytes) -> int:
    reader = PdfReader(BytesIO(content), strict=True)
    if reader.is_encrypted:
        raise ValueError("Encrypted PDF")
    return len(reader.pages)


def check_file(kind: DocumentKind, mime: str | None, content: bytes) -> Document:
    if not content:
        raise ApiError(422, "empty_file", "Choose a non-empty file.")
    if len(content) > MAX_FILE_BYTES:
        raise ApiError(413, "file_too_large", "Choose a file no larger than 8 MiB.")
    if mime not in {media_type for media_type, _ in FORMATS.values()}:
        raise ApiError(415, "unsupported_file", "Upload a PDF, JPG, or PNG.")
    try:
        if content.startswith(b"%PDF-"):
            file_format = "PDF"
            pages = pdf_pages(content)
            if not 1 <= pages <= MAX_PDF_PAGES:
                raise ApiError(422, "pdf_page_limit", "Upload a PDF with 1 to 5 pages.")
        else:
            with Image.open(BytesIO(content), formats=["JPEG", "PNG"]) as image:
                if image.width * image.height > MAX_IMAGE_PIXELS or image.n_frames != 1:
                    raise ApiError(422, "image_size", "Use a single image no larger than 16 megapixels.")
                file_format = image.format
                image.verify()
            with Image.open(BytesIO(content), formats=["JPEG", "PNG"]) as image:
                image.load()
        media_type, extension = FORMATS[file_format]
    except ApiError:
        raise
    except Exception:
        raise ApiError(415, "invalid_file", "This file could not be read as a PDF, JPG, or PNG.") from None
    if mime != media_type:
        raise ApiError(415, "file_type_mismatch", "The uploaded file does not match its declared type.")
    document_id = uuid4()
    return Document(
        document_id=document_id, kind=kind, filename=f"{kind}-{document_id}.{extension}",
        media_type=media_type, size_bytes=len(content),
    )
