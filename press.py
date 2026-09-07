import base64
import io
import os
import shutil
import subprocess
import sys
import tempfile
from PIL import Image
from pypdf import PdfReader, PdfWriter
import streamlit as st

# Konfigurasi Halaman
st.set_page_config(
    page_title="PROJECT GABUT",
    page_icon="face.png" if os.path.exists("face.png") else "🗜️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Fungsi mengubah gambar lokal ke format Base64
def get_image_base64(path):
  if os.path.exists(path):
    with open(path, "rb") as img_file:
      return base64.b64encode(img_file.read()).decode("utf-8")
  return None


# Fungsi membuat gambar thumbnail dari halaman pertama PDF
def get_pdf_first_page_thumb(file_bytes):
  try:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(file_bytes)
    if len(pdf) > 0:
      page = pdf[0]
      return page.render(scale=1.5).to_pil()
  except Exception:
    pass
  return None


# Muat file face.png
face_base64 = get_image_base64("face.png")

# Simpan state menu aktif
if "active_menu" not in st.session_state:
  st.session_state.active_menu = "gambar"

# Injeksi CSS Khusus Kartu Preview ala iLovePDF
st.markdown(
    """
<style>
  /* Styling kartu dokumen PDF */
  .pdf-card {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 12px;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.25);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    margin-bottom: 8px;
    min-height: 230px;
  }
  .pdf-card-thumb {
    max-height: 180px;
    object-fit: contain;
    border-radius: 4px;
    box-shadow: 0 2px 6px rgba(0,0,0,0.15);
  }
  .pdf-filename {
    font-size: 13px;
    font-weight: 700;
    color: #111111;
    text-align: center;
    margin-top: 10px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
  }
  .action-panel {
    background: rgba(255, 255, 255, 0.04);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 24px;
  }
</style>
""",
    unsafe_allow_html=True,
)

# --- SIDEBAR BRANDING & MENU TOMBOL ---
with st.sidebar:
  icon_html = (
      f'<img src="data:image/png;base64,{face_base64}" style="width: 28px;'
      ' height: 28px; object-fit: contain; vertical-align: middle;">'
      if face_base64
      else '<span style="font-size: 22px; color: #e5322d;">❤️</span>'
  )

  st.markdown(
      f"""
    <div style="margin-bottom: 20px;">
      <div style="display: flex; align-items: center; gap: 8px; flex-wrap: nowrap;">
        <span style="font-size: 24px; font-weight: 900; letter-spacing: -0.5px;">PROJECT</span>
        {icon_html}
        <span style="font-size: 24px; font-weight: 900; letter-spacing: -0.5px;">GABUT</span>
      </div>
      <p style="color: gray; font-size: 12px; margin-top: 2px;">Multi-Format Media Tools</p>
    </div>
    """,
      unsafe_allow_html=True,
  )

  st.caption("PILIH TOOLS:")

  is_gambar = st.session_state.active_menu == "gambar"
  if st.button(
      "🖼️  Kompres Gambar",
      use_container_width=True,
      type="primary" if is_gambar else "secondary",
  ):
    st.session_state.active_menu = "gambar"
    st.rerun()

  is_pdf = st.session_state.active_menu == "pdf"
  if st.button(
      "📄  Kompres PDF",
      use_container_width=True,
      type="primary" if is_pdf else "secondary",
  ):
    st.session_state.active_menu = "pdf"
    st.rerun()

  is_merge = st.session_state.active_menu == "merge_pdf"
  if st.button(
      "🧩  Gabung PDF (Merge)",
      use_container_width=True,
      type="primary" if is_merge else "secondary",
  ):
    st.session_state.active_menu = "merge_pdf"
    st.rerun()

  is_word = st.session_state.active_menu == "word2pdf"
  if st.button(
      "📑  Word ke PDF",
      use_container_width=True,
      type="primary" if is_word else "secondary",
  ):
    st.session_state.active_menu = "word2pdf"
    st.rerun()

  st.divider()
  st.markdown(
      "🔒 **100% Aman & Privat**<br>"
      "<small style='color: gray;'>Semua berkas diproses langsung di memori"
      " tanpa disimpan ke server.</small>",
      unsafe_allow_html=True,
  )

  st.markdown(
      """
    <div style="margin-top: 40px; padding-top: 15px; border-top: 1px dashed rgba(255, 255, 255, 0.15); text-align: center;">
      <p style="font-size: 11px; color: #888; margin-bottom: 2px; text-transform: uppercase; letter-spacing: 0.5px;">Project created by</p>
      <p style="font-size: 13px; font-weight: 700; color: #f1f1f1; margin: 0;">Syahbarudin Abdillah</p>
    </div>
    """,
      unsafe_allow_html=True,
  )


# =======================================================
# 1. MODUL: KOMPRES GAMBAR
# =======================================================
if st.session_state.active_menu == "gambar":
  st.title("🖼️ Kompres Gambar")
  st.caption(
      "Kecilkan ukuran berkas JPG, PNG, atau WEBP dengan pratinjau langsung."
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
        help="Semakin kecil nilai slider, semakin kecil ukuran berkas akhirnya.",
    )

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
# 2. MODUL: KOMPRES PDF
# =======================================================
elif st.session_state.active_menu == "pdf":
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
# 3. MODUL: GABUNG PDF (MERGE WORKSPACE ALA ILOVEPDF)
# =======================================================
elif st.session_state.active_menu == "merge_pdf":
  uploaded_pdfs = st.file_uploader(
      "Pilih berkas PDF:",
      type=["pdf"],
      accept_multiple_files=True,
      key="merge_file_uploader",
  )

  if not uploaded_pdfs:
    st.info("Unggah 2 atau lebih berkas PDF untuk mulai menyusun urutan.")
  else:
    current_ids = [f"{f.name}_{f.size}" for f in uploaded_pdfs]

    if (
        "pdf_order_ids" not in st.session_state
        or set(st.session_state.pdf_order_ids) != set(current_ids)
        or len(st.session_state.pdf_order_ids) != len(current_ids)
    ):
      st.session_state.pdf_order_ids = current_ids

    file_map = {f"{f.name}_{f.size}": f for f in uploaded_pdfs}

    # Caching thumbnail halaman pertama agar loading instan saat digeser
    if "pdf_thumbnails" not in st.session_state:
      st.session_state.pdf_thumbnails = {}

    for f_id, f_obj in file_map.items():
      if f_id not in st.session_state.pdf_thumbnails:
        f_obj.seek(0)
        thumb = get_pdf_first_page_thumb(f_obj.getvalue())
        st.session_state.pdf_thumbnails[f_id] = thumb

    st.write("---")

    # Layout ala iLovePDF: Kiri Workspace Kartu, Kanan Action Panel
    col_workspace, col_panel = st.columns([3.2, 1.1], gap="large")

    with col_workspace:
      st.caption(
          "Gunakan tombol **◀** dan **▶** di bawah tiap kartu untuk mengubah"
          " urutan halaman dokumen."
      )

      # Tampilkan kartu-kartu secara horizontal (grid)
      order_ids = st.session_state.pdf_order_ids
      total_files = len(order_ids)

      # Buat kolom grid dinamis (maksimal 4 per baris)
      num_cols = min(total_files, 4)
      cols = st.columns(num_cols)

      for idx, f_id in enumerate(order_ids):
        file_obj = file_map[f_id]
        thumb_img = st.session_state.pdf_thumbnails.get(f_id)
        target_col = cols[idx % num_cols]

        with target_col:
          # Kartu Putih Thumbnail
          with st.container(border=True):
            if thumb_img:
              st.image(thumb_img, use_container_width=True)
            else:
              st.markdown(
                  "<div style='text-align:center; font-size:60px; padding:20px"
                  " 0;'>📄</div>",
                  unsafe_allow_html=True,
              )

            st.markdown(
                f"<div style='text-align:center; font-weight:700; font-size:13px;"
                f" white-space:nowrap; overflow:hidden;"
                f" text-overflow:ellipsis;'>{file_obj.name}</div>",
                unsafe_allow_html=True,
            )

          # Tombol Geser Posisi Urutan
          c_left, c_num, c_right = st.columns([1, 1, 1])
          with c_left:
            if st.button(
                "◀",
                key=f"left_{f_id}_{idx}",
                disabled=(idx == 0),
                use_container_width=True,
            ):
              order_ids[idx], order_ids[idx - 1] = (
                  order_ids[idx - 1],
                  order_ids[idx],
              )
              st.rerun()

          with c_num:
            st.markdown(
                f"<div style='text-align:center; font-weight:bold; color:gray;"
                f" padding-top:6px;'>#{idx + 1}</div>",
                unsafe_allow_html=True,
            )

          with c_right:
            if st.button(
                "▶",
                key=f"right_{f_id}_{idx}",
                disabled=(idx == total_files - 1),
                use_container_width=True,
            ):
              order_ids[idx], order_ids[idx + 1] = (
                  order_ids[idx + 1],
                  order_ids[idx],
              )
              st.rerun()

    # Panel Aksi Kanan (Persis Box Sidebar iLovePDF)
    with col_panel:
      st.markdown("## Merge PDF")
      st.info(
          "ℹ️ Urutan dokumen paling kiri akan diletakkan di halaman pertama"
          " hasil gabungan."
      )

      st.write("")
      if len(uploaded_pdfs) < 2:
        st.warning("Pilih minimal 2 dokumen.")
      else:
        # Tombol Merah Eksekusi
        if st.button(
            "Merge PDF ➔",
            type="primary",
            use_container_width=True,
            key="btn_do_merge",
        ):
          with st.spinner("Menggabungkan seluruh PDF..."):
            try:
              merger = PdfWriter()
              for f_id in order_ids:
                f_obj = file_map[f_id]
                f_obj.seek(0)
                merger.append(f_obj)

              out_buf = io.BytesIO()
              merger.write(out_buf)
              st.session_state.merged_result = out_buf.getvalue()
              st.session_state.compressed_result = None
            except Exception as e:
              st.error(f"Gagal menggabungkan: {e}")

      # Tombol Pasca-Merge (Download & Compress)
      if (
          "merged_result" in st.session_state
          and st.session_state.merged_result
      ):
        m_bytes = st.session_state.merged_result
        m_kb = round(len(m_bytes) / 1024, 2)

        st.success(f"🎉 Siap diunduh! ({m_kb} KB)")

        st.download_button(
            label=f"⬇️ Unduh PDF ({m_kb} KB)",
            data=m_bytes,
            file_name="merged_document.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

        st.write("")
        if st.button("🗜️ Kompres Hasil Ini", use_container_width=True):
          with st.spinner("Memadatkan ukuran file gabungan..."):
            try:
              reader = PdfReader(io.BytesIO(m_bytes))
              compressor = PdfWriter()
              for p in reader.pages:
                p.compress_content_streams()
                compressor.add_page(p)
              compressor.add_metadata({})
              comp_buf = io.BytesIO()
              compressor.write(comp_buf)
              st.session_state.compressed_result = comp_buf.getvalue()
            except Exception as e:
              st.error(f"Gagal kompresi: {e}")

        if (
            "compressed_result" in st.session_state
            and st.session_state.compressed_result
        ):
          c_bytes = st.session_state.compressed_result
          c_kb = round(len(c_bytes) / 1024, 2)
          savings = (
              round((1 - (len(c_bytes) / len(m_bytes))) * 100, 1)
              if len(m_bytes) > 0
              else 0
          )

          st.caption(f"Hemat **{max(0, savings)}%** (Hasil: {c_kb} KB)")
          st.download_button(
              label=f"⬇️ Unduh PDF Terkompresi ({c_kb} KB)",
              data=c_bytes,
              file_name="merged_compressed.pdf",
              mime="application/pdf",
              use_container_width=True,
          )


# =======================================================
# 4. MODUL: UBAH WORD KE PDF (.DOCX ➔ .PDF)
# =======================================================
elif st.session_state.active_menu == "word2pdf":
  st.title("📑 Ubah Dokumen Word ke PDF")
  st.caption(
      "Konversi dokumen Microsoft Word (.docx) menjadi berkas PDF siap cetak"
      " dengan tata letak yang tetap rapi."
  )

  uploaded_docx = st.file_uploader(
      "Unggah Berkas Word (.docx)", type=["docx"], key="word2pdf_uploader"
  )

  if uploaded_docx:
    orig_bytes = uploaded_docx.size
    orig_kb = round(orig_bytes / 1024, 2)

    st.info(f"📁 Dokumen: **{uploaded_docx.name}** | Ukuran: **{orig_kb} KB**")

    if st.button(
        "⚡ Konversi ke PDF Sekarang", type="primary", use_container_width=True
    ):
      with st.spinner("Sedang mengonversi format dokumen ke PDF..."):
        try:
          with tempfile.TemporaryDirectory() as temp_dir:
            input_docx_path = os.path.join(temp_dir, uploaded_docx.name)
            base_name = os.path.splitext(uploaded_docx.name)[0]
            output_pdf_path = os.path.join(temp_dir, f"{base_name}.pdf")

            with open(input_docx_path, "wb") as f:
              f.write(uploaded_docx.getvalue())

            pdf_bytes = None

            libre_cmd = None
            for cmd in ["libreoffice", "soffice"]:
              if shutil.which(cmd):
                libre_cmd = cmd
                break

            if libre_cmd:
              subprocess.run(
                  [
                      libre_cmd,
                      "--headless",
                      "--convert-to",
                      "pdf",
                      input_docx_path,
                      "--outdir",
                      temp_dir,
                  ],
                  check=True,
                  stdout=subprocess.PIPE,
                  stderr=subprocess.PIPE,
              )
              if os.path.exists(output_pdf_path):
                with open(output_pdf_path, "rb") as f:
                  pdf_bytes = f.read()

            elif sys.platform == "win32":
              try:
                import pythoncom
                from docx2pdf import convert

                pythoncom.CoInitialize()
                convert(input_docx_path, output_pdf_path)
                if os.path.exists(output_pdf_path):
                  with open(output_pdf_path, "rb") as f:
                    pdf_bytes = f.read()
              except ImportError:
                st.error(
                    "Di Windows butuh pustaka pendukung. Jalankan: `pip"
                    " install docx2pdf pywin32`"
                )

            if pdf_bytes:
              pdf_kb = round(len(pdf_bytes) / 1024, 2)
              st.success(
                  f"🎉 Berhasil diubah ke PDF! Ukuran berkas hasil:"
                  f" **{pdf_kb} KB**"
              )

              st.download_button(
                  label="⬇️ Unduh Berkas PDF",
                  data=pdf_bytes,
                  file_name=f"{base_name}.pdf",
                  mime="application/pdf",
                  type="primary",
                  use_container_width=True,
              )
            else:
              st.error(
                  "Engine konversi belum siap. Jika di Streamlit Cloud, pastikan"
                  " file `packages.txt` sudah berisi `libreoffice`."
              )

        except Exception as e:
          st.error(f"Gagal melakukan konversi berkas: {e}")
