import io
from PIL import Image
import streamlit as st

st.set_page_config(
    page_title="Kompresi Gambar Instan", page_icon="🖼️", layout="wide"
)

st.title("🖼️ Kompresi Gambar Instan")
st.write(
    "Kompres gambar secara instan langsung di RAM tanpa simpan file di server."
)

# Upload File
uploaded_file = st.file_uploader(
    "Pilih berkas gambar", type=["jpg", "jpeg", "png", "webp"]
)

if uploaded_file:
  orig_bytes = uploaded_file.size
  orig_kb = round(orig_bytes / 1024, 2)

  # Slider Kualitas (Otomatis memicu re-render saat digeser)
  quality = st.slider(
      "Tingkat Kualitas Kompresi (Quality):",
      min_value=5,
      max_value=100,
      value=50,
      help="Semakin kecil nilainya, semakin kecil ukuran filenya.",
  )

  # Proses Kompresi di RAM via Pillow
  img = Image.open(uploaded_file)
  if img.mode in ("RGBA", "P"):
    img = img.convert("RGB")

  buffer = io.BytesIO()
  img.save(buffer, format="JPEG", quality=quality, optimize=True)
  comp_bytes = buffer.tell()
  comp_kb = round(comp_bytes / 1024, 2)
  savings = round((1 - (comp_bytes / orig_bytes)) * 100, 1)

  # Tampilan Preview 2 Kolom
  col1, col2 = st.columns(2)

  with col1:
    st.subheader("Gambar Asli")
    st.info(f"Ukuran: **{orig_kb} KB**")
    st.image(uploaded_file, use_container_width=True)

  with col2:
    st.subheader("Hasil Kompresi")
    st.success(f"Ukuran: **{comp_kb} KB** (Hemat **{max(0, savings)}%**)")
    buffer.seek(0)
    st.image(buffer, use_container_width=True)

    # Tombol Download
    st.download_button(
        label="⬇️ Unduh Hasil Kompresi",
        data=buffer.getvalue(),
        file_name=f'compressed_q{quality}.jpg',
        mime='image/jpeg',
        use_container_width=True,
        )