"""Create a minimal valid PDF with text content for testing."""
import struct, zlib

def make_pdf(text: str, out_path: str):
    # Build a minimal PDF with one text page
    content_stream = f"BT /F1 12 Tf 72 720 Td ({text}) Tj ET"
    content_bytes = content_stream.encode()

    xref = []
    body = []

    def add_obj(data: str):
        xref.append(len(b"".join(body)))
        body.append(data.encode())

    add_obj("")  # obj 0 placeholder (not used)

    add_obj("1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
    add_obj("2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n")
    add_obj(
        f"3 0 obj\n<< /Type /Page /Parent 2 0 R "
        f"/MediaBox [0 0 612 792] "
        f"/Contents 4 0 R "
        f"/Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n"
    )
    add_obj(
        f"4 0 obj\n<< /Length {len(content_bytes)} >>\nstream\n"
        + content_stream
        + "\nendstream\nendobj\n"
    )
    add_obj(
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
    )

    # header
    header = b"%PDF-1.4\n"
    # build body bytes with proper offsets
    body_bytes = b""
    offsets = [len(header)]
    for i, chunk in enumerate(body[1:], start=1):
        actual = f"{i} 0 obj\n".encode() if not chunk.startswith(f"{i} 0 obj".encode()) else b""
        body_bytes += chunk
        if i + 1 < len(body):
            offsets.append(len(header) + len(body_bytes))

    # Simple approach: just write objects sequentially with correct byte offsets
    out = bytearray()
    out += b"%PDF-1.4\n"

    offsets_real = {}
    # obj 1..5
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
         b"/Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>"),
        None,  # stream object, handle separately
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]

    for i, obj in enumerate(objs, start=1):
        offsets_real[i] = len(out)
        if i == 4:
            out += f"4 0 obj\n<< /Length {len(content_bytes)} >>\nstream\n".encode()
            out += content_bytes
            out += b"\nendstream\nendobj\n"
        else:
            out += f"{i} 0 obj\n".encode()
            out += obj
            out += b"\nendobj\n"

    xref_start = len(out)
    out += b"xref\n"
    out += f"0 6\n".encode()
    out += b"0000000000 65535 f \n"
    for i in range(1, 6):
        out += f"{offsets_real[i]:010d} 00000 n \n".encode()
    out += b"trailer\n<< /Size 6 /Root 1 0 R >>\n"
    out += f"startxref\n{xref_start}\n%%EOF\n".encode()

    with open(out_path, "wb") as f:
        f.write(bytes(out))
    print(f"Written {len(out)} bytes to {out_path}")


make_pdf("Company annual revenue was 10M in 2024", "test_revenue.pdf")
