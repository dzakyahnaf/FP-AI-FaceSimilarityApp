import os
from flask import Flask, request, render_template, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from deepface import DeepFace
import logging

# Konfigurasi logging dasar
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Konfigurasi folder upload
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload size

# Pastikan folder uploads ada
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error_message = None
    img1_path_display = None
    img2_path_display = None

    if request.method == 'POST':
        # Cek apakah file ada di request
        if 'image1' not in request.files or 'image2' not in request.files:
            error_message = "Harap unggah kedua gambar."
            return render_template('index.html', error_message=error_message)

        file1 = request.files['image1']
        file2 = request.files['image2']

        if file1.filename == '' or file2.filename == '':
            error_message = "Harap pilih kedua file gambar."
            return render_template('index.html', error_message=error_message)

        if file1 and allowed_file(file1.filename) and file2 and allowed_file(file2.filename):
            filename1 = secure_filename(file1.filename)
            filename2 = secure_filename(file2.filename)

            # Tambahkan timestamp atau ID unik untuk mencegah penimpaan file dengan nama sama
            # Untuk kesederhanaan, kita gunakan nama file asli, tapi ini bisa jadi masalah
            # jika banyak pengguna mengunggah file dengan nama sama.
            # Solusi lebih baik: timestamp + filename atau UUID.
            # Contoh sederhana:
            # import time
            # unique_filename1 = str(int(time.time())) + "_" + filename1
            # unique_filename2 = str(int(time.time())) + "_2_" + filename2
            # path_img1 = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename1)
            # path_img2 = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename2)


            path_img1 = os.path.join(app.config['UPLOAD_FOLDER'], filename1)
            path_img2 = os.path.join(app.config['UPLOAD_FOLDER'], filename2)

            try:
                file1.save(path_img1)
                file2.save(path_img2)
                logging.info(f"Gambar 1 disimpan di: {path_img1}")
                logging.info(f"Gambar 2 disimpan di: {path_img2}")

                # Path untuk ditampilkan di HTML (relatif terhadap folder uploads)
                img1_path_display = filename1
                img2_path_display = filename2

                # Lakukan verifikasi menggunakan DeepFace
                # Model yang umum digunakan: "VGG-Face", "Facenet", "ArcFace", "DeepID"
                # Detector backend: "opencv", "ssd", "mtcnn", "retinaface"
                # enforce_detection=False agar tidak error jika wajah tidak terdeteksi, tapi hasilnya mungkin tidak akurat
                verification_result = DeepFace.verify(
                    img1_path=path_img1,
                    img2_path=path_img2,
                    model_name="VGG-Face", # Anda bisa ganti model ini
                    detector_backend="mtcnn", # Anda bisa ganti backend ini
                    enforce_detection=False # Ubah ke True jika ingin lebih ketat
                )
                result = verification_result
                logging.info(f"Hasil verifikasi: {result}")

            except Exception as e:
                error_message = f"Terjadi kesalahan saat pemrosesan: {str(e)}"
                logging.error(f"Error: {e}", exc_info=True)
                # Hapus file jika terjadi error agar tidak menumpuk
                if os.path.exists(path_img1): os.remove(path_img1)
                if os.path.exists(path_img2): os.remove(path_img2)
                img1_path_display = None
                img2_path_display = None
        else:
            error_message = "Format file tidak diizinkan. Gunakan PNG, JPG, atau JPEG."

    return render_template('index.html', result=result, error_message=error_message,
                           img1_path_display=img1_path_display, img2_path_display=img2_path_display)

# Route untuk menyajikan file yang diunggah
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    # Hapus port jika menggunakan gunicorn atau server WSGI lain di produksi
    app.run(debug=True, host='0.0.0.0', port=5000)