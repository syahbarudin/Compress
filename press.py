import io
import zipfile
from PIL import Image
from pypdf import PdfReader, PdfWriter
import streamlit as st

# Konfigurasi Halaman (Sidebar ditutup agar fokus ke Top Navbar)
st.set_page_config(
    page_title="PROJECT GABUT",
    page_icon="🗜️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# --- INJEKSI CSS TAMPILAN NAVBAR ALA ILOVEPDF ---
st.markdown(
    """
<style>
  /* Kurangi padding default atas Streamlit */
  .block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 1100px;
  }

  /* Sembunyikan sidebar toggle bawaan jika ada */
  [data-testid="collapsedControl"] {
    display: none;
  }

  /* Hilangkan bulatan radio button agar jadi tombol teks navbar murni */
  div[role="radiogroup"] label > div:first-child {
    display: none !important;
  }

  /* Desain item navigasi */
  div[role="radiogroup"] {
    display: flex !important;
    justify-content: flex-end !important;
    align-items: center !important;
    gap: 20px !important;
  }

  div[role="radiogroup"] label {
    background: transparent !important;
    border: none !important;
    padding: 8px 12px !important;
    font-weight: 700 !important;
    font-size: 14px !important;
    letter-spacing: 0.5px !important;
    text-transform: uppercase !important;
    cursor: pointer !important;
    transition: color 0.2s ease-in-out;
  }

  /* Efek Hover warna merah ala iLovePDF */
  div[role="radiogroup"] label:hover {
    color: #e5322d !important;
  }

  /* Garis pemisah navbar */
  .nav-divider {
    border-bottom: 2px solid rgba(128, 128, 128, 0.2);
    margin-bottom: 30px;
  }
</style>
""",
    unsafe_allow_html=True,
)

# --- TOP NAVBAR HEADER ---
col_logo, col_menu = st.columns([1.2, 2.8], vertical_alignment="center")

with col_logo:
  # Logo Brand ala iLovePDF
  st.markdown(
      """
    <div style="display: flex; align-items: center; gap: 4px; user-select: none;">
      <span style="font-size: 26px; font-weight: 900; letter-spacing: -0.5px;">PROJECT</span>
      <span style="font-size: 24px; color: #e5322d; margin: 0 2px;">❤️</span>
      <span style="font-size: 26px; font-weight: 900; letter-spacing: -0.5px;">GABUT</span>
    </div>
    """,
      unsafe_allow_html=True,
  )

with col_menu:
  menu = st.radio(
      "Navigasi",
      ["KOMPRES GAMBAR", "KOMPRES PDF", "KOMPRES WORD"],
      horizontal=True,
      label_visibility="collapsed",
  )

# Garis batas bawah navbar
st.markdown('<div class="nav-divider"></div>', unsafe_allow_html=True)


# =======================================================
# 1. HALAMAN: KOMPRES GAMBAR
# =======================================================
if menu == "KOMPRES GAMBAR":
  st.markdown(
      "<h2 style='text-align: center; margin-bottom: 5px;'>Kompres Gambar"
      " Instan</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='text-align: center; color: gray; margin-bottom: 25px;'>Kecilkan"
      " ukuran file JPG, PNG, atau WEBP tanpa penurunan kualitas yang"
      " drastis.</p>",
      unsafe_allow_html=True,
  )

  uploaded_image = st.file_uploader(
      "Pilih Berkas Gambar",
      type=["jpg", "jpeg", "png", "webp"],
      label_visibility="collapsed",
  )

  if uploaded_image:
    orig_bytes = uploaded_image.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.write("---")
    quality = st.slider(
        "Tingkat Kualitas Gambar (Quality):",
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

    col1, col2 = st.columns(2)
    with col1:
      st.subheader("Gambar Asli")
      st.caption(f"Ukuran: **{orig_kb} KB**")
      st.image(uploaded_image, use_container_width=True)

    with col2:
      st.subheader("Hasil Kompresi")
      st.caption(f"Ukuran: **{comp_kb} KB** (Hemat **{max(0, savings)}%**)")
      buffer_img.seek(0)
      st.image(buffer_img, use_container_width=True)

      st.download_button(
          label="⬇️ Unduh Gambar",
          data=buffer_img.getvalue(),
          file_name=f"compressed_q{quality}.jpg",
          mime="image/jpeg",
          use_container_width=True,
          type="primary",
      )


# =======================================================
# 2. HALAMAN: KOMPRES PDF
# =======================================================
elif menu == "KOMPRES PDF":
  st.markdown(
      "<h2 style='text-align: center; margin-bottom: 5px;'>Kompres Berkas"
      " PDF</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='text-align: center; color: gray; margin-bottom: 25px;'>Optimasi"
      " aliran teks dan buang metadata sampah dari PDF.</p>",
      unsafe_allow_html=True,
  )

  uploaded_pdf = st.file_uploader(
      "Pilih Berkas PDF", type=["pdf"], label_visibility="collapsed"
  )

  if uploaded_pdf:
    orig_bytes = uploaded_pdf.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.info(f"📁 Berkas: **{uploaded_pdf.name}** | Ukuran Asli: **{orig_kb} KB**")

    if st.button("Mulai Kompresi PDF", type="primary", use_container_width=True):
      with st.spinner("Sedang memadatkan dokumen PDF..."):
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
# 3. HALAMAN: KOMPRES WORD
# =======================================================
elif menu == "KOMPRES WORD":
  st.markdown(
      "<h2 style='text-align: center; margin-bottom: 5px;'>Kompres Dokumen Word"
      " (.docx)</h2>",
      unsafe_allow_html=True,
  )
  st.markdown(
      "<p style='text-align: center; color: gray; margin-bottom: 25px;'>Optimasi"
      " dan perkecil seluruh gambar yang tertanam di dalam dokumen Word.</p>",
      unsafe_allow_html=True,
  )

  uploaded_docx = st.file_uploader(
      "Pilih Berkas DOCX", type=["docx"], label_visibility="collapsed"
  )

  if uploaded_docx:
    orig_bytes = uploaded_docx.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.info(
        f"📁 Berkas: **{uploaded_docx.name}** | Ukuran Asli: **{orig_kb} KB**"
    )

    img_quality = st.slider(
        "Tingkat Kualitas Gambar di Dalam Dokumen:",
        min_value=10,
        max_value=90,
        value=50,
        help="Gambar di dalam dokumen Word akan di-recompress ke kualitas ini.",
    )

    if st.button(
        "Mulai Kompresi Word", type="primary", use_container_width=True
    ):
      with st.spinner("Mengekstrak dan mengompresi gambar internal..."):
        try:
          in_zip = zipfile.ZipFile(uploaded_docx)
          buffer_docx = io.BytesIO()
          out_zip = zipfile.ZipFile(
              buffer_docx, "w", compression=zipfile.ZIP_DEFLATED
          )

          img_count = 0

          for item in in_zip.infolist():
            content = in_zip.read(item.filename)

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
              f"🎉 Berhasil! Sebanyak {img_count} gambar dioptimasi. Ukuran:"
              f" **{orig_kb} KB** ➔ **{comp_kb} KB** (Hemat"
              f" **{max(0, savings)}%**)"
          )

          st.download_button(
              label="⬇️ Unduh File Word Terkompresi",
              data=buffer_docx.getvalue(),
              file_name=f"compressed_{uploaded_docx.name}",
              mime=(
                  "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
              ),
              use_container_width=True,
          )
        except Exception as e:
          st.error(f"Gagal memproses file Word: {e}")
