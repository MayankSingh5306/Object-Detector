ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}

IMAGE_SIGNATURES = {
    b"\xff\xd8\xff": "jpg",
    b"\x89PNG\r\n\x1a\n": "png",
    b"BM": "bmp",
    b"RIFF": "webp",                 # RIFF....WEBP
}

VIDEO_SIGNATURES = {
    b"\x00\x00\x00\x18ftyp": "mp4",
    b"\x00\x00\x00\x1cftyp": "mp4",
    b"\x00\x00\x00\x20ftyp": "mp4",
    b"RIFF": "avi",                  # RIFF....AVI
    b"\x1aE\xdf\xa3": "mkv",        # EBML header
}


def has_valid_extension(filename: str, allowed: set) -> bool:
    if not filename or "." not in filename:
        return False
    ext = "." + filename.rsplit(".", 1)[1].lower()
    return ext in allowed


def has_valid_magic_bytes(file_bytes: bytes, signatures: dict) -> bool:
    for sig, fmt in signatures.items():
        if sig == b"RIFF":
            # RIFF is a shared container — actual format tag sits at bytes 8-12
            if file_bytes[:4] == b"RIFF" and fmt == "webp" and file_bytes[8:12] == b"WEBP":
                return True
            if file_bytes[:4] == b"RIFF" and fmt == "avi"  and file_bytes[8:12] == b"AVI ":
                return True
            continue
        if file_bytes.startswith(sig):
            return True
    # MP4 can have variable-length headers — check if "ftyp" appears within first 16 bytes
    if b"ftyp" in file_bytes[:16]:
        return True
    return False