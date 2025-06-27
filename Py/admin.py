import flask
import pyodbc
from flask import jsonify, request
from flask_cors import CORS
import hashlib
import secrets
from datetime import datetime, timedelta
import jwt

conn_str = (
    "Driver={ODBC Driver 17 for SQL Server};"
    "Server=KAZEL;"
    "Database=QL_GIAIDAU_VALORANT;"
    "Trusted_Connection=yes"
)
con = pyodbc.connect(conn_str)
cursor = con.cursor()

app = flask.Flask(__name__)
CORS(app)

# Secret key for JWT (in production, use environment variable)
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed_password):
    """Verify password against hash"""
    return hash_password(password) == hashed_password

def generate_token(user_id, username):
    """Generate JWT token"""
    payload = {
        'user_id': user_id,
        'username': username,
        'exp': datetime.utcnow() + timedelta(hours=24)
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# ===== QUAN TRI ROUTES =====

@app.route('/QuanTri/Register', methods=['POST'])
def register_admin():
    try:
        data = request.json
        ten_dang_nhap = data.get('TenDangNhap')
        mat_khau = data.get('MatKhau')
        ho_ten = data.get('HoTen')
        vai_tro = data.get('VaiTro', 'Admin')
        mo_ta = data.get('MoTa', '')

        if not ten_dang_nhap or not mat_khau or not ho_ten:
            return jsonify({'error': 'Tên đăng nhập, mật khẩu và họ tên là bắt buộc'}), 400

        if len(mat_khau) < 6:
            return jsonify({'error': 'Mật khẩu phải có ít nhất 6 ký tự'}), 400

        cursor = con.cursor()
        
        # Kiểm tra tên đăng nhập đã tồn tại
        cursor.execute("SELECT COUNT(*) FROM QuanTri WHERE TenDangNhap = ?", (ten_dang_nhap,))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Tên đăng nhập đã tồn tại'}), 400

        # Hash mật khẩu
        hashed_password = hash_password(mat_khau)

        # Thêm quản trị viên mới
        query = """
            INSERT INTO QuanTri (TenDangNhap, MatKhau, HoTen, VaiTro, MoTa)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (ten_dang_nhap, hashed_password, ho_ten, vai_tro, mo_ta))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Đăng ký quản trị viên thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/QuanTri/Login', methods=['POST'])
def login_admin():
    try:
        data = request.json
        ten_dang_nhap = data.get('TenDangNhap')
        mat_khau = data.get('MatKhau')

        if not ten_dang_nhap or not mat_khau:
            return jsonify({'error': 'Tên đăng nhập và mật khẩu là bắt buộc'}), 400

        cursor = con.cursor()
        cursor.execute("""
            SELECT IdQuanTri, TenDangNhap, MatKhau, HoTen, VaiTro 
            FROM QuanTri 
            WHERE TenDangNhap = ?
        """, (ten_dang_nhap,))
        
        user = cursor.fetchone()
        cursor.close()

        if not user:
            return jsonify({'error': 'Tên đăng nhập không tồn tại'}), 401

        # Verify password
        if not verify_password(mat_khau, user.MatKhau):
            return jsonify({'error': 'Mật khẩu không chính xác'}), 401

        # Generate token
        token = generate_token(user.IdQuanTri, user.TenDangNhap)

        return jsonify({
            'message': 'Đăng nhập thành công',
            'token': token,
            'user': {
                'IdQuanTri': user.IdQuanTri,
                'TenDangNhap': user.TenDangNhap,
                'HoTen': user.HoTen,
                'VaiTro': user.VaiTro
            }
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/QuanTri/GetAll', methods=['GET'])
def get_all_quan_tri():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT IdQuanTri, TenDangNhap, HoTen, VaiTro, MoTa
            FROM QuanTri
            ORDER BY IdQuanTri
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdQuanTri": row.IdQuanTri,
                "TenDangNhap": row.TenDangNhap,
                "HoTen": row.HoTen,
                "VaiTro": row.VaiTro,
                "MoTa": row.MoTa if row.MoTa else ""
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/QuanTri/GetById/<int:id_quan_tri>', methods=['GET'])
def get_quan_tri_by_id(id_quan_tri):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT IdQuanTri, TenDangNhap, HoTen, VaiTro, MoTa
            FROM QuanTri
            WHERE IdQuanTri = ?
        """, (id_quan_tri,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Quản trị viên không tồn tại'}), 404

        result = {
            "IdQuanTri": row.IdQuanTri,
            "TenDangNhap": row.TenDangNhap,
            "HoTen": row.HoTen,
            "VaiTro": row.VaiTro,
            "MoTa": row.MoTa if row.MoTa else ""
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/QuanTri/Update/<int:id_quan_tri>', methods=['PUT'])
def update_quan_tri(id_quan_tri):
    try:
        data = request.json
        ho_ten = data.get('HoTen')
        vai_tro = data.get('VaiTro')
        mo_ta = data.get('MoTa', '')

        if not ho_ten or not vai_tro:
            return jsonify({'error': 'Họ tên và vai trò là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra quản trị viên có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM QuanTri WHERE IdQuanTri = ?", (id_quan_tri,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Quản trị viên không tồn tại'}), 404

        # Cập nhật thông tin
        query = """
            UPDATE QuanTri 
            SET HoTen = ?, VaiTro = ?, MoTa = ?
            WHERE IdQuanTri = ?
        """
        cursor.execute(query, (ho_ten, vai_tro, mo_ta, id_quan_tri))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật thông tin quản trị viên thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/QuanTri/ChangePassword/<int:id_quan_tri>', methods=['PUT'])
def change_password(id_quan_tri):
    try:
        data = request.json
        mat_khau_cu = data.get('MatKhauCu')
        mat_khau_moi = data.get('MatKhauMoi')

        if not mat_khau_cu or not mat_khau_moi:
            return jsonify({'error': 'Mật khẩu cũ và mật khẩu mới là bắt buộc'}), 400

        if len(mat_khau_moi) < 6:
            return jsonify({'error': 'Mật khẩu mới phải có ít nhất 6 ký tự'}), 400

        cursor = con.cursor()
        
        # Lấy mật khẩu hiện tại
        cursor.execute("SELECT MatKhau FROM QuanTri WHERE IdQuanTri = ?", (id_quan_tri,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Quản trị viên không tồn tại'}), 404

        # Verify mật khẩu cũ
        if not verify_password(mat_khau_cu, row.MatKhau):
            return jsonify({'error': 'Mật khẩu cũ không chính xác'}), 400

        # Hash mật khẩu mới
        hashed_new_password = hash_password(mat_khau_moi)

        # Cập nhật mật khẩu
        cursor.execute("UPDATE QuanTri SET MatKhau = ? WHERE IdQuanTri = ?", 
                      (hashed_new_password, id_quan_tri))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Đổi mật khẩu thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/QuanTri/Delete/<int:id_quan_tri>', methods=['DELETE'])
def delete_quan_tri(id_quan_tri):
    try:
        cursor = con.cursor()
        
        # Kiểm tra quản trị viên có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM QuanTri WHERE IdQuanTri = ?", (id_quan_tri,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Quản trị viên không tồn tại'}), 404

        # Kiểm tra không được xóa quản trị viên cuối cùng
        cursor.execute("SELECT COUNT(*) FROM QuanTri")
        total_count = cursor.fetchone()[0]
        if total_count <= 1:
            return jsonify({'error': 'Không thể xóa quản trị viên cuối cùng'}), 400

        # Xóa quản trị viên
        cursor.execute("DELETE FROM QuanTri WHERE IdQuanTri = ?", (id_quan_tri,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa quản trị viên thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ===== GIAI DAU ROUTES =====

@app.route('/GiaiDau/GetAll', methods=['GET'])
def get_all_giai_dau():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT IdGiai, TenGiai, NgayBatDau, NgayKetThuc, SoTeamThamGia, 
                   GiaiThuong, HinhAnh, MoTa
            FROM GiaiDau
            ORDER BY NgayBatDau DESC
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdGiai": row.IdGiai,
                "TenGiai": row.TenGiai,
                "NgayBatDau": row.NgayBatDau.strftime('%Y-%m-%d') if row.NgayBatDau else None,
                "NgayKetThuc": row.NgayKetThuc.strftime('%Y-%m-%d') if row.NgayKetThuc else None,
                "SoTeamThamGia": row.SoTeamThamGia if row.SoTeamThamGia else 0,
                "GiaiThuong": float(row.GiaiThuong) if row.GiaiThuong else 0,
                "HinhAnh": row.HinhAnh if row.HinhAnh else "",
                "MoTa": row.MoTa if row.MoTa else ""
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/GiaiDau/GetById/<int:id_giai>', methods=['GET'])
def get_giai_dau_by_id(id_giai):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT IdGiai, TenGiai, NgayBatDau, NgayKetThuc, SoTeamThamGia, 
                   GiaiThuong, HinhAnh, MoTa
            FROM GiaiDau
            WHERE IdGiai = ?
        """, (id_giai,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 404

        result = {
            "IdGiai": row.IdGiai,
            "TenGiai": row.TenGiai,
            "NgayBatDau": row.NgayBatDau.strftime('%Y-%m-%d') if row.NgayBatDau else None,
            "NgayKetThuc": row.NgayKetThuc.strftime('%Y-%m-%d') if row.NgayKetThuc else None,
            "SoTeamThamGia": row.SoTeamThamGia if row.SoTeamThamGia else 0,
            "GiaiThuong": float(row.GiaiThuong) if row.GiaiThuong else 0,
            "HinhAnh": row.HinhAnh if row.HinhAnh else "",
            "MoTa": row.MoTa if row.MoTa else ""
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/GiaiDau/Create', methods=['POST'])
def create_giai_dau():
    try:
        data = request.json
        ten_giai = data.get('TenGiai')
        ngay_bat_dau = data.get('NgayBatDau')
        ngay_ket_thuc = data.get('NgayKetThuc')
        so_team_tham_gia = data.get('SoTeamThamGia', 0)
        giai_thuong = data.get('GiaiThuong', 0)
        hinh_anh = data.get('HinhAnh', '')
        mo_ta = data.get('MoTa', '')

        if not ten_giai:
            return jsonify({'error': 'Tên giải đấu là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra tên giải đấu đã tồn tại
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE TenGiai = ?", (ten_giai,))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Tên giải đấu đã tồn tại'}), 400

        # Thêm giải đấu mới
        query = """
            INSERT INTO GiaiDau (TenGiai, NgayBatDau, NgayKetThuc, SoTeamThamGia, 
                               GiaiThuong, HinhAnh, MoTa)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (ten_giai, ngay_bat_dau, ngay_ket_thuc, so_team_tham_gia, 
                              giai_thuong, hinh_anh, mo_ta))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Tạo giải đấu thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/GiaiDau/Update/<int:id_giai>', methods=['PUT'])
def update_giai_dau(id_giai):
    try:
        data = request.json
        ten_giai = data.get('TenGiai')
        ngay_bat_dau = data.get('NgayBatDau')
        ngay_ket_thuc = data.get('NgayKetThuc')
        so_team_tham_gia = data.get('SoTeamThamGia', 0)
        giai_thuong = data.get('GiaiThuong', 0)
        hinh_anh = data.get('HinhAnh', '')
        mo_ta = data.get('MoTa', '')

        if not ten_giai:
            return jsonify({'error': 'Tên giải đấu là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 404

        # Kiểm tra tên giải đấu đã tồn tại (trừ chính nó)
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE TenGiai = ? AND IdGiai != ?", 
                      (ten_giai, id_giai))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Tên giải đấu đã tồn tại'}), 400

        # Cập nhật thông tin
        query = """
            UPDATE GiaiDau 
            SET TenGiai = ?, NgayBatDau = ?, NgayKetThuc = ?, SoTeamThamGia = ?,
                GiaiThuong = ?, HinhAnh = ?, MoTa = ?
            WHERE IdGiai = ?
        """
        cursor.execute(query, (ten_giai, ngay_bat_dau, ngay_ket_thuc, so_team_tham_gia,
                              giai_thuong, hinh_anh, mo_ta, id_giai))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật giải đấu thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/GiaiDau/Delete/<int:id_giai>', methods=['DELETE'])
def delete_giai_dau(id_giai):
    try:
        cursor = con.cursor()
        
        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 404

        # Xóa giải đấu
        cursor.execute("DELETE FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa giải đấu thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    # ===== TEAM ROUTES =====

@app.route('/Team/GetAll', methods=['GET'])
def get_all_teams():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT t.IdTeam, t.TenTeam, t.TenCaptain, t.EmailLienHe, t.Logo, 
                   t.IdGiai, t.NgayDangKy, g.TenGiai
            FROM Team t
            LEFT JOIN GiaiDau g ON t.IdGiai = g.IdGiai
            ORDER BY t.NgayDangKy DESC
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdTeam": row.IdTeam,
                "TenTeam": row.TenTeam,
                "TenCaptain": row.TenCaptain if row.TenCaptain else "",
                "EmailLienHe": row.EmailLienHe if row.EmailLienHe else "",
                "Logo": row.Logo if row.Logo else "",
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "NgayDangKy": row.NgayDangKy.strftime('%Y-%m-%d %H:%M:%S') if row.NgayDangKy else None
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Team/GetById/<int:id_team>', methods=['GET'])
def get_team_by_id(id_team):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT t.IdTeam, t.TenTeam, t.TenCaptain, t.EmailLienHe, t.Logo, 
                   t.IdGiai, t.NgayDangKy, g.TenGiai
            FROM Team t
            LEFT JOIN GiaiDau g ON t.IdGiai = g.IdGiai
            WHERE t.IdTeam = ?
        """, (id_team,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Team không tồn tại'}), 404

        result = {
            "IdTeam": row.IdTeam,
            "TenTeam": row.TenTeam,
            "TenCaptain": row.TenCaptain if row.TenCaptain else "",
            "EmailLienHe": row.EmailLienHe if row.EmailLienHe else "",
            "Logo": row.Logo if row.Logo else "",
            "IdGiai": row.IdGiai if row.IdGiai else None,
            "TenGiai": row.TenGiai if row.TenGiai else "",
            "NgayDangKy": row.NgayDangKy.strftime('%Y-%m-%d %H:%M:%S') if row.NgayDangKy else None
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Team/Create', methods=['POST'])
def create_team():
    try:
        data = request.json
        ten_team = data.get('TenTeam')
        ten_captain = data.get('TenCaptain', '')
        email_lien_he = data.get('EmailLienHe', '')
        logo = data.get('Logo', '')
        id_giai = data.get('IdGiai')

        if not ten_team:
            return jsonify({'error': 'Tên team là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra tên team đã tồn tại
        cursor.execute("SELECT COUNT(*) FROM Team WHERE TenTeam = ?", (ten_team,))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Tên team đã tồn tại'}), 400

        # Kiểm tra giải đấu có tồn tại không (nếu có IdGiai)
        if id_giai:
            cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
            count = cursor.fetchone()[0]
            if count == 0:
                return jsonify({'error': 'Giải đấu không tồn tại'}), 400

        # Thêm team mới
        query = """
            INSERT INTO Team (TenTeam, TenCaptain, EmailLienHe, Logo, IdGiai)
            VALUES (?, ?, ?, ?, ?)
        """
        cursor.execute(query, (ten_team, ten_captain, email_lien_he, logo, id_giai))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Tạo team thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Team/Update/<int:id_team>', methods=['PUT'])
def update_team(id_team):
    try:
        data = request.json
        ten_team = data.get('TenTeam')
        ten_captain = data.get('TenCaptain', '')
        email_lien_he = data.get('EmailLienHe', '')
        logo = data.get('Logo', '')
        id_giai = data.get('IdGiai')

        if not ten_team:
            return jsonify({'error': 'Tên team là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra team có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (id_team,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Team không tồn tại'}), 404

        # Kiểm tra tên team đã tồn tại (trừ chính nó)
        cursor.execute("SELECT COUNT(*) FROM Team WHERE TenTeam = ? AND IdTeam != ?", 
                      (ten_team, id_team))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Tên team đã tồn tại'}), 400

        # Kiểm tra giải đấu có tồn tại không (nếu có IdGiai)
        if id_giai:
            cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
            count = cursor.fetchone()[0]
            if count == 0:
                return jsonify({'error': 'Giải đấu không tồn tại'}), 400

        # Cập nhật thông tin
        query = """
            UPDATE Team 
            SET TenTeam = ?, TenCaptain = ?, EmailLienHe = ?, Logo = ?, IdGiai = ?
            WHERE IdTeam = ?
        """
        cursor.execute(query, (ten_team, ten_captain, email_lien_he, logo, id_giai, id_team))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật team thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Team/Delete/<int:id_team>', methods=['DELETE'])
def delete_team(id_team):
    try:
        cursor = con.cursor()
        
        # Kiểm tra team có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (id_team,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Team không tồn tại'}), 404

        # Xóa team
        cursor.execute("DELETE FROM Team WHERE IdTeam = ?", (id_team,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa team thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Team/GetByGiai/<int:id_giai>', methods=['GET'])
def get_teams_by_giai(id_giai):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT t.IdTeam, t.TenTeam, t.TenCaptain, t.EmailLienHe, t.Logo, 
                   t.IdGiai, t.NgayDangKy, g.TenGiai
            FROM Team t
            LEFT JOIN GiaiDau g ON t.IdGiai = g.IdGiai
            WHERE t.IdGiai = ?
            ORDER BY t.NgayDangKy DESC
        """, (id_giai,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdTeam": row.IdTeam,
                "TenTeam": row.TenTeam,
                "TenCaptain": row.TenCaptain if row.TenCaptain else "",
                "EmailLienHe": row.EmailLienHe if row.EmailLienHe else "",
                "Logo": row.Logo if row.Logo else "",
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "NgayDangKy": row.NgayDangKy.strftime('%Y-%m-%d %H:%M:%S') if row.NgayDangKy else None
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ===== PLAYER ROUTES =====

@app.route('/Player/GetAll', methods=['GET'])
def get_all_players():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT p.IdPlayer, p.GameName, p.TagLine, p.HoTenThat, p.ViTri, 
                   p.RankHienTai, p.MainAgent, p.IdTeam, t.TenTeam
            FROM Player p
            LEFT JOIN Team t ON p.IdTeam = t.IdTeam
            ORDER BY p.IdPlayer DESC
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdPlayer": row.IdPlayer,
                "GameName": row.GameName,
                "TagLine": row.TagLine if row.TagLine else "",
                "HoTenThat": row.HoTenThat if row.HoTenThat else "",
                "ViTri": row.ViTri if row.ViTri else "",
                "RankHienTai": row.RankHienTai if row.RankHienTai else "",
                "MainAgent": row.MainAgent if row.MainAgent else "",
                "IdTeam": row.IdTeam if row.IdTeam else None,
                "TenTeam": row.TenTeam if row.TenTeam else ""
            })

        cursor.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Player/GetById/<int:id_player>', methods=['GET'])
def get_player_by_id(id_player):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT p.IdPlayer, p.GameName, p.TagLine, p.HoTenThat, p.ViTri, 
                   p.RankHienTai, p.MainAgent, p.IdTeam, t.TenTeam
            FROM Player p
            LEFT JOIN Team t ON p.IdTeam = t.IdTeam
            WHERE p.IdPlayer = ?
        """, (id_player,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Thành viên không tồn tại'}), 404

        result = {
            "IdPlayer": row.IdPlayer,
            "GameName": row.GameName,
            "TagLine": row.TagLine if row.TagLine else "",
            "HoTenThat": row.HoTenThat if row.HoTenThat else "",
            "ViTri": row.ViTri if row.ViTri else "",
            "RankHienTai": row.RankHienTai if row.RankHienTai else "",
            "MainAgent": row.MainAgent if row.MainAgent else "",
            "IdTeam": row.IdTeam if row.IdTeam else None,
            "TenTeam": row.TenTeam if row.TenTeam else ""
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Player/Create', methods=['POST'])
def create_player():
    try:
        data = request.json
        game_name = data.get('GameName')
        tag_line = data.get('TagLine', '')
        ho_ten_that = data.get('HoTenThat', '')
        vi_tri = data.get('ViTri', '')
        rank_hien_tai = data.get('RankHienTai', '')
        main_agent = data.get('MainAgent', '')
        id_team = data.get('IdTeam')

        if not game_name:
            return jsonify({'error': 'Tên game là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra tên game đã tồn tại
        cursor.execute("SELECT COUNT(*) FROM Player WHERE GameName = ?", (game_name,))
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.close()
            return jsonify({'error': 'Tên game đã tồn tại'}), 400

        # Kiểm tra đội có tồn tại không (nếu có IdTeam)
        if id_team:
            cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (id_team,))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.close()
                return jsonify({'error': 'Đội không tồn tại'}), 400

        # Thêm thành viên mới
        query = """
            INSERT INTO Player (GameName, TagLine, HoTenThat, ViTri, RankHienTai, MainAgent, IdTeam)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (game_name, tag_line, ho_ten_that, vi_tri, rank_hien_tai, main_agent, id_team))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Tạo thành viên thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Player/Update/<int:id_player>', methods=['PUT'])
def update_player(id_player):
    try:
        data = request.json
        game_name = data.get('GameName')
        tag_line = data.get('TagLine', '')
        ho_ten_that = data.get('HoTenThat', '')
        vi_tri = data.get('ViTri', '')
        rank_hien_tai = data.get('RankHienTai', '')
        main_agent = data.get('MainAgent', '')
        id_team = data.get('IdTeam')

        if not game_name:
            return jsonify({'error': 'Tên game là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra thành viên có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Player WHERE IdPlayer = ?", (id_player,))
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.close()
            return jsonify({'error': 'Thành viên không tồn tại'}), 404

        # Kiểm tra tên game đã tồn tại (trừ chính nó)
        cursor.execute("SELECT COUNT(*) FROM Player WHERE GameName = ? AND IdPlayer != ?", 
                      (game_name, id_player))
        count = cursor.fetchone()[0]
        if count > 0:
            cursor.close()
            return jsonify({'error': 'Tên game đã tồn tại'}), 400

        # Kiểm tra đội có tồn tại không (nếu có IdTeam)
        if id_team:
            cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (id_team,))
            count = cursor.fetchone()[0]
            if count == 0:
                cursor.close()
                return jsonify({'error': 'Đội không tồn tại'}), 400

        # Cập nhật thông tin
        query = """
            UPDATE Player 
            SET GameName = ?, TagLine = ?, HoTenThat = ?, ViTri = ?, 
                RankHienTai = ?, MainAgent = ?, IdTeam = ?
            WHERE IdPlayer = ?
        """
        cursor.execute(query, (game_name, tag_line, ho_ten_that, vi_tri, rank_hien_tai, main_agent, id_team, id_player))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật thành viên thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Player/Delete/<int:id_player>', methods=['DELETE'])
def delete_player(id_player):
    try:
        cursor = con.cursor()
        
        # Kiểm tra thành viên có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Player WHERE IdPlayer = ?", (id_player,))
        count = cursor.fetchone()[0]
        if count == 0:
            cursor.close()
            return jsonify({'error': 'Thành viên không tồn tại'}), 404

        # Xóa thành viên
        cursor.execute("DELETE FROM Player WHERE IdPlayer = ?", (id_player,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa thành viên thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Player/GetByTeam/<int:id_team>', methods=['GET'])
def get_players_by_team(id_team):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT p.IdPlayer, p.GameName, p.TagLine, p.HoTenThat, p.ViTri, 
                   p.RankHienTai, p.MainAgent, p.IdTeam, t.TenTeam
            FROM Player p
            LEFT JOIN Team t ON p.IdTeam = t.IdTeam
            WHERE p.IdTeam = ?
            ORDER BY p.IdPlayer DESC
        """, (id_team,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdPlayer": row.IdPlayer,
                "GameName": row.GameName,
                "TagLine": row.TagLine if row.TagLine else "",
                "HoTenThat": row.HoTenThat if row.HoTenThat else "",
                "ViTri": row.ViTri if row.ViTri else "",
                "RankHienTai": row.RankHienTai if row.RankHienTai else "",
                "MainAgent": row.MainAgent if row.MainAgent else "",
                "IdTeam": row.IdTeam if row.IdTeam else None,
                "TenTeam": row.TenTeam if row.TenTeam else ""
            })

        cursor.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# ===== TRAN DAU ROUTES =====

@app.route('/TranDau/GetAll', methods=['GET'])
def get_all_tran_dau():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT td.IdTran, td.IdGiai, td.Team1, td.Team2, td.TiSoTeam1, td.TiSoTeam2,
                   td.NgayThiDau, td.VongDau, td.TrangThai, td.TeamThang, td.GhiChu,
                   g.TenGiai, t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang
            FROM TranDau td
            LEFT JOIN GiaiDau g ON td.IdGiai = g.IdGiai
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON td.TeamThang = tw.IdTeam
            ORDER BY td.NgayThiDau DESC
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdTran": row.IdTran,
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "Team1": row.Team1 if row.Team1 else None,
                "Team2": row.Team2 if row.Team2 else None,
                "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
                "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
                "TiSoTeam1": row.TiSoTeam1 if row.TiSoTeam1 else 0,
                "TiSoTeam2": row.TiSoTeam2 if row.TiSoTeam2 else 0,
                "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None,
                "VongDau": row.VongDau if row.VongDau else "",
                "TrangThai": row.TrangThai if row.TrangThai else "Chưa diễn ra",
                "TeamThang": row.TeamThang if row.TeamThang else None,
                "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
                "GhiChu": row.GhiChu if row.GhiChu else ""
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/TranDau/GetById/<int:id_tran>', methods=['GET'])
def get_tran_dau_by_id(id_tran):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT td.IdTran, td.IdGiai, td.Team1, td.Team2, td.TiSoTeam1, td.TiSoTeam2,
                   td.NgayThiDau, td.VongDau, td.TrangThai, td.TeamThang, td.GhiChu,
                   g.TenGiai, t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang
            FROM TranDau td
            LEFT JOIN GiaiDau g ON td.IdGiai = g.IdGiai
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON td.TeamThang = tw.IdTeam
            WHERE td.IdTran = ?
        """, (id_tran,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 404

        result = {
            "IdTran": row.IdTran,
            "IdGiai": row.IdGiai if row.IdGiai else None,
            "TenGiai": row.TenGiai if row.TenGiai else "",
            "Team1": row.Team1 if row.Team1 else None,
            "Team2": row.Team2 if row.Team2 else None,
            "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
            "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
            "TiSoTeam1": row.TiSoTeam1 if row.TiSoTeam1 else 0,
            "TiSoTeam2": row.TiSoTeam2 if row.TiSoTeam2 else 0,
            "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None,
            "VongDau": row.VongDau if row.VongDau else "",
            "TrangThai": row.TrangThai if row.TrangThai else "Chưa diễn ra",
            "TeamThang": row.TeamThang if row.TeamThang else None,
            "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
            "GhiChu": row.GhiChu if row.GhiChu else ""
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/TranDau/Create', methods=['POST'])
def create_tran_dau():
    try:
        data = request.json
        id_giai = data.get('IdGiai')
        team1 = data.get('Team1')
        team2 = data.get('Team2')
        ngay_thi_dau = data.get('NgayThiDau')
        vong_dau = data.get('VongDau', '')
        ghi_chu = data.get('GhiChu', '')

        if not id_giai or not team1 or not team2:
            return jsonify({'error': 'Giải đấu và hai đội thi đấu là bắt buộc'}), 400

        if team1 == team2:
            return jsonify({'error': 'Hai đội thi đấu không thể giống nhau'}), 400

        cursor = con.cursor()
        
        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 400

        # Kiểm tra team có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (team1,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Team 1 không tồn tại'}), 400

        cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (team2,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Team 2 không tồn tại'}), 400

        # Thêm trận đấu mới
        query = """
            INSERT INTO TranDau (IdGiai, Team1, Team2, NgayThiDau, VongDau, GhiChu)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (id_giai, team1, team2, ngay_thi_dau, vong_dau, ghi_chu))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Tạo trận đấu thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/TranDau/Update/<int:id_tran>', methods=['PUT'])
def update_tran_dau(id_tran):
    try:
        data = request.json
        id_giai = data.get('IdGiai')
        team1 = data.get('Team1')
        team2 = data.get('Team2')
        ti_so_team1 = data.get('TiSoTeam1', 0)
        ti_so_team2 = data.get('TiSoTeam2', 0)
        ngay_thi_dau = data.get('NgayThiDau')
        vong_dau = data.get('VongDau', '')
        trang_thai = data.get('TrangThai', 'Chưa diễn ra')
        team_thang = data.get('TeamThang')
        ghi_chu = data.get('GhiChu', '')

        if not id_giai or not team1 or not team2:
            return jsonify({'error': 'Giải đấu và hai đội thi đấu là bắt buộc'}), 400

        if team1 == team2:
            return jsonify({'error': 'Hai đội thi đấu không thể giống nhau'}), 400

        cursor = con.cursor()
        
        # Kiểm tra trận đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM TranDau WHERE IdTran = ?", (id_tran,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 404

        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 400

        # Kiểm tra team có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (team1,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Team 1 không tồn tại'}), 400

        cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (team2,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Team 2 không tồn tại'}), 400

        # Cập nhật thông tin
        query = """
            UPDATE TranDau 
            SET IdGiai = ?, Team1 = ?, Team2 = ?, TiSoTeam1 = ?, TiSoTeam2 = ?,
                NgayThiDau = ?, VongDau = ?, TrangThai = ?, TeamThang = ?, GhiChu = ?
            WHERE IdTran = ?
        """
        cursor.execute(query, (id_giai, team1, team2, ti_so_team1, ti_so_team2,
                              ngay_thi_dau, vong_dau, trang_thai, team_thang, ghi_chu, id_tran))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật trận đấu thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/TranDau/UpdateScore/<int:id_tran>', methods=['PUT'])
def update_tran_dau_score(id_tran):
    try:
        data = request.json
        ti_so_team1 = data.get('TiSoTeam1', 0)
        ti_so_team2 = data.get('TiSoTeam2', 0)
        trang_thai = data.get('TrangThai', 'Đã kết thúc')

        cursor = con.cursor()
        
        # Kiểm tra trận đấu có tồn tại không
        cursor.execute("SELECT Team1, Team2 FROM TranDau WHERE IdTran = ?", (id_tran,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 404

        # Xác định team thắng
        team_thang = None
        if ti_so_team1 > ti_so_team2:
            team_thang = row.Team1
        elif ti_so_team2 > ti_so_team1:
            team_thang = row.Team2

        # Cập nhật tỷ số và team thắng
        query = """
            UPDATE TranDau 
            SET TiSoTeam1 = ?, TiSoTeam2 = ?, TrangThai = ?, TeamThang = ?
            WHERE IdTran = ?
        """
        cursor.execute(query, (ti_so_team1, ti_so_team2, trang_thai, team_thang, id_tran))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật tỷ số thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/TranDau/Delete/<int:id_tran>', methods=['DELETE'])
def delete_tran_dau(id_tran):
    try:
        cursor = con.cursor()
        
        # Kiểm tra trận đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM TranDau WHERE IdTran = ?", (id_tran,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 404

        # Xóa trận đấu
        cursor.execute("DELETE FROM TranDau WHERE IdTran = ?", (id_tran,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa trận đấu thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/TranDau/GetByGiai/<int:id_giai>', methods=['GET'])
def get_tran_dau_by_giai(id_giai):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT td.IdTran, td.IdGiai, td.Team1, td.Team2, td.TiSoTeam1, td.TiSoTeam2,
                   td.NgayThiDau, td.VongDau, td.TrangThai, td.TeamThang, td.GhiChu,
                   g.TenGiai, t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang
            FROM TranDau td
            LEFT JOIN GiaiDau g ON td.IdGiai = g.IdGiai
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON td.TeamThang = tw.IdTeam
            WHERE td.IdGiai = ?
            ORDER BY td.NgayThiDau DESC
        """, (id_giai,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdTran": row.IdTran,
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "Team1": row.Team1 if row.Team1 else None,
                "Team2": row.Team2 if row.Team2 else None,
                "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
                "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
                "TiSoTeam1": row.TiSoTeam1 if row.TiSoTeam1 else 0,
                "TiSoTeam2": row.TiSoTeam2 if row.TiSoTeam2 else 0,
                "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None,
                "VongDau": row.VongDau if row.VongDau else "",
                "TrangThai": row.TrangThai if row.TrangThai else "Chưa diễn ra",
                "TeamThang": row.TeamThang if row.TeamThang else None,
                "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
                "GhiChu": row.GhiChu if row.GhiChu else ""
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/TranDau/GetByVongDau/<vong_dau>', methods=['GET'])
def get_tran_dau_by_vong(vong_dau):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT td.IdTran, td.IdGiai, td.Team1, td.Team2, td.TiSoTeam1, td.TiSoTeam2,
                   td.NgayThiDau, td.VongDau, td.TrangThai, td.TeamThang, td.GhiChu,
                   g.TenGiai, t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang
            FROM TranDau td
            LEFT JOIN GiaiDau g ON td.IdGiai = g.IdGiai
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON td.TeamThang = tw.IdTeam
            WHERE td.VongDau = ?
            ORDER BY td.NgayThiDau DESC
        """, (vong_dau,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdTran": row.IdTran,
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "Team1": row.Team1 if row.Team1 else None,
                "Team2": row.Team2 if row.Team2 else None,
                "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
                "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
                "TiSoTeam1": row.TiSoTeam1 if row.TiSoTeam1 else 0,
                "TiSoTeam2": row.TiSoTeam2 if row.TiSoTeam2 else 0,
                "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None,
                "VongDau": row.VongDau if row.VongDau else "",
                "TrangThai": row.TrangThai if row.TrangThai else "Chưa diễn ra",
                "TeamThang": row.TeamThang if row.TeamThang else None,
                "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
                "GhiChu": row.GhiChu if row.GhiChu else ""
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/Map/GetAll', methods=['GET'])
def get_all_maps():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT IdMap, TenMap, TrangThai
            FROM Map
            WHERE TrangThai = 1
            ORDER BY TenMap
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdMap": row.IdMap,
                "TenMap": row.TenMap,
                "TrangThai": row.TrangThai
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Map/GetById/<int:id_map>', methods=['GET'])
def get_map_by_id(id_map):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT IdMap, TenMap, TrangThai
            FROM Map
            WHERE IdMap = ?
        """, (id_map,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Map không tồn tại'}), 404

        result = {
            "IdMap": row.IdMap,
            "TenMap": row.TenMap,
            "TrangThai": row.TrangThai
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Route để lấy trận đấu theo map (cần thêm cột IdMap vào bảng TranDau)
@app.route('/Map/GetMatches/<int:id_map>', methods=['GET'])
def get_matches_by_map(id_map):
    try:
        cursor = con.cursor()
        # Giả sử bạn đã thêm cột IdMap vào bảng TranDau
        cursor.execute("""
            SELECT td.IdTran, td.IdGiai, td.Team1, td.Team2, td.TiSoTeam1, td.TiSoTeam2,
                   td.NgayThiDau, td.VongDau, td.TrangThai, td.TeamThang, td.GhiChu,
                   g.TenGiai, t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang, m.TenMap
            FROM TranDau td
            LEFT JOIN GiaiDau g ON td.IdGiai = g.IdGiai
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON td.TeamThang = tw.IdTeam
            LEFT JOIN Map m ON td.IdMap = m.IdMap
            WHERE td.IdMap = ?
            ORDER BY td.NgayThiDau DESC
        """, (id_map,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdTran": row.IdTran,
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "Team1": row.Team1 if row.Team1 else None,
                "Team2": row.Team2 if row.Team2 else None,
                "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
                "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
                "TiSoTeam1": row.TiSoTeam1 if row.TiSoTeam1 else 0,
                "TiSoTeam2": row.TiSoTeam2 if row.TiSoTeam2 else 0,
                "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None,
                "VongDau": row.VongDau if row.VongDau else "",
                "TrangThai": row.TrangThai if row.TrangThai else "Chưa diễn ra",
                "TeamThang": row.TeamThang if row.TeamThang else None,
                "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
                "GhiChu": row.GhiChu if row.GhiChu else "",
                "TenMap": row.TenMap if row.TenMap else ""
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

    
    
# ===== BANG XEP HANG ROUTES =====

@app.route('/BangXepHang/GetAll', methods=['GET'])
def get_all_bang_xep_hang():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT bxh.IdXH, bxh.IdGiai, bxh.IdTeam, bxh.TranDa, bxh.TranThang, 
                   bxh.TranThua, bxh.MapThang, bxh.MapThua, bxh.Diem, bxh.HangHienTai,
                   g.TenGiai, t.TenTeam
            FROM BangXepHang bxh
            LEFT JOIN GiaiDau g ON bxh.IdGiai = g.IdGiai
            LEFT JOIN Team t ON bxh.IdTeam = t.IdTeam
            ORDER BY bxh.IdGiai, bxh.Diem DESC, bxh.HangHienTai
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdXH": row.IdXH,
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "IdTeam": row.IdTeam if row.IdTeam else None,
                "TenTeam": row.TenTeam if row.TenTeam else "",
                "TranDa": row.TranDa if row.TranDa else 0,
                "TranThang": row.TranThang if row.TranThang else 0,
                "TranThua": row.TranThua if row.TranThua else 0,
                "MapThang": row.MapThang if row.MapThang else 0,
                "MapThua": row.MapThua if row.MapThua else 0,
                "Diem": row.Diem if row.Diem else 0,
                "HangHienTai": row.HangHienTai if row.HangHienTai else 0,
                "TiLe": f"{row.MapThang}/{row.MapThua}" if row.MapThang and row.MapThua else "0/0"
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/BangXepHang/GetById/<int:id_xh>', methods=['GET'])
def get_bang_xep_hang_by_id(id_xh):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT bxh.IdXH, bxh.IdGiai, bxh.IdTeam, bxh.TranDa, bxh.TranThang, 
                   bxh.TranThua, bxh.MapThang, bxh.MapThua, bxh.Diem, bxh.HangHienTai,
                   g.TenGiai, t.TenTeam
            FROM BangXepHang bxh
            LEFT JOIN GiaiDau g ON bxh.IdGiai = g.IdGiai
            LEFT JOIN Team t ON bxh.IdTeam = t.IdTeam
            WHERE bxh.IdXH = ?
        """, (id_xh,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Bảng xếp hạng không tồn tại'}), 404

        result = {
            "IdXH": row.IdXH,
            "IdGiai": row.IdGiai if row.IdGiai else None,
            "TenGiai": row.TenGiai if row.TenGiai else "",
            "IdTeam": row.IdTeam if row.IdTeam else None,
            "TenTeam": row.TenTeam if row.TenTeam else "",
            "TranDa": row.TranDa if row.TranDa else 0,
            "TranThang": row.TranThang if row.TranThang else 0,
            "TranThua": row.TranThua if row.TranThua else 0,
            "MapThang": row.MapThang if row.MapThang else 0,
            "MapThua": row.MapThua if row.MapThua else 0,
            "Diem": row.Diem if row.Diem else 0,
            "HangHienTai": row.HangHienTai if row.HangHienTai else 0,
            "TiLe": f"{row.MapThang}/{row.MapThua}" if row.MapThang and row.MapThua else "0/0"
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/BangXepHang/GetByGiai/<int:id_giai>', methods=['GET'])
def get_bang_xep_hang_by_giai(id_giai):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT bxh.IdXH, bxh.IdGiai, bxh.IdTeam, bxh.TranDa, bxh.TranThang, 
                   bxh.TranThua, bxh.MapThang, bxh.MapThua, bxh.Diem, bxh.HangHienTai,
                   g.TenGiai, t.TenTeam
            FROM BangXepHang bxh
            LEFT JOIN GiaiDau g ON bxh.IdGiai = g.IdGiai
            LEFT JOIN Team t ON bxh.IdTeam = t.IdTeam
            WHERE bxh.IdGiai = ?
            ORDER BY bxh.Diem DESC, bxh.HangHienTai
        """, (id_giai,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdXH": row.IdXH,
                "IdGiai": row.IdGiai if row.IdGiai else None,
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "IdTeam": row.IdTeam if row.IdTeam else None,
                "TenTeam": row.TenTeam if row.TenTeam else "",
                "TranDa": row.TranDa if row.TranDa else 0,
                "TranThang": row.TranThang if row.TranThang else 0,
                "TranThua": row.TranThua if row.TranThua else 0,
                "MapThang": row.MapThang if row.MapThang else 0,
                "MapThua": row.MapThua if row.MapThua else 0,
                "Diem": row.Diem if row.Diem else 0,
                "HangHienTai": row.HangHienTai if row.HangHienTai else 0,
                "TiLe": f"{row.MapThang}/{row.MapThua}" if row.MapThang and row.MapThua else "0/0"
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
@app.route('/BangXepHang/Create', methods=['POST'])
def create_bang_xep_hang():
    try:
        data = request.json
        id_giai = data.get('IdGiai')
        id_team = data.get('IdTeam')
        tran_da = data.get('TranDa', 0)
        tran_thang = data.get('TranThang', 0)
        tran_thua = data.get('TranThua', 0)
        map_thang = data.get('MapThang', 0)
        map_thua = data.get('MapThua', 0)
        diem = data.get('Diem', 0)
        hang_hien_tai = data.get('HangHienTai', 0)

        if not id_giai or not id_team:
            return jsonify({'error': 'ID giải đấu và ID team là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 400

        # Kiểm tra team có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Team WHERE IdTeam = ?", (id_team,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Team không tồn tại'}), 400

        # Kiểm tra team đã có trong bảng xếp hạng của giải này chưa
        cursor.execute("SELECT COUNT(*) FROM BangXepHang WHERE IdGiai = ? AND IdTeam = ?", 
                      (id_giai, id_team))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Team đã có trong bảng xếp hạng của giải này'}), 400

        # Thêm bảng xếp hạng mới
        query = """
            INSERT INTO BangXepHang (IdGiai, IdTeam, TranDa, TranThang, TranThua, 
                                   MapThang, MapThua, Diem, HangHienTai)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (id_giai, id_team, tran_da, tran_thang, tran_thua,
                              map_thang, map_thua, diem, hang_hien_tai))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Tạo bảng xếp hạng thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/BangXepHang/Update/<int:id_xh>', methods=['PUT'])
def update_bang_xep_hang(id_xh):
    try:
        data = request.json
        tran_da = data.get('TranDa', 0)
        tran_thang = data.get('TranThang', 0)
        tran_thua = data.get('TranThua', 0)
        map_thang = data.get('MapThang', 0)
        map_thua = data.get('MapThua', 0)
        diem = data.get('Diem', 0)
        hang_hien_tai = data.get('HangHienTai', 0)

        cursor = con.cursor()
        
        # Kiểm tra bảng xếp hạng có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM BangXepHang WHERE IdXH = ?", (id_xh,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Bảng xếp hạng không tồn tại'}), 404

        # Cập nhật thông tin
        query = """
            UPDATE BangXepHang 
            SET TranDa = ?, TranThang = ?, TranThua = ?, MapThang = ?, 
                MapThua = ?, Diem = ?, HangHienTai = ?
            WHERE IdXH = ?
        """
        cursor.execute(query, (tran_da, tran_thang, tran_thua, map_thang,
                              map_thua, diem, hang_hien_tai, id_xh))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật bảng xếp hạng thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/BangXepHang/Delete/<int:id_xh>', methods=['DELETE'])
def delete_bang_xep_hang(id_xh):
    try:
        cursor = con.cursor()
        
        # Kiểm tra bảng xếp hạng có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM BangXepHang WHERE IdXH = ?", (id_xh,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Bảng xếp hạng không tồn tại'}), 404

        # Xóa bảng xếp hạng
        cursor.execute("DELETE FROM BangXepHang WHERE IdXH = ?", (id_xh,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa bảng xếp hạng thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/BangXepHang/UpdateFromMatches/<int:id_giai>', methods=['PUT'])
def update_bang_xep_hang_from_matches(id_giai):
    """Cập nhật bảng xếp hạng dựa trên kết quả trận đấu"""
    try:
        cursor = con.cursor()
        
        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 404

        # Lấy tất cả team trong giải
        cursor.execute("SELECT IdTeam FROM Team WHERE IdGiai = ?", (id_giai,))
        teams = cursor.fetchall()

        for team in teams:
            id_team = team.IdTeam
            
            # Tính toán thống kê từ trận đấu
            cursor.execute("""
                SELECT 
                    COUNT(*) as TranDa,
                    SUM(CASE WHEN TeamThang = ? THEN 1 ELSE 0 END) as TranThang,
                    SUM(CASE WHEN TeamThang != ? AND TeamThang IS NOT NULL THEN 1 ELSE 0 END) as TranThua,
                    SUM(CASE WHEN Team1 = ? THEN TiSoTeam1 ELSE TiSoTeam2 END) as MapThang,
                    SUM(CASE WHEN Team1 = ? THEN TiSoTeam2 ELSE TiSoTeam1 END) as MapThua
                FROM TranDau 
                WHERE IdGiai = ? AND (Team1 = ? OR Team2 = ?) AND TrangThai = 'Đã kết thúc'
            """, (id_team, id_team, id_team, id_team, id_giai, id_team, id_team))
            
            stats = cursor.fetchone()
            tran_da = stats.TranDa if stats.TranDa else 0
            tran_thang = stats.TranThang if stats.TranThang else 0
            tran_thua = stats.TranThua if stats.TranThua else 0
            map_thang = stats.MapThang if stats.MapThang else 0
            map_thua = stats.MapThua if stats.MapThua else 0
            
            # Tính điểm (3 điểm thắng, 0 điểm thua)
            diem = tran_thang * 3

            # Kiểm tra team đã có trong bảng xếp hạng chưa
            cursor.execute("SELECT COUNT(*) FROM BangXepHang WHERE IdGiai = ? AND IdTeam = ?", 
                          (id_giai, id_team))
            exists = cursor.fetchone()[0]

            if exists > 0:
                # Cập nhật
                cursor.execute("""
                    UPDATE BangXepHang 
                    SET TranDa = ?, TranThang = ?, TranThua = ?, MapThang = ?, 
                        MapThua = ?, Diem = ?
                    WHERE IdGiai = ? AND IdTeam = ?
                """, (tran_da, tran_thang, tran_thua, map_thang, map_thua, diem, id_giai, id_team))
            else:
                # Thêm mới
                cursor.execute("""
                    INSERT INTO BangXepHang (IdGiai, IdTeam, TranDa, TranThang, TranThua, 
                                           MapThang, MapThua, Diem, HangHienTai)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0)
                """, (id_giai, id_team, tran_da, tran_thang, tran_thua, map_thang, map_thua, diem))

        # Cập nhật hạng hiện tại
        cursor.execute("""
            WITH RankedTeams AS (
                SELECT IdXH, ROW_NUMBER() OVER (ORDER BY Diem DESC, MapThang DESC) as NewRank
                FROM BangXepHang
                WHERE IdGiai = ?
            )
            UPDATE BangXepHang 
            SET HangHienTai = (SELECT NewRank FROM RankedTeams WHERE RankedTeams.IdXH = BangXepHang.IdXH)
            WHERE IdGiai = ?
        """, (id_giai, id_giai))

        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật bảng xếp hạng từ trận đấu thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/BangXepHang/InitializeForTournament/<int:id_giai>', methods=['POST'])
def initialize_bang_xep_hang_for_tournament(id_giai):
    """Khởi tạo bảng xếp hạng cho tất cả team trong giải đấu"""
    try:
        cursor = con.cursor()
        
        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 404

        # Lấy tất cả team trong giải
        cursor.execute("SELECT IdTeam FROM Team WHERE IdGiai = ?", (id_giai,))
        teams = cursor.fetchall()

        if not teams:
            return jsonify({'error': 'Không có team nào trong giải đấu này'}), 400

        # Xóa bảng xếp hạng cũ (nếu có)
        cursor.execute("DELETE FROM BangXepHang WHERE IdGiai = ?", (id_giai,))

        # Thêm tất cả team vào bảng xếp hạng với giá trị mặc định
        for i, team in enumerate(teams):
            cursor.execute("""
                INSERT INTO BangXepHang (IdGiai, IdTeam, TranDa, TranThang, TranThua, 
                                       MapThang, MapThua, Diem, HangHienTai)
                VALUES (?, ?, 0, 0, 0, 0, 0, 0, ?)
            """, (id_giai, team.IdTeam, i + 1))

        con.commit()
        cursor.close()
        
        return jsonify({'message': f'Khởi tạo bảng xếp hạng cho {len(teams)} team thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    # ===== CHI TIET MAP ROUTES =====

@app.route('/ChiTietMap/GetAll', methods=['GET'])
def get_all_chi_tiet_map():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT ctm.IdChiTiet, ctm.IdTran, ctm.IdMap, ctm.ThuTuMap, 
                   ctm.ScoreTeam1, ctm.ScoreTeam2, ctm.TeamThang,
                   td.VongDau, td.NgayThiDau,
                   t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang, m.TenMap
            FROM ChiTietMap ctm
            LEFT JOIN TranDau td ON ctm.IdTran = td.IdTran
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON ctm.TeamThang = tw.IdTeam
            LEFT JOIN Map m ON ctm.IdMap = m.IdMap
            ORDER BY ctm.IdTran, ctm.ThuTuMap
        """)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdChiTiet": row.IdChiTiet,
                "IdTran": row.IdTran if row.IdTran else None,
                "IdMap": row.IdMap if row.IdMap else None,
                "TenMap": row.TenMap if row.TenMap else "",
                "ThuTuMap": row.ThuTuMap if row.ThuTuMap else 0,
                "ScoreTeam1": row.ScoreTeam1 if row.ScoreTeam1 else 0,
                "ScoreTeam2": row.ScoreTeam2 if row.ScoreTeam2 else 0,
                "TeamThang": row.TeamThang if row.TeamThang else None,
                "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
                "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
                "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
                "VongDau": row.VongDau if row.VongDau else "",
                "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ChiTietMap/GetById/<int:id_chi_tiet>', methods=['GET'])
def get_chi_tiet_map_by_id(id_chi_tiet):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT ctm.IdChiTiet, ctm.IdTran, ctm.IdMap, ctm.ThuTuMap, 
                   ctm.ScoreTeam1, ctm.ScoreTeam2, ctm.TeamThang,
                   td.VongDau, td.NgayThiDau,
                   t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang, m.TenMap
            FROM ChiTietMap ctm
            LEFT JOIN TranDau td ON ctm.IdTran = td.IdTran
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON ctm.TeamThang = tw.IdTeam
            LEFT JOIN Map m ON ctm.IdMap = m.IdMap
            WHERE ctm.IdChiTiet = ?
        """, (id_chi_tiet,))
        
        row = cursor.fetchone()
        cursor.close()

        if not row:
            return jsonify({'error': 'Chi tiết map không tồn tại'}), 404

        result = {
            "IdChiTiet": row.IdChiTiet,
            "IdTran": row.IdTran if row.IdTran else None,
            "IdMap": row.IdMap if row.IdMap else None,
            "TenMap": row.TenMap if row.TenMap else "",
            "ThuTuMap": row.ThuTuMap if row.ThuTuMap else 0,
            "ScoreTeam1": row.ScoreTeam1 if row.ScoreTeam1 else 0,
            "ScoreTeam2": row.ScoreTeam2 if row.ScoreTeam2 else 0,
            "TeamThang": row.TeamThang if row.TeamThang else None,
            "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
            "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
            "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
            "VongDau": row.VongDau if row.VongDau else "",
            "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None
        }

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ChiTietMap/GetByTran/<int:id_tran>', methods=['GET'])
def get_chi_tiet_map_by_tran(id_tran):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT ctm.IdChiTiet, ctm.IdTran, ctm.IdMap, ctm.ThuTuMap, 
                   ctm.ScoreTeam1, ctm.ScoreTeam2, ctm.TeamThang,
                   td.VongDau, td.NgayThiDau,
                   t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang, m.TenMap
            FROM ChiTietMap ctm
            LEFT JOIN TranDau td ON ctm.IdTran = td.IdTran
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON ctm.TeamThang = tw.IdTeam
            LEFT JOIN Map m ON ctm.IdMap = m.IdMap
            WHERE ctm.IdTran = ?
            ORDER BY ctm.ThuTuMap
        """, (id_tran,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdChiTiet": row.IdChiTiet,
                "IdTran": row.IdTran if row.IdTran else None,
                "IdMap": row.IdMap if row.IdMap else None,
                "TenMap": row.TenMap if row.TenMap else "",
                "ThuTuMap": row.ThuTuMap if row.ThuTuMap else 0,
                "ScoreTeam1": row.ScoreTeam1 if row.ScoreTeam1 else 0,
                "ScoreTeam2": row.ScoreTeam2 if row.ScoreTeam2 else 0,
                "TeamThang": row.TeamThang if row.TeamThang else None,
                "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
                "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
                "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
                "VongDau": row.VongDau if row.VongDau else "",
                "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ChiTietMap/Create', methods=['POST'])
def create_chi_tiet_map():
    try:
        data = request.json
        id_tran = data.get('IdTran')
        id_map = data.get('IdMap')
        thu_tu_map = data.get('ThuTuMap')
        score_team1 = data.get('ScoreTeam1', 0)
        score_team2 = data.get('ScoreTeam2', 0)
        team_thang = data.get('TeamThang')

        if not id_tran or not id_map or not thu_tu_map:
            return jsonify({'error': 'ID trận đấu, ID map và thứ tự map là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra trận đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM TranDau WHERE IdTran = ?", (id_tran,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 400

        # Kiểm tra map có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Map WHERE IdMap = ?", (id_map,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Map không tồn tại'}), 400

        # Kiểm tra team thắng có thuộc trận đấu không (nếu có)
        if team_thang:
            cursor.execute("""
                SELECT COUNT(*) FROM TranDau 
                WHERE IdTran = ? AND (Team1 = ? OR Team2 = ?)
            """, (id_tran, team_thang, team_thang))
            count = cursor.fetchone()[0]
            if count == 0:
                return jsonify({'error': 'Team thắng phải là một trong hai team thi đấu'}), 400

        # Kiểm tra thứ tự map đã tồn tại trong trận đấu này chưa
        cursor.execute("""
            SELECT COUNT(*) FROM ChiTietMap 
            WHERE IdTran = ? AND ThuTuMap = ?
        """, (id_tran, thu_tu_map))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Thứ tự map này đã tồn tại trong trận đấu'}), 400

        # Thêm chi tiết map mới
        query = """
            INSERT INTO ChiTietMap (IdTran, IdMap, ThuTuMap, ScoreTeam1, ScoreTeam2, TeamThang)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (id_tran, id_map, thu_tu_map, score_team1, score_team2, team_thang))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Tạo chi tiết map thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ChiTietMap/Update/<int:id_chi_tiet>', methods=['PUT'])
def update_chi_tiet_map(id_chi_tiet):
    try:
        data = request.json
        id_tran = data.get('IdTran')
        id_map = data.get('IdMap')
        thu_tu_map = data.get('ThuTuMap')
        score_team1 = data.get('ScoreTeam1', 0)
        score_team2 = data.get('ScoreTeam2', 0)
        team_thang = data.get('TeamThang')

        if not id_tran or not id_map or not thu_tu_map:
            return jsonify({'error': 'ID trận đấu, ID map và thứ tự map là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra chi tiết map có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM ChiTietMap WHERE IdChiTiet = ?", (id_chi_tiet,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Chi tiết map không tồn tại'}), 404

        # Kiểm tra trận đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM TranDau WHERE IdTran = ?", (id_tran,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 400

        # Kiểm tra map có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM Map WHERE IdMap = ?", (id_map,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Map không tồn tại'}), 400

        # Kiểm tra team thắng có thuộc trận đấu không (nếu có)
        if team_thang:
            cursor.execute("""
                SELECT COUNT(*) FROM TranDau 
                WHERE IdTran = ? AND (Team1 = ? OR Team2 = ?)
            """, (id_tran, team_thang, team_thang))
            count = cursor.fetchone()[0]
            if count == 0:
                return jsonify({'error': 'Team thắng phải là một trong hai team thi đấu'}), 400

        # Kiểm tra thứ tự map đã tồn tại trong trận đấu này chưa (trừ chính nó)
        cursor.execute("""
            SELECT COUNT(*) FROM ChiTietMap 
            WHERE IdTran = ? AND ThuTuMap = ? AND IdChiTiet != ?
        """, (id_tran, thu_tu_map, id_chi_tiet))
        count = cursor.fetchone()[0]
        if count > 0:
            return jsonify({'error': 'Thứ tự map này đã tồn tại trong trận đấu'}), 400

        # Cập nhật thông tin
        query = """
            UPDATE ChiTietMap 
            SET IdTran = ?, IdMap = ?, ThuTuMap = ?, ScoreTeam1 = ?, 
                ScoreTeam2 = ?, TeamThang = ?
            WHERE IdChiTiet = ?
        """
        cursor.execute(query, (id_tran, id_map, thu_tu_map, score_team1, 
                              score_team2, team_thang, id_chi_tiet))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật chi tiết map thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ChiTietMap/Delete/<int:id_chi_tiet>', methods=['DELETE'])
def delete_chi_tiet_map(id_chi_tiet):
    try:
        cursor = con.cursor()
        
        # Kiểm tra chi tiết map có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM ChiTietMap WHERE IdChiTiet = ?", (id_chi_tiet,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Chi tiết map không tồn tại'}), 404

        # Xóa chi tiết map
        cursor.execute("DELETE FROM ChiTietMap WHERE IdChiTiet = ?", (id_chi_tiet,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa chi tiết map thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ChiTietMap/UpdateScore/<int:id_chi_tiet>', methods=['PUT'])
def update_score_chi_tiet_map(id_chi_tiet):
    """Cập nhật điểm số và team thắng cho một map"""
    try:
        data = request.json
        score_team1 = data.get('ScoreTeam1', 0)
        score_team2 = data.get('ScoreTeam2', 0)

        cursor = con.cursor()
        
        # Kiểm tra chi tiết map có tồn tại không
        cursor.execute("SELECT IdTran FROM ChiTietMap WHERE IdChiTiet = ?", (id_chi_tiet,))
        row = cursor.fetchone()
        if not row:
            return jsonify({'error': 'Chi tiết map không tồn tại'}), 404

        id_tran = row.IdTran

        # Lấy thông tin team từ trận đấu
        cursor.execute("SELECT Team1, Team2 FROM TranDau WHERE IdTran = ?", (id_tran,))
        tran_row = cursor.fetchone()
        if not tran_row:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 404

        # Xác định team thắng
        team_thang = None
        if score_team1 > score_team2:
            team_thang = tran_row.Team1
        elif score_team2 > score_team1:
            team_thang = tran_row.Team2

        # Cập nhật điểm số và team thắng
        query = """
            UPDATE ChiTietMap 
            SET ScoreTeam1 = ?, ScoreTeam2 = ?, TeamThang = ?
            WHERE IdChiTiet = ?
        """
        cursor.execute(query, (score_team1, score_team2, team_thang, id_chi_tiet))
        con.commit()
        cursor.close()
        
        return jsonify({
            'message': 'Cập nhật điểm số thành công',
            'ScoreTeam1': score_team1,
            'ScoreTeam2': score_team2,
            'TeamThang': team_thang
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    # Thêm endpoint này vào file backend Python của bạn

@app.route('/ChiTietMap/GetByMap/<int:id_map>', methods=['GET'])
def get_chi_tiet_map_by_map(id_map):
    """Lấy tất cả chi tiết map theo IdMap"""
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT ctm.IdChiTiet, ctm.IdTran, ctm.IdMap, ctm.ThuTuMap, 
                   ctm.ScoreTeam1, ctm.ScoreTeam2, ctm.TeamThang,
                   td.VongDau, td.NgayThiDau, td.TrangThai,
                   t1.TenTeam as TenTeam1, t2.TenTeam as TenTeam2,
                   tw.TenTeam as TenTeamThang, m.TenMap,
                   gd.TenGiai
            FROM ChiTietMap ctm
            LEFT JOIN TranDau td ON ctm.IdTran = td.IdTran
            LEFT JOIN Team t1 ON td.Team1 = t1.IdTeam
            LEFT JOIN Team t2 ON td.Team2 = t2.IdTeam
            LEFT JOIN Team tw ON ctm.TeamThang = tw.IdTeam
            LEFT JOIN Map m ON ctm.IdMap = m.IdMap
            LEFT JOIN GiaiDau gd ON td.IdGiai = gd.IdGiai
            WHERE ctm.IdMap = ?
            ORDER BY td.NgayThiDau DESC, ctm.IdTran, ctm.ThuTuMap
        """, (id_map,))
        rows = cursor.fetchall()

        result = []
        for row in rows:
            result.append({
                "IdChiTiet": row.IdChiTiet,
                "IdTran": row.IdTran if row.IdTran else None,
                "IdMap": row.IdMap if row.IdMap else None,
                "TenMap": row.TenMap if row.TenMap else "",
                "ThuTuMap": row.ThuTuMap if row.ThuTuMap else 0,
                "ScoreTeam1": row.ScoreTeam1 if row.ScoreTeam1 else 0,
                "ScoreTeam2": row.ScoreTeam2 if row.ScoreTeam2 else 0,
                "TeamThang": row.TeamThang if row.TeamThang else None,
                "TenTeam1": row.TenTeam1 if row.TenTeam1 else "",
                "TenTeam2": row.TenTeam2 if row.TenTeam2 else "",
                "TenTeamThang": row.TenTeamThang if row.TenTeamThang else "",
                "VongDau": row.VongDau if row.VongDau else "",
                "TrangThai": row.TrangThai if row.TrangThai else "",
                "TenGiai": row.TenGiai if row.TenGiai else "",
                "NgayThiDau": row.NgayThiDau.strftime('%Y-%m-%d %H:%M:%S') if row.NgayThiDau else None
            })

        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/Map/GetStatistics/<int:id_map>', methods=['GET'])
def get_map_statistics(id_map):
    """Lấy thống kê của một map"""
    try:
        cursor = con.cursor()
        
        # Thống kê tổng quan
        cursor.execute("""
            SELECT 
                COUNT(*) as TongSoTran,
                AVG(CAST(ctm.ScoreTeam1 + ctm.ScoreTeam2 AS FLOAT)) as DiemTrungBinh,
                MAX(ctm.ScoreTeam1 + ctm.ScoreTeam2) as DiemCaoNhat,
                COUNT(CASE WHEN ctm.TeamThang IS NOT NULL THEN 1 END) as TranCoKetQua
            FROM ChiTietMap ctm
            WHERE ctm.IdMap = ?
        """, (id_map,))
        
        stats_row = cursor.fetchone()
        
        # Thống kê team thắng nhiều nhất
        cursor.execute("""
            SELECT TOP 3
                t.TenTeam,
                COUNT(*) as SoLanThang
            FROM ChiTietMap ctm
            JOIN Team t ON ctm.TeamThang = t.IdTeam
            WHERE ctm.IdMap = ?
            GROUP BY t.TenTeam, ctm.TeamThang
            ORDER BY COUNT(*) DESC
        """, (id_map,))
        
        top_teams = cursor.fetchall()
        
        cursor.close()
        
        result = {
            "TongSoTran": stats_row.TongSoTran if stats_row else 0,
            "DiemTrungBinh": round(stats_row.DiemTrungBinh, 2) if stats_row and stats_row.DiemTrungBinh else 0,
            "DiemCaoNhat": stats_row.DiemCaoNhat if stats_row else 0,
            "TranCoKetQua": stats_row.TranCoKetQua if stats_row else 0,
            "TopTeams": [
                {
                    "TenTeam": team.TenTeam,
                    "SoLanThang": team.SoLanThang
                } for team in top_teams
            ]
        }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# === CHẠY APP ===
if __name__ == '__main__':
    if con:
        app.run(debug=True)
    else:
        print("❌ Không chạy Flask do kết nối SQL thất bại.")