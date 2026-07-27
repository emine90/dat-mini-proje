import os
import random
import time
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)

# Doğrudan sabitlenen Supabase Bağlantı Adresi (Şifre URL-encoded hallidir)
POSTGRES_URI = "postgresql://postgres.bvdywitsulunkyjdmclg:EM%C4%B0NE1234.%3Fi@aws-1-ap-northeast-2.pooler.supabase.com:5432/postgres"

# 🚀 Bağlantı Havuzu (Connection Pool)
try:
    db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, POSTGRES_URI)
    print("Veritabanı bağlantı havuzu başarıyla oluşturuldu.")
except Exception as e:
    print(f"Havuz oluşturulurken hata: {e}")
    db_pool = None

def get_db_connection():
    global db_pool
    max_retries = 3
    for attempt in range(max_retries):
        try:
            if db_pool is None or db_pool.closed:
                db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, POSTGRES_URI)
            
            if db_pool:
                conn = db_pool.getconn()
                if conn:
                    with conn.cursor() as cur:
                        cur.execute("SELECT 1;")
                    return conn
        except Exception as e:
            print(f"Bağlantı denemesi {attempt + 1} başarısız: {e}")
            time.sleep(0.5)
            try:
                db_pool = psycopg2.pool.SimpleConnectionPool(1, 10, POSTGRES_URI)
            except:
                pass
    
    return psycopg2.connect(POSTGRES_URI, cursor_factory=RealDictCursor)

def release_db_connection(conn):
    if db_pool and not db_pool.closed and conn:
        try:
            db_pool.putconn(conn)
        except:
            conn.close()
    elif conn:
        conn.close()

# KODUN GERİ KALANI (CAR_BRANDS, HTML_TEMPLATE ve @app.route fonksiyonları) AYNEN KALACAK...
CAR_BRANDS = sorted([
    "Alfa Romeo", "Audi", "BMW", "Chery", "Chevrolet", "Citroen", "Dacia", "Fiat", 
    "Ford", "Honda", "Hyundai", "Isuzu", "Jaguar", "Jeep", "Kia", "Lada", 
    "Land Rover", "Lexus", "Maserati", "Mazda", "Mercedes-Benz", "Mini", "Mitsubishi", 
    "Nissan", "Opel", "Peugeot", "Porsche", "Renault", "Seat", "Skoda", "Subaru", 
    "Suzuki", "Tesla", "Tofaş", "Toyota", "TOGG", "Volkswagen", "Volvo"
])

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>DAT.NET Mini Ekspertiz Portalı</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { background-color: #f8f9fa; }
        .card { border-radius: 10px; border: none; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .vin-input { font-family: monospace; letter-spacing: 2px; font-weight: bold; text-transform: uppercase; }
    </style>
</head>
<body>
<nav class="navbar navbar-dark bg-dark mb-4">
    <div class="container">
        <a class="navbar-brand fw-bold" href="/"><i class="bi bi-car-front-fill text-warning me-2"></i>DAT.NET / Oto-Ekspertiz Portalı</a>
        <span class="badge bg-success"><i class="bi bi-lightning-charge-fill me-1"></i>Hızlı Bağlantı Aktif</span>
    </div>
</nav>

<div class="container">
    {% if error_message %}
    <div class="alert alert-danger alert-dismissible fade show mb-4 shadow-sm" role="alert">
        <i class="bi bi-exclamation-triangle-fill me-2"></i><strong>Hata:</strong> {{ error_message }}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    </div>
    {% endif %}

    <div class="row">
        <!-- SOL: VIN Sorgu ve Dosya Ekleme -->
        <div class="col-md-5 mb-4">
            <div class="card mb-4">
                <div class="card-header bg-secondary text-white fw-bold"><i class="bi bi-search me-2"></i>VIN / Şasi Detay Sorgula</div>
                <div class="card-body">
                    <form action="/query-vin" method="POST" class="d-flex gap-2">
                        <input type="text" name="vin" id="search_vin" class="form-control vin-input" placeholder="_________________" required>
                        <button type="submit" class="btn btn-dark">Sorgula</button>
                    </form>
                    {% if queried_vehicle %}
                    <div class="alert alert-info mt-3 mb-0">
                        <strong>Marka/Model:</strong> {{ queried_vehicle.brand }} {{ queried_vehicle.model }} ({{ queried_vehicle.model_year }})<br>
                        <strong>Motor:</strong> {{ queried_vehicle.engine }}<br>
                        <strong>Şasi:</strong> <code>{{ queried_vehicle.vin }}</code>
                    </div>
                    {% endif %}
                </div>
            </div>

            <div class="card">
                <div class="card-header bg-primary text-white fw-bold"><i class="bi bi-plus-circle me-2"></i>Yeni Hasar Dosyası Aç</div>
                <div class="card-body">
                    <form action="/create-dossier" method="POST">
                        <div class="mb-3">
                            <label class="form-label fw-bold">Araç Şasi No (VIN) <span class="text-danger">* (17 Hane)</span></label>
                            <input type="text" name="vin" id="create_vin" class="form-control vin-input" placeholder="_________________" required>
                        </div>

                        <div class="row mb-3">
                            <div class="col">
                                <label class="form-label fw-bold">Marka</label>
                                <input type="text" name="brand" list="brands_list" class="form-control" placeholder="Seçin veya Yazın..." required autocomplete="off">
                                <datalist id="brands_list">
                                    {% for brand in car_brands %}
                                    <option value="{{ brand }}"></option>
                                    {% endfor %}
                                </datalist>
                            </div>
                            <div class="col">
                                <label class="form-label fw-bold">Model</label>
                                <input type="text" name="model" class="form-control" placeholder="Örn: Corolla / 320i" required>
                            </div>
                        </div>

                        <div class="mb-3">
                            <label class="form-label fw-bold">Müşteri Adı Soyadı</label>
                            <input type="text" name="customer_name" class="form-control" placeholder="Örn: Ahmet Yılmaz" required>
                        </div>
                        <div class="row mb-3">
                            <div class="col">
                                <label class="form-label">Parça Maliyeti (₺)</label>
                                <input type="number" step="0.01" name="parts_cost" class="form-control" value="0.00">
                            </div>
                            <div class="col">
                                <label class="form-label">İşçilik (₺)</label>
                                <input type="number" step="0.01" name="labor_cost" class="form-control" value="0.00">
                            </div>
                        </div>
                        <button type="submit" class="btn btn-primary w-100 fw-bold">Dosyayı Veritabanına Kaydet</button>
                    </form>
                </div>
            </div>
        </div>

        <!-- SAĞ: Kayıtlı Dosyalar Listesi & Arama -->
        <div class="col-md-7">
            <div class="card">
                <div class="card-header bg-dark text-white d-flex justify-content-between align-items-center fw-bold">
                    <span><i class="bi bi-folder2-open me-2"></i>Ekspertiz Dosyaları</span>
                    {% if search_keyword %}
                    <span class="badge bg-warning text-dark">Arama: "{{ search_keyword }}"</span>
                    {% endif %}
                </div>
                
                <div class="p-3 bg-light border-bottom">
                    <form action="/search-dossier" method="POST" class="d-flex gap-2">
                        <input type="text" name="keyword" class="form-control" placeholder="İsim Soyisim veya Şasi No ile Ara..." value="{{ search_keyword or '' }}">
                        <button type="submit" class="btn btn-outline-dark"><i class="bi bi-search"></i> Ara</button>
                        {% if search_keyword %}
                        <a href="/" class="btn btn-outline-secondary">Temizle</a>
                        {% endif %}
                    </form>
                </div>

                <div class="card-body p-0">
                    <div class="table-responsive">
                        <table class="table table-hover align-middle mb-0">
                            <thead>
                                <tr>
                                    <th>Kod</th>
                                    <th>Şasi / Araç</th>
                                    <th>Müşteri</th>
                                    <th>Toplam</th>
                                    <th>Durum</th>
                                    <th class="text-end">İşlem</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% if not dossiers %}
                                <tr>
                                    <td colspan="6" class="text-center py-4 text-muted">Kayıt bulunamadı.</td>
                                </tr>
                                {% endif %}
                                {% for d in dossiers %}
                                <tr>
                                    <td><strong>{{ d.dossier_code }}</strong></td>
                                    <td>
                                        <small class="fw-bold d-block">{{ d.brand }} {{ d.model }}</small>
                                        <small class="text-muted">{{ d.vin }}</small>
                                    </td>
                                    <td>{{ d.customer_name }}</td>
                                    <td class="text-success fw-bold">₺{{ "%.2f"|format(d.total_cost) }}</td>
                                    <td><span class="badge bg-warning text-dark">{{ d.status }}</span></td>
                                    <td class="text-end">
                                        <a href="/delete-dossier/{{ d.id }}" class="btn btn-sm btn-outline-danger" onclick="return confirm('Silmek istediğinize emin misiniz?');">
                                            <i class="bi bi-trash"></i> Sil
                                        </a>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- JS Maskeleme ve Bağımlılıklar -->
<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
<script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jquery.inputmask/5.0.8/jquery.inputmask.min.js"></script>
<script>
    $(document).ready(function(){
        // Karakter girildikçe kalan alanlar '_' olarak görünmeye devam eder
        $("#create_vin, #search_vin").inputmask({
            mask: "*****************",
            placeholder: "_",
            greedy: true,
            clearMaskOnLostFocus: false,
            definitions: {
                '*': {
                    validator: "[A-Za-z0-9]",
                    casing: "upper"
                }
            }
        });
    });
</script>
</body>
</html>
"""

@app.route('/')
def index():
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("""
            SELECT d.*, v.brand, v.model 
            FROM dossiers d
            LEFT JOIN vehicles v ON d.vin = v.vin
            ORDER BY d.created_at DESC;
        """)
        dossiers = cur.fetchall()
        cur.close()
    finally:
        release_db_connection(conn)
    return render_template_string(HTML_TEMPLATE, dossiers=dossiers, car_brands=CAR_BRANDS)

@app.route('/create-dossier', methods=['POST'])
def create_dossier():
    vin = request.form['vin'].strip().upper()
    brand = request.form['brand'].strip()
    model = request.form['model'].strip()
    customer_name = request.form['customer_name'].strip()
    parts_cost = float(request.form.get('parts_cost', 0))
    labor_cost = float(request.form.get('labor_cost', 0))
    total_cost = parts_cost + labor_cost

    clean_vin = vin.replace("_", "")
    if len(clean_vin) != 17:
        conn = get_db_connection()
        try:
            cur = conn.cursor(cursor_factory=RealDictCursor)
            cur.execute("SELECT d.*, v.brand, v.model FROM dossiers d LEFT JOIN vehicles v ON d.vin = v.vin ORDER BY d.created_at DESC;")
            dossiers = cur.fetchall()
            cur.close()
        finally:
            release_db_connection(conn)
        error_msg = f"Şasi numarası eksik girildi! Lütfen 17 hanenin tamamını doldurunuz (Girilen: {len(clean_vin)} hane)."
        return render_template_string(HTML_TEMPLATE, dossiers=dossiers, car_brands=CAR_BRANDS, error_message=error_msg)

    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT vin FROM vehicles WHERE vin = %s;", (clean_vin,))
        exists = cur.fetchone()

        if not exists:
            cur.execute("""
                INSERT INTO vehicles (vin, brand, model, model_year, engine)
                VALUES (%s, %s, %s, 2024, '1.6 Standart');
            """, (clean_vin, brand, model))
        else:
            cur.execute("""
                UPDATE vehicles SET brand = %s, model = %s WHERE vin = %s;
            """, (brand, model, clean_vin))

        dossier_code = f"DOS-{random.randint(1000, 9999)}"
        cur.execute("""
            INSERT INTO dossiers (dossier_code, vin, customer_name, parts_cost, labor_cost, total_cost, status)
            VALUES (%s, %s, %s, %s, %s, %s, 'DRAFT');
        """, (dossier_code, clean_vin, customer_name, parts_cost, labor_cost, total_cost))

        conn.commit()
        cur.close()
    finally:
        release_db_connection(conn)
    return redirect(url_for('index'))

@app.route('/search-dossier', methods=['POST'])
def search_dossier():
    keyword = request.form.get('keyword', '').strip()
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        query = """
            SELECT d.*, v.brand, v.model 
            FROM dossiers d
            LEFT JOIN vehicles v ON d.vin = v.vin
            WHERE d.customer_name ILIKE %s OR d.vin ILIKE %s
            ORDER BY d.created_at DESC;
        """
        search_pattern = f"%{keyword}%"
        cur.execute(query, (search_pattern, search_pattern))
        dossiers = cur.fetchall()
        cur.close()
    finally:
        release_db_connection(conn)
    return render_template_string(HTML_TEMPLATE, dossiers=dossiers, car_brands=CAR_BRANDS, search_keyword=keyword)

@app.route('/delete-dossier/<int:id>')
def delete_dossier(id):
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM dossiers WHERE id = %s;", (id,))
        conn.commit()
        cur.close()
    finally:
        release_db_connection(conn)
    return redirect(url_for('index'))

@app.route('/query-vin', methods=['POST'])
def query_vin():
    search_vin = request.form['vin'].strip().upper().replace("_", "")
    conn = get_db_connection()
    try:
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute("SELECT * FROM vehicles WHERE vin = %s;", (search_vin,))
        queried_vehicle = cur.fetchone()
        cur.execute("SELECT d.*, v.brand, v.model FROM dossiers d LEFT JOIN vehicles v ON d.vin = v.vin ORDER BY d.created_at DESC;")
        dossiers = cur.fetchall()
        cur.close()
    finally:
        release_db_connection(conn)
    return render_template_string(HTML_TEMPLATE, dossiers=dossiers, car_brands=CAR_BRANDS, queried_vehicle=queried_vehicle)

if __name__ == '__main__':
    app.run(debug=True, port=5000)