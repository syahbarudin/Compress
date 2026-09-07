import io
import zipfile
from PIL import Image
from pypdf import PdfReader, PdfWriter
import streamlit as st

st.set_page_config(
    page_title="Multi-Compressor Studio", page_icon="🗜️", layout="wide"
)

# --- SIDEBAR NAVIGASI ---
with st.sidebar:
  st.title("🗜️ Multi-Compressor")
  st.caption("Aplikasi kompresi serbaguna berbasis Python di RAM.")

  menu = st.radio(
      "Pilih Kategori Dokumen:",
      [
          "🖼️ Kompres Gambar",
          "📄 Kompres PDF",
          "📝 Kompres Dokumen Word (.docx)",
      ],
  )

  st.divider()
  st.info("💡 **Privasi Terjaga:** Berkas tidak pernah disimpan ke server/disk.")


# ==========================================
# 1. MENU: KOMPRES GAMBAR
# ==========================================
if menu == "🖼️ Kompres Gambar":
  st.header("🖼️ Kompres Gambar Instan")
  st.write("Dukung format JPG, PNG, dan WebP dengan tinjauan langsung.")

  uploaded_image = st.file_uploader(
      "Unggah Gambar",
      type=["jpg", "jpeg", "png", "webp"],
      key="img_uploader",
  )

  if uploaded_image:
    orig_bytes = uploaded_image.size
    orig_kb = round(orig_bytes / 1024, 2)

    quality = st.slider(
        "Tingkat Kualitas Kompresi (Quality):",
        min_value=5,
        max_value=100,
        value=50,
        help="Semakin kecil nilai, semakin kecil ukuran file hasil kompresi.",
    )

    # Proses kompresi di RAM
    img = Image.open(uploaded_image)
    if img.mode in ("RGBA", "P"):
      img = img.convert("RGB")

    buffer_img = io.BytesIO()
    img.save(buffer_img, format="JPEG", quality=quality, optimize=True)
    comp_bytes = buffer_img.tell()
    comp_kb = round(comp_bytes / 1024, 2)
    savings = (
        round((1 - (comp_bytes / orig_bytes)) * 100, 1)
        if orig_bytes > 0
        else 0
    )

    # Preview 2 Kolom
    col1, col2 = st.columns(2)
    with col1:
      st.subheader("Gambar Asli")
      st.info(f"Ukuran: **{orig_kb} KB**")
      st.image(uploaded_image, use_container_width=True)

    with col2:
      st.subheader("Hasil Kompresi")
      st.success(f"Ukuran: **{comp_kb} KB** (Hemat **{max(0, savings)}%**)")
      buffer_img.seek(0)
      st.image(buffer_img, use_container_width=True)

      st.download_button(
          label="⬇️ Unduh Gambar Terkompresi",
          data=buffer_img.getvalue(),
          file_name=f"compressed_q{quality}.jpg",
          mime="image/jpeg",
          use_container_width=True,
      )


# ==========================================
# 2. MENU: KOMPRES PDF
# ==========================================
elif menu == "📄 Kompres PDF":
  st.header("📄 Kompres Berkas PDF")
  st.write(
      "Mengompresi aliran teks, menghapus metadata berlebih, dan merapikan"
      " struktur PDF."
  )

  uploaded_pdf = st.file_uploader(
      "Unggah Berkas PDF", type=["pdf"], key="pdf_uploader"
  )

  if uploaded_pdf:
    orig_bytes = uploaded_pdf.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.write(f"Ukuran Asli: **{orig_kb} KB**")

    if st.button("Mulai Kompresi PDF", type="primary"):
      with st.spinner("Sedang memproses PDF..."):
        try:
          reader = PdfReader(uploaded_pdf)
          writer = PdfWriter()

          # Kompresi setiap halaman
          for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

          # Hapus metadata identitas & objek duplikat
          writer.add_metadata({})

          buffer_pdf = io.BytesIO()
          writer.write(buffer_pdf)
          comp_bytes = buffer_pdf.tell()
          comp_kb = round(comp_bytes / 1024, 2)
          savings = (
              round((1 - (comp_bytes / orig_bytes)) * 100, 1)
              if orig_bytes > 0
              else 0
          )

          st.success(
              f"Selesai! Ukuran berkurang dari **{orig_kb} KB** menjadi"
              f" **{comp_kb} KB** (Hemat **{max(0, savings)}%**)"
          )

          st.download_button(
              label="⬇️ Unduh PDF Hasil Kompresi",
              data=buffer_pdf.getvalue(),
              file_name=f"compressed_{uploaded_pdf.name}",
              mime="application/pdf",
              use_container_width=True,
          )
        except Exception as e:
          st.error(f"Gagal memproses PDF: {e}")


# ==========================================
# 3. MENU: KOMPRES WORD (.DOCX)
# ==========================================
elif menu == "📝 Kompres Dokumen Word (.docx)":
  st.header("📝 Kompres Dokumen Word (.docx)")
  st.write(
      "Membongkar arsip DOCX, mengompresi semua foto/gambar di dalamnya via"
      " Pillow, lalu membungkusnya kembali."
  )

  uploaded_docx = st.file_uploader(
      "Unggah Berkas Word (.docx)", type=["docx"], key="docx_uploader"
  )

  if uploaded_docx:
    orig_bytes = uploaded_docx.size
    orig_kb = round(orig_bytes / 1024, 2)
    st.write(f"Ukuran Asli: **{orig_kb} KB**")

    img_quality = st.slider(
        "Kualitas Gambar di dalam Dokumen:",
        min_value=10,
        max_value=90,
        value=50,
        help="Gambar di dalam dokumen Word akan di-recompress ke kualitas ini.",
    )

    if st.button("Mulai Kompresi Word", type="primary"):
      with st.spinner("Sedang mengekstrak dan mengompresi isi dokumen..."):
        try:
          in_zip = zipfile.ZipFile(uploaded_docx)
          buffer_docx = io.BytesIO()
          out_zip = zipfile.ZipFile(
              buffer_docx, "w", compression=zipfile.ZIP_DEFLATED
          )

          total_images_compressed = 0

          # Telusuri semua file di dalam .docx
          for item in in_zip.infolist():
            content = in_zip.read(item.filename)

            # Jika file ada di folder media Word dan berupa gambar
            if item.filename.startswith("word/media/"):
              try:
                img = Image.open(io.BytesIO(content))
                img_buf = io.BytesIO()

                # Recompress jika JPEG / PNG
                if item.filename.lower().endswith((".jpg", ".jpeg")):
                  if img.mode != "RGB":
                    img = img.convert("RGB")
                  img.save(
                      img_buf, format="JPEG", quality=img_quality, optimize=True
                  )
                  if len(img_buf.getvalue()) < len(content):
                    content = img_buf.getvalue()
                    total_images_compressed += 1

                elif item.filename.lower().endswith(".png"):
                  img.save(img_buf, format="PNG", optimize=True)
                  if len(img_buf.getvalue()) < len(content):
                    content = img_buf.getvalue()
                    total_images_compressed += 1
              except Exception:
                pass  # Lewati jika bukan format gambar standar

            # Tulis ulang file ke arsip baru
            out_zip.writestr(item, content)

          out_zip.close()
          comp_bytes = buffer_docx.tell()
          comp_kb = round(comp_bytes / 1024, 2)
          savings = (
              round((1 - (comp_bytes / orig_bytes)) * 100, 1)
              if orig_bytes > 0
              else 0
          )

          st.success(
              f"Berhasil! {total_images_compressed} gambar dioptimasi. Ukuran:"
              f" **{orig_kb} KB** ➔ **{comp_kb} KB** (Hemat"
              f" **{max(0, savings)}%**)"
          )

          st.download_button(
              label="⬇️ Unduh Word (.docx) Terkompresi",
              data=buffer_docx.getvalue(),
              file_name=f"compressed_{uploaded_docx.name}",
              mime=(
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              ),
              use_container_width=True,
          )
        except Exception as e:
          st.error(f"Gagal memproses Word: {e}")
