import base64
import io
import os
import shutil
import subprocess
import sys
import tempfile
from PIL import Image, ImageOps
from pypdf import PdfReader, PdfWriter
import streamlit as st
from streamlit_sortables import sort_items

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="PROJECT GABUT",
    page_icon="face.png" if os.path.exists("face.png") else "🗜️",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --- HELPER FUNCTIONS ---
def get_image_base64(path):
  if os.path.exists(path):
    with open(path, "rb") as img_file:
      return base64.b64encode(img_file.read()).decode("utf-8")
  return None


def get_pdf_first_page_thumb(file_bytes):
  """Membuat gambar thumbnail halaman pertama PDF untuk ruang kerja."""
  try:
    import pypdfium2 as pdfium

    pdf = pdfium.PdfDocument(file_bytes)
    if len(pdf) > 0:
      page = pdf[0]
      return page.render(scale=1.5).to_pil()
  except Exception:
    pass
  return None


def process_image_for_pdf(img, max_dim=1754):
  """Mengkoreksi rotasi EXIF dan meresize gambar proporsional tanpa kanvas/border putih."""
  # 1. Koreksi rotasi otomatis dari sensor HP (EXIF)
  img = ImageOps.exif_transpose(img)
  if img.mode != "RGB":
    img = img.convert("RGB")

  # 2. Resize proporsional jika gambar terlalu besar (mencegah ukuran titan di PDF)
  w, h = img.size
  if max(w, h) > max_dim:
    img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)

  return img


def compress_pdf_engine(pdf_bytes):
  """Mesin kompresi standar untuk PDF berbasis teks/vektor."""
  gs_cmd = None
  for cmd in ["gs", "gswin64c", "gswin32c"]:
    if shutil.which(cmd):
      gs_cmd = cmd
      break

  if gs_cmd:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_in:
      f_in.write(pdf_bytes)
      in_path = f_in.name
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as f_out:
      out_path = f_out.name

    try:
      subprocess.run(
          [
              gs_cmd,
              "-sDEVICE=pdfwrite",
              "-dCompatibilityLevel=1.4",
              "-dPDFSETTINGS=/screen",
              "-dNOPAUSE",
              "-dQUIET",
              "-dBatch",
              f"-sOutputFile={out_path}",
              in_path,
          ],
          check=True,
          timeout=15,
          stdout=subprocess.PIPE,
          stderr=subprocess.PIPE,
      )
      with open(out_path, "rb") as f:
        res_bytes = f.read()
      if len(res_bytes) < len(pdf_bytes):
        return res_bytes
    except Exception:
      pass
    finally:
      if os.path.exists(in_path):
        os.remove(in_path)
      if os.path.exists(out_path):
        os.remove(out_path)

  reader = PdfReader(io.BytesIO(pdf_bytes))
  writer = PdfWriter()

  for page in reader.pages:
    writer.add_page(page)

  for page in writer.pages:
    page.compress_content_streams()

  writer.add_metadata({})
  comp_buf = io.BytesIO()
  writer.write(comp_buf)
  return comp_buf.getvalue()


def compress_image_pdf_engine(pdf_bytes, quality=40, scale=1.2):
  """Mesin kompresi ekstrem khusus PDF hasil scan/convert gambar."""
  import pypdfium2 as pdfium

  pdf = pdfium.PdfDocument(pdf_bytes)
  processed_images = []

  for page in pdf:
    pil_img = page.render(scale=scale).to_pil()
    if pil_img.mode != "RGB":
      pil_img = pil_img.convert("RGB")

    img_buf = io.BytesIO()
    pil_img.save(img_buf, format="JPEG", quality=quality, optimize=True)
    processed_images.append(Image.open(img_buf))

  if not processed_images:
    return pdf_bytes

  out_buf = io.BytesIO()
  processed_images[0].save(
      out_buf,
      format="PDF",
      save_all=True,
      append_images=processed_images[1:],
      resolution=150.0,
  )
  return out_buf.getvalue()


# Muat aset branding
face_base64 = get_image_base64("face.png")

# State menu navigasi
if "active_menu" not in st.session_state:
  st.session_state.active_menu = "gambar"

# --- SIDEBAR NAVIGASI & BRANDING ---
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

  is_pdf2word = st.session_state.active_menu == "pdf2word"
  if st.button(
      "📄➔📑  PDF ke Word",
      use_container_width=True,
      type="primary" if is_pdf2word else "secondary",
  ):
    st.session_state.active_menu = "pdf2word"
    st.rerun()

  is_img2pdf = st.session_state.active_menu == "img2pdf"
  if st.button(
      "🖼️➡️📄  Gambar ke PDF",
      use_container_width=True,
      type="primary" if is_img2pdf else "secondary",
  ):
    st.session_state.active_menu = "img2pdf"
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
    base_name = os.path.splitext(uploaded_image.name)[0]

    st.write("---")
    quality = st.slider(
        "Tingkat Kualitas Kompresi (Quality):",
        min_value=5,
        max_value=100,
        value=50,
        help="Semakin kecil nilai slider, semakin kecil ukuran berkas akhirnya.",
    )

    img = Image.open(uploaded_image)
    img = ImageOps.exif_transpose(img)
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
          file_name=f"{base_name}_compress.jpg",
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
      "Optimalkan aliran teks atau pangkas ukuran PDF hasil scan/convert"
      " gambar."
  )

  uploaded_pdf = st.file_uploader(
      "Unggah Berkas PDF", type=["pdf"], key="pdf_uploader"
  )

  if uploaded_pdf:
    orig_bytes = uploaded_pdf.size
    orig_kb = round(orig_bytes / 1024, 2)
    base_name = os.path.splitext(uploaded_pdf.name)[0]

    st.info(f"📁 Berkas: **{uploaded_pdf.name}** | Ukuran Asli: **{orig_kb} KB**")

    st.write("---")
    mode_pdf = st.radio(
        "Pilih Jenis PDF & Metode Kompresi:",
        [
            "📄 PDF Dokumen Teks / Campuran (Standar)",
            "🖼️ PDF Scan / Hasil Convert Gambar (Ekstrem Ala iLovePDF)",
        ],
        help=(
            "Gunakan mode 'Hasil Convert Gambar' jika PDF kamu isinya foto/scan"
            " agar ukurannya bisa turun drastis."
        ),
    )

    quality_pdf = 40
    scale_pdf = 1.2

    if "Gambar" in mode_pdf:
      col_p1, col_p2 = st.columns(2)
      with col_p1:
        quality_pdf = st.slider(
            "Kualitas Gambar di PDF:",
            min_value=10,
            max_value=80,
            value=40,
            help="Semakin kecil nilai, semakin kecil ukuran file PDF-nya.",
        )
      with col_p2:
        dpi_choice = st.selectbox(
            "Tingkat Kejelasan / Ketajaman:",
            [
                "Sedang / Hemat Ukuran (DPI ~100)",
                "Tinggi / Cukup Jelas (DPI ~135)",
                "Sangat Tinggi (DPI ~180)",
            ],
        )
        if "Sedang" in dpi_choice:
          scale_pdf = 1.2
        elif "Tinggi" in dpi_choice:
          scale_pdf = 1.5
        else:
          scale_pdf = 2.0

    if st.button(
        "⚡ Mulai Kompresi PDF", type="primary", use_container_width=True
    ):
      with st.spinner("Sedang memproses dan mengompresi dokumen PDF..."):
        try:
          if "Gambar" in mode_pdf:
            comp_bytes = compress_image_pdf_engine(
                uploaded_pdf.getvalue(),
                quality=quality_pdf,
                scale=scale_pdf,
            )
          else:
            comp_bytes = compress_pdf_engine(uploaded_pdf.getvalue())

          comp_kb = round(len(comp_bytes) / 1024, 2)
          savings = (
              round((1 - (len(comp_bytes) / orig_bytes)) * 100, 1)
              if orig_bytes > 0
              else 0
          )

          st.success(
              f"🎉 Selesai! Ukuran berkurang dari **{orig_kb} KB** menjadi"
              f" **{comp_kb} KB** (Hemat **{max(0, savings)}%**)"
          )

          st.download_button(
              label="⬇️ Unduh PDF Hasil Kompresi",
              data=comp_bytes,
              file_name=f"{base_name}_compress.pdf",
              mime="application/pdf",
              type="primary",
              use_container_width=True,
          )
        except Exception as e:
          st.error(f"Gagal memproses PDF: {e}")


# =======================================================
# 3. MODUL: GABUNG PDF (MERGE WORKSPACE HYBRID)
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
    file_map = {f.name: f for f in uploaded_pdfs}
    file_names = [f.name for f in uploaded_pdfs]

    if "pdf_thumbnails" not in st.session_state:
      st.session_state.pdf_thumbnails = {}

    for name, f_obj in file_map.items():
      if name not in st.session_state.pdf_thumbnails:
        f_obj.seek(0)
        thumb = get_pdf_first_page_thumb(f_obj.getvalue())
        st.session_state.pdf_thumbnails[name] = thumb

    st.write("---")
    col_workspace, col_panel = st.columns([3.2, 1.1], gap="large")

    with col_workspace:
      st.write("### 🛠️ Atur Urutan Berkas")
      st.caption(
          "Klik, tahan, lalu geser nama berkas di bawah ini untuk mengatur"
          " urutan halaman dokumen:"
      )

      sorted_names = sort_items(file_names, direction="horizontal")

      st.write("")
      st.caption("Pratinjau Hasil Urutan Halaman:")

      num_cols = min(len(sorted_names), 4)
      cols = st.columns(num_cols)

      for idx, name in enumerate(sorted_names):
        thumb_img = st.session_state.pdf_thumbnails.get(name)
        target_col = cols[idx % num_cols]

        with target_col:
          with st.container(border=True):
            if thumb_img:
              st.image(thumb_img, use_container_width=True)
            else:
              st.markdown(
                  "<div style='text-align:center; font-size:50px;'>📄</div>",
                  unsafe_allow_html=True,
              )

            st.markdown(
                f"<div style='text-align:center; font-weight:700; font-size:12px;"
                f" white-space:nowrap; overflow:hidden;"
                f" text-overflow:ellipsis;'>{name}</div>",
                unsafe_allow_html=True,
            )
            st.markdown(
                f"<div style='text-align:center; color:#e5322d; font-size:11px;"
                f" font-weight:bold;'>Urutan #{idx + 1}</div>",
                unsafe_allow_html=True,
            )

    # Panel Eksekusi Gabung
    with col_panel:
      st.markdown("## Merge PDF")
      st.info("ℹ️ Dokumen paling kiri akan menjadi halaman terdepan.")

      st.write("")
      if len(uploaded_pdfs) < 2:
        st.warning("Pilih minimal 2 dokumen.")
      else:
        if st.button(
            "Merge PDF ➔",
            type="primary",
            use_container_width=True,
            key="btn_do_merge",
        ):
          with st.spinner("Menggabungkan seluruh PDF..."):
            try:
              merger = PdfWriter()
              for name in sorted_names:
                f_obj = file_map[name]
                f_obj.seek(0)
                merger.append(f_obj)

              out_buf = io.BytesIO()
              merger.write(out_buf)
              st.session_state.merged_result = out_buf.getvalue()
              st.session_state.compressed_result = None
            except Exception as e:
              st.error(f"Gagal menggabungkan: {e}")

      if (
          "merged_result" in st.session_state
          and st.session_state.merged_result
      ):
        m_bytes = st.session_state.merged_result
        m_kb = round(len(m_bytes) / 1024, 2)
        first_pdf_base = os.path.splitext(sorted_names[0])[0]

        st.success(f"🎉 Dokumen siap! ({m_kb} KB)")

        st.download_button(
            label=f"⬇️ Unduh PDF ({m_kb} KB)",
            data=m_bytes,
            file_name=f"{first_pdf_base}_merge.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )

        st.write("")
        if st.button("🗜️ Kompres Hasil Ini", use_container_width=True):
          with st.spinner("Mengompresi dan merampingkan dokumen gabungan..."):
            try:
              st.session_state.compressed_result = compress_image_pdf_engine(
                  m_bytes, quality=40, scale=1.2
              )
              st.rerun()
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

          st.caption(f"Hemat **{max(0, savings)}%** (Ukuran: {c_kb} KB)")
          st.download_button(
              label=f"⬇️ Unduh PDF Terkompresi ({c_kb} KB)",
              data=c_bytes,
              file_name=f"{first_pdf_base}_merge_compress.pdf",
              mime="application/pdf",
              use_container_width=True,
          )


# =======================================================
# 4. MODUL: UBAH PDF KE WORD (.PDF ➔ .DOCX)
# =======================================================
elif st.session_state.active_menu == "pdf2word":
  st.title("📄➔📑 Ubah Dokumen PDF ke Word")
  st.caption(
      "Konversi berkas PDF menjadi dokumen Microsoft Word (.docx) yang dapat"
      " disunting."
  )

  uploaded_pdf = st.file_uploader(
      "Unggah Berkas PDF", type=["pdf"], key="pdf2word_uploader"
  )

  if uploaded_pdf:
    orig_bytes = uploaded_pdf.size
    orig_kb = round(orig_bytes / 1024, 2)
    base_name = os.path.splitext(uploaded_pdf.name)[0]

    st.info(f"📁 Dokumen: **{uploaded_pdf.name}** | Ukuran: **{orig_kb} KB**")

    if st.button(
        "⚡ Konversi ke Word Sekarang", type="primary", use_container_width=True
    ):
      with st.spinner(
          "Sedang mengonversi tata letak, gambar, dan teks PDF ke Word..."
      ):
        try:
          from pdf2docx import Converter

          with tempfile.TemporaryDirectory() as temp_dir:
            input_pdf_path = os.path.join(temp_dir, uploaded_pdf.name)
            output_docx_path = os.path.join(
                temp_dir, f"{base_name}_pdf2word.docx"
            )

            with open(input_pdf_path, "wb") as f:
              f.write(uploaded_pdf.getvalue())

            cv = Converter(input_pdf_path)
            cv.convert(output_docx_path, start=0, end=None)
            cv.close()

            if os.path.exists(output_docx_path):
              with open(output_docx_path, "rb") as f:
                docx_bytes = f.read()

              docx_kb = round(len(docx_bytes) / 1024, 2)
              st.success(
                  f"🎉 Berhasil diubah ke Word! Ukuran berkas:"
                  f" **{docx_kb} KB**"
              )

              st.download_button(
                  label="⬇️ Unduh Berkas Word (.docx)",
                  data=docx_bytes,
                  file_name=f"{base_name}_pdf2word.docx",
                  mime=(
                      "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  ),
                  type="primary",
                  use_container_width=True,
              )
            else:
              st.error("Gagal membuat berkas Word hasil konversi.")

        except Exception as e:
          st.error(f"Gagal melakukan konversi berkas: {e}")


# =======================================================
# 5. MODUL: UBAH GAMBAR KE PDF (FULL IMAGE TANPA BORDER)
# =======================================================
elif st.session_state.active_menu == "img2pdf":
  st.title("🖼️➡️📄 Ubah Gambar ke PDF")
  st.caption(
      "Gabungkan foto (JPG, PNG, WEBP) menjadi berkas PDF full image tanpa"
      " border/padding putih."
  )

  uploaded_images = st.file_uploader(
      "Unggah Berkas Gambar (Bisa pilih banyak sekaligus):",
      type=["jpg", "jpeg", "png", "webp"],
      accept_multiple_files=True,
      key="img2pdf_uploader",
  )

  if uploaded_images:
    st.info(f"📁 Total gambar diunggah: **{len(uploaded_images)} berkas**")
    first_img_base = os.path.splitext(uploaded_images[0].name)[0]

    num_cols = min(len(uploaded_images), 4)
    cols = st.columns(num_cols)

    for idx, img_file in enumerate(uploaded_images):
      with cols[idx % num_cols]:
        with st.container(border=True):
          st.image(img_file, caption=img_file.name, use_container_width=True)

    st.write("---")
    fit_mode = st.checkbox(
        "Optimalkan skala gambar (Mencegah PDF raksasa & menjaga Full Image"
        " tanpa border)",
        value=True,
    )

    if st.button(
        "⚡ Konversi ke PDF Sekarang", type="primary", use_container_width=True
    ):
      with st.spinner("Sedang memproses dan mengonversi gambar ke PDF..."):
        try:
          img_list = []
          for img_file in uploaded_images:
            raw_img = Image.open(img_file)

            if fit_mode:
              formatted_img = process_image_for_pdf(raw_img)
            else:
              raw_img = ImageOps.exif_transpose(raw_img)
              formatted_img = (
                  raw_img.convert("RGB")
                  if raw_img.mode != "RGB"
                  else raw_img
              )

            img_list.append(formatted_img)

          if img_list:
            buffer_pdf = io.BytesIO()
            img_list[0].save(
                buffer_pdf,
                format="PDF",
                save_all=True,
                append_images=img_list[1:],
                resolution=150.0,
            )
            pdf_bytes = buffer_pdf.getvalue()
            pdf_kb = round(len(pdf_bytes) / 1024, 2)

            st.success(
                f"🎉 Berhasil diubah ke PDF! Ukuran berkas: **{pdf_kb} KB**"
            )

            st.download_button(
                label="⬇️ Unduh Berkas PDF",
                data=pdf_bytes,
                file_name=f"{first_img_base}_img2pdf.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )
        except Exception as e:
          st.error(f"Gagal mengonversi gambar ke PDF: {e}")
            
