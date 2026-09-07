import io
import zipfile
from PIL import Image
from pypdf import PdfReader, PdfWriter
import streamlit as st

# Konfigurasi Halaman
st.set_page_config(
    page_title="PROJECT GABUT",
    page_icon="🗜️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- SIDEBAR BRANDING & NAVIGASI ---
with st.sidebar:
  # Logo Brand ala iLovePDF
  st.markdown(
      """
    <div style="margin-bottom: 20px;">
      <span style="font-size: 26px; font-weight: 900; letter-spacing: -0.5px;">PROJECT</span>
      <span style="font-size: 24px; color: #e5322d; margin: 0 2px;">❤️</span>
      <span style="font-size: 26px; font-weight: 900; letter-spacing: -0.5px;">GABUT</span>
      <p style="color: gray; font-size: 12px; margin-top: 2px;">Multi-Format Compression Tools</p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  menu = st.radio(
      "PILIH TOOLS:",
      [
          "🖼️ Kompres Gambar",
          "📄 Kompres PDF",
          "📝 Kompres Dokumen Word",
      ],
  )

  st.divider()
  st.markdown(
      "🔒 **100% Aman & Privat**<br>"
      "<small style='color: gray;'>Semua berkas diproses langsung di RAM tanpa disimpan ke harddisk server.</small>",
      unsafe_allow_html=True,
  )


# =======================================================
# 1. MENU: KOMPRES GAMBAR
# =======================================================
if menu == "🖼️ Kompres Gambar":
  st.title("🖼️ Kompres Gambar")
  st.caption(
      "Kecilkan ukuran file JPG, PNG, atau WEBP dengan pratinjau langsung."
  )

  uploaded_image = st.file_uploader(
      "Unggah Gambar",
      type=["jpg", "jpeg", "png", "webp"],
      key="img_uploader",
  )

  if uploaded_image:
    orig_bytes = uploaded_image.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.write("---")
    quality = st.slider(
        "Tingkat Kualitas Kompresi (Quality):",
        min_value=5,
        max_value=100,
        value=50,
        help="Semakin kecil nilai slider, semakin kecil ukuran file akhirnya.",
    )

    # Proses kompresi gambar di RAM
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

    # Preview Komparasi 2 Kolom
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
          label="⬇️ Unduh Gambar Hasil Kompresi",
          data=buffer_img.getvalue(),
          file_name=f"compressed_q{quality}.jpg",
          mime="image/jpeg",
          type="primary",
          use_container_width=True,
      )


# =======================================================
# 2. MENU: KOMPRES PDF
# =======================================================
elif menu == "📄 Kompres PDF":
  st.title("📄 Kompres Berkas PDF")
  st.caption(
      "Optimalkan aliran teks, bersihkan metadata berlebih, dan ringkas"
      " struktur internal PDF."
  )

  uploaded_pdf = st.file_uploader(
      "Unggah Berkas PDF", type=["pdf"], key="pdf_uploader"
  )

  if uploaded_pdf:
    orig_bytes = uploaded_pdf.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.info(f"📁 Berkas: **{uploaded_pdf.name}** | Ukuran Asli: **{orig_kb} KB**")

    if st.button(
        "⚡ Mulai Kompresi PDF", type="primary", use_container_width=True
    ):
      with st.spinner("Sedang memproses dokumen PDF..."):
        try:
          reader = PdfReader(uploaded_pdf)
          writer = PdfWriter()

          for page in reader.pages:
            page.compress_content_streams()
            writer.add_page(page)

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
              f"🎉 Selesai! Ukuran berkurang dari **{orig_kb} KB** menjadi"
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


# =======================================================
# 3. MENU: KOMPRES DOKUMEN WORD (.DOCX)
# =======================================================
elif menu == "📝 Kompres Dokumen Word":
  st.title("📝 Kompres Dokumen Word (.docx)")
  st.caption(
      "Mengekstrak file Word, mengompresi gambar internal yang bikin ukuran"
      " dokumen bengkak, lalu mengemasnya kembali."
  )

  uploaded_docx = st.file_uploader(
      "Unggah Berkas Word (.docx)", type=["docx"], key="docx_uploader"
  )

  if uploaded_docx:
    orig_bytes = uploaded_docx.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.info(
        f"📁 Berkas: **{uploaded_docx.name}** | Ukuran Asli: **{orig_kb} KB**"
    )

    img_quality = st.slider(
        "Kualitas Gambar di Dalam Dokumen Word:",
        min_value=10,
        max_value=90,
        value=50,
        help="Gambar/foto di dalam Word akan dikompresi ke kualitas ini.",
    )

    if st.button(
        "⚡ Mulai Kompresi Word", type="primary", use_container_width=True
    ):
      with st.spinner("Sedang mengoptimasi isi dokumen..."):
        try:
          in_zip = zipfile.ZipFile(uploaded_docx)
          buffer_docx = io.BytesIO()
          out_zip = zipfile.ZipFile(
              buffer_docx, "w", compression=zipfile.ZIP_DEFLATED
          )

          img_count = 0

          for item in in_zip.infolist():
            content = in_zip.read(item.filename)

            # Jika target adalah gambar di dalam Word
            if item.filename.startswith("word/media/"):
              try:
                img = Image.open(io.BytesIO(content))
                img_buf = io.BytesIO()

                if item.filename.lower().endswith((".jpg", ".jpeg")):
                  if img.mode != "RGB":
                    img = img.convert("RGB")
                  img.save(
                      img_buf, format="JPEG", quality=img_quality, optimize=True
                  )
                  if len(img_buf.getvalue()) < len(content):
                    content = img_buf.getvalue()
                    img_count += 1

                elif item.filename.lower().endswith(".png"):
                  img.save(img_buf, format="PNG", optimize=True)
                  if len(img_buf.getvalue()) < len(content):
                    content = img_buf.getvalue()
                    img_count += 1
              except Exception:
                pass

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
              f"🎉 Berhasil! Sebanyak {img_count} gambar di dalam dokumen"
              f" dioptimalkan. Ukuran: **{orig_kb} KB** ➔ **{comp_kb} KB**"
              f" (Hemat **{max(0, savings)}%**)"
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
          st.error(f"Gagal memproses dokumen Word: {e}")
