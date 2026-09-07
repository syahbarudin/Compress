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


# Fungsi mengubah gambar lokal ke format Base64
def get_image_base64(path):
  if os.path.exists(path):
    with open(path, "rb") as img_file:
      return base64.b64encode(img_file.read()).decode("utf-8")
  return None


# Muat file face.png
face_base64 = get_image_base64("face.png")

st.set_page_config(
    page_title="PROJECT GABUT",
    page_icon="face.png" if os.path.exists("face.png") else "🗜️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Simpan state menu aktif
if "active_menu" not in st.session_state:
  st.session_state.active_menu = "gambar"

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

  # Tombol 1: Kompres Gambar
  is_gambar = st.session_state.active_menu == "gambar"
  if st.button(
      "🖼️  Kompres Gambar",
      use_container_width=True,
      type="primary" if is_gambar else "secondary",
  ):
    st.session_state.active_menu = "gambar"
    st.rerun()

  # Tombol 2: Kompres PDF
  is_pdf = st.session_state.active_menu == "pdf"
  if st.button(
      "📄  Kompres PDF",
      use_container_width=True,
      type="primary" if is_pdf else "secondary",
  ):
    st.session_state.active_menu = "pdf"
    st.rerun()

  # Tombol 3: Gabung PDF (Baru)
  is_merge = st.session_state.active_menu == "merge_pdf"
  if st.button(
      "🧩  Gabung PDF (Merge)",
      use_container_width=True,
      type="primary" if is_merge else "secondary",
  ):
    st.session_state.active_menu = "merge_pdf"
    st.rerun()

  # Tombol 4: Word ke PDF
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

  # Watermark Creator
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
# 3. MODUL: GABUNG PDF (MERGE WORKSPACE)
# =======================================================
elif st.session_state.active_menu == "merge_pdf":
  st.title("🧩 Gabungkan Berkas PDF")
  st.caption(
      "Unggah beberapa dokumen PDF, atur urutan halaman sesuai keinginan pada"
      " workspace, lalu gabungkan."
  )

  uploaded_pdfs = st.file_uploader(
      "Pilih 2 atau lebih berkas PDF:",
      type=["pdf"],
      accept_multiple_files=True,
      key="merge_file_uploader",
  )

  if uploaded_pdfs:
    # Inisialisasi atau sinkronisasi urutan indeks file
    current_ids = [f"{f.name}_{f.size}" for f in uploaded_pdfs]

    if (
        "pdf_order_ids" not in st.session_state
        or set(st.session_state.pdf_order_ids) != set(current_ids)
        or len(st.session_state.pdf_order_ids) != len(current_ids)
    ):
      st.session_state.pdf_order_ids = current_ids

    file_map = {f"{f.name}_{f.size}": f for f in uploaded_pdfs}

    st.write("---")
    st.subheader("🛠️ Ruang Kerja (Atur Urutan Dokumen)")
    st.caption("Urutan teratas akan menjadi halaman paling depan pada PDF gabungan.")

    # Tampilkan kartu urutan file dengan tombol geser
    for idx, f_id in enumerate(st.session_state.pdf_order_ids):
      file_obj = file_map[f_id]
      size_kb = round(file_obj.size / 1024, 1)

      col_info, col_up, col_down = st.columns([5, 1, 1], vertical_alignment="center")

      with col_info:
        st.markdown(
            f"""
            <div style="background-color: rgba(255, 255, 255, 0.05); padding: 10px 15px; border-radius: 6px; border: 1px solid rgba(255, 255, 255, 0.1);">
                <b>#{idx + 1}</b> 📄 {file_obj.name} <span style="color: gray; font-size: 12px; margin-left: 10px;">({size_kb} KB)</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

      with col_up:
        if st.button("⬆️ Naik", key=f"up_{f_id}", disabled=(idx == 0), use_container_width=True):
          order = st.session_state.pdf_order_ids
          order[idx], order[idx - 1] = order[idx - 1], order[idx]
          st.rerun()

      with col_down:
        if st.button(
            "⬇️ Turun",
            key=f"down_{f_id}",
            disabled=(idx == len(st.session_state.pdf_order_ids) - 1),
            use_container_width=True,
        ):
          order = st.session_state.pdf_order_ids
          order[idx], order[idx + 1] = order[idx + 1], order[idx]
          st.rerun()

    st.write("")

    # Tombol Eksekusi Penggabungan
    if len(uploaded_pdfs) < 2:
      st.info("💡 Unggah minimal 2 berkas PDF untuk mengaktifkan tombol gabung.")
    else:
      if st.button("⚡ Gabungkan PDF Sekarang", type="primary", use_container_width=True):
        with st.spinner("Menggabungkan seluruh dokumen sesuai urutan..."):
          try:
            merger = PdfWriter()
            total_orig_bytes = 0

            for f_id in st.session_state.pdf_order_ids:
              file_obj = file_map[f_id]
              total_orig_bytes += file_obj.size
              file_obj.seek(0)
              merger.append(file_obj)

            merged_buffer = io.BytesIO()
            merger.write(merged_buffer)
            st.session_state.merged_result = merged_buffer.getvalue()
            st.session_state.merged_orig_size = total_orig_bytes
            st.session_state.compressed_result = None  # Reset kompresi jika ada merge baru

          except Exception as e:
            st.error(f"Gagal menggabungkan PDF: {e}")

    # Area Hasil & Pilihan Tindakan (Download vs Compress)
    if "merged_result" in st.session_state and st.session_state.merged_result:
      merged_bytes = st.session_state.merged_result
      merged_kb = round(len(merged_bytes) / 1024, 2)

      st.success(f"🎉 Dokumen berhasil digabungkan! Ukuran total: **{merged_kb} KB**")
      st.write("### Pilih Langkah Selanjutnya:")

      col_act1, col_act2 = st.columns(2)

      with col_act1:
        st.download_button(
            label=f"⬇️ Unduh PDF Gabungan ({merged_kb} KB)",
            data=merged_bytes,
            file_name="merged_document.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

      with col_act2:
        if st.button("🗜️ Kompres Hasil Gabungan", use_container_width=True):
          with st.spinner("Sedang memadatkan hasil PDF gabungan..."):
            try:
              reader = PdfReader(io.BytesIO(merged_bytes))
              compressor = PdfWriter()

              for page in reader.pages:
                page.compress_content_streams()
                compressor.add_page(page)

              compressor.add_metadata({})
              comp_buffer = io.BytesIO()
              compressor.write(comp_buffer)
              st.session_state.compressed_result = comp_buffer.getvalue()

            except Exception as e:
              st.error(f"Gagal mengompresi hasil PDF: {e}")

      # Tampilkan tombol download kompresi jika sudah diproses
      if (
          "compressed_result" in st.session_state
          and st.session_state.compressed_result
      ):
        comp_bytes = st.session_state.compressed_result
        comp_kb = round(len(comp_bytes) / 1024, 2)
        savings = (
            round((1 - (len(comp_bytes) / len(merged_bytes))) * 100, 1)
            if len(merged_bytes) > 0
            else 0
        )

        st.info(
            f"📦 Kompresi tuntas! Ukuran hemat **{max(0, savings)}%** (dari"
            f" {merged_kb} KB ➔ **{comp_kb} KB**)"
        )
        st.download_button(
            label=f"⬇️ Unduh PDF Terkompresi ({comp_kb} KB)",
            data=comp_bytes,
            file_name="merged_compressed_document.pdf",
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
                    "Di Windows lokal butuh pustaka pendukung. Jalankan di"
                    " terminal: `pip install docx2pdf pywin32`"
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
