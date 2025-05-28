import flask
import pyodbc
from flask import jsonify, request
from flask_cors import CORS



conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=KAZEL;"
    "Database=QL_GIAIDAUONLINE;"
    "Trusted_Connection=yes"
)
con = pyodbc.connect(conn_str)
cursor = con.cursor()

app = flask.Flask(__name__)
CORS(app)

@app.route('/GiaiDau/GetAll', methods=['GET'])
def get_giaidau():
    cursor = con.cursor()
    cursor.execute("""
        SELECT IdGiai, TenGiai, NgayBatDau, NgayKetThuc, MoTa 
        FROM GiaiDau
    """)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            "IdGiai": row.IdGiai,
            "TenGiai": row.TenGiai,
            "NgayBatDau": row.NgayBatDau.strftime('%Y-%m-%d') if row.NgayBatDau else None,
            "NgayKetThuc": row.NgayKetThuc.strftime('%Y-%m-%d') if row.NgayKetThuc else None,
            "MoTa": row.MoTa if row.MoTa else ""
        })

    return jsonify(result)


@app.route('/GiaiDau/Add', methods=['POST'])
def tao_giai_dau():
    try:
        data = request.json
        ten_giai = data.get('TenGiai')
        ngay_bat_dau = data.get('NgayBatDau')  # 'YYYY-MM-DD'
        ngay_ket_thuc = data.get('NgayKetThuc')
        mo_ta = data.get('MoTa')

        if not ten_giai:
            return jsonify({'error': 'Tên giải đấu là bắt buộc'}), 400

        cursor = con.cursor()
        query = """
            INSERT INTO GiaiDau (TenGiai, NgayBatDau, NgayKetThuc, MoTa)
            VALUES (?, ?, ?, ?)
        """
        cursor.execute(query, (ten_giai, ngay_bat_dau, ngay_ket_thuc, mo_ta))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Tạo giải đấu thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# Lấy danh sách đội thi đấu kèm tên giải đấu
@app.route('/DoiThiDau/GetAll', methods=['GET'])
def get_all_doi_thi_dau():
    cursor = con.cursor()
    cursor.execute("""
        SELECT d.IdDoi, d.TenDoi, d.TenHuanLuyenVien, d.IdGiai, g.TenGiai
        FROM DoiThiDau d
        LEFT JOIN GiaiDau g ON d.IdGiai = g.IdGiai
    """)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'IdDoi': row.IdDoi,
            'TenDoi': row.TenDoi,
            'TenHuanLuyenVien': row.TenHuanLuyenVien,
            'IdGiai': row.IdGiai,
            'TenGiai': row.TenGiai
        })
    return jsonify(result)


# Lấy danh sách thành viên theo đội
@app.route('/ThanhVienDoi/GetByDoi/<int:id_doi>', methods=['GET'])
def get_thanh_vien_by_doi(id_doi):
    cursor = con.cursor()
    cursor.execute("""
        SELECT IdThanhVien, HoTen, ViTri, SoAo, IdDoi FROM ThanhVienDoi WHERE IdDoi = ?
    """, (id_doi,))
    rows = cursor.fetchall()
    result = []
    for row in rows:
        result.append({
            'IdThanhVien': row.IdThanhVien,
            'HoTen': row.HoTen,
            'ViTri': row.ViTri,
            'SoAo': row.SoAo,
            'IdDoi': row.IdDoi
        })
    return jsonify(result)

@app.route('/DoiThiDau/AddFull', methods=['POST'])
def add_doi_va_thanhvien():
    data = request.json
    ten_doi = data.get('TenDoi')
    ten_hlv = data.get('TenHuanLuyenVien')
    id_giai = data.get('IdGiai')
    thanh_vien_list = data.get('ThanhVien')

    if not ten_doi or not id_giai or not thanh_vien_list:
        return jsonify({'error': 'Thiếu dữ liệu bắt buộc'}), 400

    cursor = con.cursor()
    try:
        # Thêm đội và lấy ID bằng OUTPUT
        cursor.execute("""
            INSERT INTO DoiThiDau (TenDoi, TenHuanLuyenVien, IdGiai)
            OUTPUT INSERTED.IdDoi
            VALUES (?, ?, ?)
        """, (ten_doi, ten_hlv, id_giai))
        
        id_doi_row = cursor.fetchone()
        if not id_doi_row or id_doi_row[0] is None:
            return jsonify({'error': 'Không lấy được ID đội'}), 500

        id_doi = id_doi_row[0]
        print("ID đội:", id_doi)  # ✅ Log ra ID để debug

        # Thêm từng thành viên với ID đội
        for tv in thanh_vien_list:
            cursor.execute("""
                INSERT INTO ThanhVienDoi (HoTen, ViTri, SoAo, IdDoi)
                VALUES (?, ?, ?, ?)
            """, (tv.get('HoTen'), tv.get('ViTri'), tv.get('SoAo'), id_doi))

        con.commit()
        return jsonify({'message': 'Thêm đội và thành viên thành công'}), 201

    except Exception as e:
        con.rollback()
        return jsonify({'error': str(e)}), 500


    
# === CHẠY APP ===
if __name__ == '__main__':
    if con:
        app.run(debug=True)
    else:
        print("❌ Không chạy Flask do kết nối SQL thất bại.")

