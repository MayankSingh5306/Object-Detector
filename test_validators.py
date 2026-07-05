# Run with: py -m pytest test_validators.py -v

from validators import (
    has_valid_extension,
    has_valid_magic_bytes,
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_VIDEO_EXTENSIONS,
    IMAGE_SIGNATURES,
    VIDEO_SIGNATURES,
)

# ── has_valid_extension ──────────────────────────────────────

def test_valid_image_extensions():
    assert has_valid_extension("photo.jpg",  ALLOWED_IMAGE_EXTENSIONS) is True
    assert has_valid_extension("photo.jpeg", ALLOWED_IMAGE_EXTENSIONS) is True
    assert has_valid_extension("photo.png",  ALLOWED_IMAGE_EXTENSIONS) is True
    assert has_valid_extension("photo.bmp",  ALLOWED_IMAGE_EXTENSIONS) is True
    assert has_valid_extension("photo.webp", ALLOWED_IMAGE_EXTENSIONS) is True

def test_valid_video_extensions():
    assert has_valid_extension("clip.mp4", ALLOWED_VIDEO_EXTENSIONS) is True
    assert has_valid_extension("clip.avi", ALLOWED_VIDEO_EXTENSIONS) is True
    assert has_valid_extension("clip.mov", ALLOWED_VIDEO_EXTENSIONS) is True
    assert has_valid_extension("clip.mkv", ALLOWED_VIDEO_EXTENSIONS) is True

def test_invalid_extension_rejected():
    assert has_valid_extension("malware.exe", ALLOWED_IMAGE_EXTENSIONS) is False
    assert has_valid_extension("script.js",   ALLOWED_IMAGE_EXTENSIONS) is False
    assert has_valid_extension("data.pdf",    ALLOWED_VIDEO_EXTENSIONS) is False

def test_uppercase_extension_accepted():
    # Extensions should be case-insensitive
    assert has_valid_extension("PHOTO.JPG", ALLOWED_IMAGE_EXTENSIONS) is True
    assert has_valid_extension("CLIP.MP4",  ALLOWED_VIDEO_EXTENSIONS) is True

def test_no_extension_rejected():
    assert has_valid_extension("noextension",  ALLOWED_IMAGE_EXTENSIONS) is False
    assert has_valid_extension("",             ALLOWED_IMAGE_EXTENSIONS) is False

def test_renamed_exe_extension_rejected():
    # A .exe renamed to .jpg should fail extension check if extension is .exe
    assert has_valid_extension("virus.exe", ALLOWED_IMAGE_EXTENSIONS) is False


# ── has_valid_magic_bytes ────────────────────────────────────

def test_valid_jpeg_magic_bytes():
    jpeg_header = b"\xff\xd8\xff" + b"\x00" * 13
    assert has_valid_magic_bytes(jpeg_header, IMAGE_SIGNATURES) is True

def test_valid_png_magic_bytes():
    png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 8
    assert has_valid_magic_bytes(png_header, IMAGE_SIGNATURES) is True

def test_valid_bmp_magic_bytes():
    bmp_header = b"BM" + b"\x00" * 14
    assert has_valid_magic_bytes(bmp_header, IMAGE_SIGNATURES) is True

def test_valid_mp4_magic_bytes():
    # ftyp within first 16 bytes
    mp4_header = b"\x00\x00\x00\x18ftyp" + b"\x00" * 8
    assert has_valid_magic_bytes(mp4_header, VIDEO_SIGNATURES) is True

def test_valid_mkv_magic_bytes():
    mkv_header = b"\x1aE\xdf\xa3" + b"\x00" * 12
    assert has_valid_magic_bytes(mkv_header, VIDEO_SIGNATURES) is True

def test_exe_bytes_rejected_as_image():
    # Windows PE executable starts with MZ
    exe_header = b"MZ" + b"\x00" * 14
    assert has_valid_magic_bytes(exe_header, IMAGE_SIGNATURES) is False

def test_exe_bytes_rejected_as_video():
    exe_header = b"MZ" + b"\x00" * 14
    assert has_valid_magic_bytes(exe_header, VIDEO_SIGNATURES) is False

def test_empty_bytes_rejected():
    assert has_valid_magic_bytes(b"", IMAGE_SIGNATURES) is False
    assert has_valid_magic_bytes(b"", VIDEO_SIGNATURES) is False

def test_random_bytes_rejected():
    garbage = b"\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10"
    assert has_valid_magic_bytes(garbage, IMAGE_SIGNATURES) is False
    assert has_valid_magic_bytes(garbage, VIDEO_SIGNATURES) is False

def test_renamed_exe_fails_magic_check():
    # Core security test: a .exe renamed to .jpg passes extension check
    # but must fail magic byte check
    exe_header = b"MZ" + b"\x00" * 14
    assert has_valid_extension("virus.jpg",   ALLOWED_IMAGE_EXTENSIONS) is True   # passes ext
    assert has_valid_magic_bytes(exe_header, IMAGE_SIGNATURES)           is False  # fails magic
