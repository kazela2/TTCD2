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

@app.route('/BangXepHang/GetAll', methods=['GET'])
def get_bang_xep_hang():
    cursor = con.cursor()
    cursor.execute("""
        SELECT bxh.Idxh, dt.TenDoi, gd.TenGiai, bxh.TranThang, bxh.TranHoa, bxh.TranThua, bxh.Diem, bxh.HieuSo
        FROM BangXepHang bxh
        JOIN DoiThiDau dt ON bxh.IdDoi = dt.IdDoi
        JOIN GiaiDau gd ON bxh.IdGiai = gd.IdGiai
        ORDER BY bxh.Diem DESC, bxh.HieuSo DESC
    """)
    rows = cursor.fetchall()

    result = []
    for row in rows:
        result.append({
            "Idxh": row.Idxh,
            "TenDoi": row.TenDoi,
            "TenGiai": row.TenGiai,
            "TranThang": row.TranThang,
            "TranHoa": row.TranHoa,
            "TranThua": row.TranThua,
            "Diem": row.Diem,
            "HieuSo": row.HieuSo
        })

    return jsonify(result)

@app.route('/BangXepHang/Add', methods=['POST'])
def them_bang_xep_hang():
    try:
        data = request.json
        doi_id = data.get('IdDoi')
        giai_id = data.get('IdGiai')
        tran_thang = data.get('TranThang', 0)
        tran_hoa = data.get('TranHoa', 0)
        tran_thua = data.get('TranThua', 0)
        hieu_so = data.get('HieuSo', 0)
        diem = data.get('Diem', 0)

        if not doi_id or not giai_id:
            return jsonify({'error': 'IdDoi và IdGiai là bắt buộc'}), 400

        cursor = con.cursor()
        query = """
            INSERT INTO BangXepHang (IdDoi, IdGiai, TranThang, TranHoa, TranThua, HieuSo, Diem)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (doi_id, giai_id, tran_thang, tran_hoa, tran_thua, hieu_so, diem))
        con.commit()
        cursor.close()
        return jsonify({'message': '✅ Thêm bảng xếp hạng thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/BangXepHang/Delete/<int:id>', methods=['DELETE'])
def xoa_bang_xep_hang(id):
    try:
        cursor = con.cursor()
        # Kiểm tra xem id có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM BangXepHang WHERE Idxh = %s", (id,))
        (count,) = cursor.fetchone()
        if count == 0:
            return jsonify({"error": "Bản ghi không tồn tại"}), 404

        # Xóa bản ghi
        cursor.execute("DELETE FROM BangXepHang WHERE Idxh = %s", (id,))
        con.commit()
        return jsonify({"message": "Xóa thành công"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


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

@app.route('/GiaiDau/Delete/<int:id_giai>', methods=['DELETE'])
def xoa_giai_dau(id_giai):
    try:
        cursor = con.cursor()
        # Kiểm tra xem giải đấu có tồn tại không
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


# Lấy tất cả trận đấu kèm thông tin đội và giải đấu
@app.route('/TranDau/GetAll', methods=['GET'])
def get_all_tran_dau():
    cursor = con.cursor()
    cursor.execute("""
        SELECT 
            td.IdTran, 
            td.IdGiai, 
            g.TenGiai,
            td.Doi1, 
            d1.TenDoi AS TenDoi1,
            td.Doi2, 
            d2.TenDoi AS TenDoi2,
            td.TySo, 
            td.NgayThiDau, 
            td.DiaDiem
        FROM TranDau td
        LEFT JOIN GiaiDau g ON td.IdGiai = g.IdGiai
        LEFT JOIN DoiThiDau d1 ON td.Doi1 = d1.IdDoi
        LEFT JOIN DoiThiDau d2 ON td.Doi2 = d2.IdDoi
        ORDER BY td.NgayThiDau DESC
    """)
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append({
            'IdTran': row.IdTran,
            'IdGiai': row.IdGiai,
            'TenGiai': row.TenGiai,
            'Doi1': row.Doi1,
            'TenDoi1': row.TenDoi1,
            'Doi2': row.Doi2,
            'TenDoi2': row.TenDoi2,
            'TySo': row.TySo if row.TySo else "",
            'NgayThiDau': row.NgayThiDau.strftime('%Y-%m-%d') if row.NgayThiDau else None,
            'DiaDiem': row.DiaDiem if row.DiaDiem else ""
        })
    
    return jsonify(result)


# Lấy trận đấu theo giải đấu
@app.route('/TranDau/GetByGiai/<int:id_giai>', methods=['GET'])
def get_tran_dau_by_giai(id_giai):
    cursor = con.cursor()
    cursor.execute("""
        SELECT 
            td.IdTran, 
            td.IdGiai, 
            g.TenGiai,
            td.Doi1, 
            d1.TenDoi AS TenDoi1,
            td.Doi2, 
            d2.TenDoi AS TenDoi2,
            td.TySo, 
            td.NgayThiDau, 
            td.DiaDiem
        FROM TranDau td
        LEFT JOIN GiaiDau g ON td.IdGiai = g.IdGiai
        LEFT JOIN DoiThiDau d1 ON td.Doi1 = d1.IdDoi
        LEFT JOIN DoiThiDau d2 ON td.Doi2 = d2.IdDoi
        WHERE td.IdGiai = ?
        ORDER BY td.NgayThiDau DESC
    """, (id_giai,))
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append({
            'IdTran': row.IdTran,
            'IdGiai': row.IdGiai,
            'TenGiai': row.TenGiai,
            'Doi1': row.Doi1,
            'TenDoi1': row.TenDoi1,
            'Doi2': row.Doi2,
            'TenDoi2': row.TenDoi2,
            'TySo': row.TySo if row.TySo else "",
            'NgayThiDau': row.NgayThiDau.strftime('%Y-%m-%d') if row.NgayThiDau else None,
            'DiaDiem': row.DiaDiem if row.DiaDiem else ""
        })
    
    return jsonify(result)


# Thêm trận đấu mới
@app.route('/TranDau/Add', methods=['POST'])
def add_tran_dau():
    try:
        data = request.json
        id_giai = data.get('IdGiai')
        doi1 = data.get('Doi1')
        doi2 = data.get('Doi2')
        ty_so = data.get('TySo', '')
        ngay_thi_dau = data.get('NgayThiDau')  # 'YYYY-MM-DD'
        dia_diem = data.get('DiaDiem', '')

        if not id_giai or not doi1 or not doi2:
            return jsonify({'error': 'IdGiai, Doi1 và Doi2 là bắt buộc'}), 400
        
        if doi1 == doi2:
            return jsonify({'error': 'Hai đội không thể giống nhau'}), 400

        cursor = con.cursor()
        
        # Kiểm tra xem các đội có tồn tại và thuộc giải đấu này không
        cursor.execute("""
            SELECT COUNT(*) FROM DoiThiDau 
            WHERE IdDoi IN (?, ?) AND IdGiai = ?
        """, (doi1, doi2, id_giai))
        count = cursor.fetchone()[0]
        
        if count != 2:
            return jsonify({'error': 'Một hoặc cả hai đội không thuộc giải đấu này'}), 400

        # Thêm trận đấu
        query = """
            INSERT INTO TranDau (IdGiai, Doi1, Doi2, TySo, NgayThiDau, DiaDiem)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (id_giai, doi1, doi2, ty_so, ngay_thi_dau, dia_diem))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Thêm trận đấu thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Cập nhật tỷ số trận đấu
@app.route('/TranDau/UpdateScore/<int:id_tran>', methods=['PUT'])
def update_ty_so(id_tran):
    try:
        data = request.json
        ty_so = data.get('TySo')
        
        if not ty_so:
            return jsonify({'error': 'Tỷ số là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra trận đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM TranDau WHERE IdTran = ?", (id_tran,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 404

        # Cập nhật tỷ số
        cursor.execute("UPDATE TranDau SET TySo = ? WHERE IdTran = ?", (ty_so, id_tran))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật tỷ số thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Cập nhật thông tin trận đấu
@app.route('/TranDau/Update/<int:id_tran>', methods=['PUT'])
def update_tran_dau(id_tran):
    try:
        data = request.json
        ty_so = data.get('TySo')
        ngay_thi_dau = data.get('NgayThiDau')
        dia_diem = data.get('DiaDiem')

        cursor = con.cursor()
        
        # Kiểm tra trận đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM TranDau WHERE IdTran = ?", (id_tran,))
        count = cursor.fetchone()[0]
        if count == 0:
            return jsonify({'error': 'Trận đấu không tồn tại'}), 404

        # Cập nhật thông tin
        query = """
            UPDATE TranDau 
            SET TySo = ?, NgayThiDau = ?, DiaDiem = ?
            WHERE IdTran = ?
        """
        cursor.execute(query, (ty_so, ngay_thi_dau, dia_diem, id_tran))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật trận đấu thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Xóa trận đấu
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


# Lấy danh sách đội theo giải đấu (để hiển thị trong dropdown)
@app.route('/DoiThiDau/GetByGiai/<int:id_giai>', methods=['GET'])
def get_doi_by_giai(id_giai):
    cursor = con.cursor()
    cursor.execute("""
        SELECT IdDoi, TenDoi, TenHuanLuyenVien
        FROM DoiThiDau 
        WHERE IdGiai = ?
        ORDER BY TenDoi
    """, (id_giai,))
    rows = cursor.fetchall()
    
    result = []
    for row in rows:
        result.append({
            'IdDoi': row.IdDoi,
            'TenDoi': row.TenDoi,
            'TenHuanLuyenVien': row.TenHuanLuyenVien
        })
    
    return jsonify(result)


@app.route('/LichSuGiaiDau/GetAll', methods=['GET'])
def get_all_lich_su():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT 
                ls.Idls, 
                ls.IdGiai, 
                g.TenGiai,
                ls.Nam, 
                ls.DoiVoDich, 
                d.TenDoi AS TenDoiVoDich,
                ls.MoTa
            FROM LichSuGiaiDau ls
            LEFT JOIN GiaiDau g ON ls.IdGiai = g.IdGiai
            LEFT JOIN DoiThiDau d ON ls.DoiVoDich = d.IdDoi
            ORDER BY ls.Nam DESC
        """)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'Idls': row.Idls,
                'IdGiai': row.IdGiai,
                'TenGiai': row.TenGiai,
                'Nam': row.Nam,
                'DoiVoDich': row.DoiVoDich,
                'TenDoiVoDich': row.TenDoiVoDich,
                'MoTa': row.MoTa if row.MoTa else ""
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
@app.route('/LichSuGiaiDau/GetByGiai/<int:id_giai>', methods=['GET'])
def get_lich_su_by_giai(id_giai):
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT 
                ls.Idls, 
                ls.IdGiai, 
                g.TenGiai,
                ls.Nam, 
                ls.DoiVoDich, 
                d.TenDoi AS TenDoiVoDich,
                ls.MoTa
            FROM LichSuGiaiDau ls
            LEFT JOIN GiaiDau g ON ls.IdGiai = g.IdGiai
            LEFT JOIN DoiThiDau d ON ls.DoiVoDich = d.IdDoi
            WHERE ls.IdGiai = ?
            ORDER BY ls.Nam DESC
        """, (id_giai,))
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'Idls': row.Idls,
                'IdGiai': row.IdGiai,
                'TenGiai': row.TenGiai,
                'Nam': row.Nam,
                'DoiVoDich': row.DoiVoDich,
                'TenDoiVoDich': row.TenDoiVoDich,
                'MoTa': row.MoTa if row.MoTa else ""
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/LichSuGiaiDau/ThongKe', methods=['GET'])
def thong_ke_lich_su():
    try:
        cursor = con.cursor()
        cursor.execute("""
            SELECT 
                d.TenDoi,
                COUNT(ls.DoiVoDich) AS SoLanVoDich,
                MIN(ls.Nam) AS NamDauTien,
                MAX(ls.Nam) AS NamGanNhat
            FROM LichSuGiaiDau ls
            JOIN DoiThiDau d ON ls.DoiVoDich = d.IdDoi
            GROUP BY d.IdDoi, d.TenDoi
            ORDER BY SoLanVoDich DESC, NamGanNhat DESC
        """)
        rows = cursor.fetchall()
        
        result = []
        for row in rows:
            result.append({
                'TenDoi': row.TenDoi,
                'SoLanVoDich': row.SoLanVoDich,
                'NamDauTien': row.NamDauTien,
                'NamGanNhat': row.NamGanNhat
            })
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    
# Thêm lịch sử giải đấu mới
@app.route('/LichSuGiaiDau/Add', methods=['POST'])
def add_lich_su():
    try:
        data = request.json
        id_giai = data.get('IdGiai')
        nam = data.get('Nam')
        doi_vo_dich = data.get('DoiVoDich')
        mo_ta = data.get('MoTa', '')

        if not id_giai or not nam or not doi_vo_dich:
            return jsonify({'error': 'IdGiai, Nam và DoiVoDich là bắt buộc'}), 400

        cursor = con.cursor()
        
        # Kiểm tra giải đấu có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM GiaiDau WHERE IdGiai = ?", (id_giai,))
        if cursor.fetchone()[0] == 0:
            return jsonify({'error': 'Giải đấu không tồn tại'}), 404
            
        # Kiểm tra đội có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM DoiThiDau WHERE IdDoi = ?", (doi_vo_dich,))
        if cursor.fetchone()[0] == 0:
            return jsonify({'error': 'Đội không tồn tại'}), 404
            
        # Kiểm tra đã có lịch sử cho giải và năm này chưa
        cursor.execute("""
            SELECT COUNT(*) FROM LichSuGiaiDau 
            WHERE IdGiai = ? AND Nam = ?
        """, (id_giai, nam))
        if cursor.fetchone()[0] > 0:
            return jsonify({'error': 'Đã có lịch sử cho giải đấu này trong năm ' + str(nam)}), 400

        # Thêm lịch sử
        cursor.execute("""
            INSERT INTO LichSuGiaiDau (IdGiai, Nam, DoiVoDich, MoTa)
            VALUES (?, ?, ?, ?)
        """, (id_giai, nam, doi_vo_dich, mo_ta))
        con.commit()
        cursor.close()

        return jsonify({'message': 'Thêm lịch sử giải đấu thành công'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Cập nhật lịch sử giải đấu
@app.route('/LichSuGiaiDau/Update/<int:id_ls>', methods=['PUT'])
def update_lich_su(id_ls):
    try:
        data = request.json
        nam = data.get('Nam')
        doi_vo_dich = data.get('DoiVoDich')
        mo_ta = data.get('MoTa', '')

        cursor = con.cursor()
        
        # Kiểm tra lịch sử có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM LichSuGiaiDau WHERE Idls = ?", (id_ls,))
        if cursor.fetchone()[0] == 0:
            return jsonify({'error': 'Lịch sử không tồn tại'}), 404
            
        # Kiểm tra đội có tồn tại không (nếu có cập nhật)
        if doi_vo_dich:
            cursor.execute("SELECT COUNT(*) FROM DoiThiDau WHERE IdDoi = ?", (doi_vo_dich,))
            if cursor.fetchone()[0] == 0:
                return jsonify({'error': 'Đội không tồn tại'}), 404

        # Cập nhật
        updates = []
        params = []
        
        if nam is not None:
            updates.append("Nam = ?")
            params.append(nam)
        if doi_vo_dich is not None:
            updates.append("DoiVoDich = ?")
            params.append(doi_vo_dich)
        if mo_ta is not None:
            updates.append("MoTa = ?")
            params.append(mo_ta)
            
        if not updates:
            return jsonify({'error': 'Không có dữ liệu để cập nhật'}), 400
            
        params.append(id_ls)
        query = f"UPDATE LichSuGiaiDau SET {', '.join(updates)} WHERE Idls = ?"
        
        cursor.execute(query, params)
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Cập nhật lịch sử thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# Xóa lịch sử giải đấu
@app.route('/LichSuGiaiDau/Delete/<int:id_ls>', methods=['DELETE'])
def delete_lich_su(id_ls):
    try:
        cursor = con.cursor()
        
        # Kiểm tra lịch sử có tồn tại không
        cursor.execute("SELECT COUNT(*) FROM LichSuGiaiDau WHERE Idls = ?", (id_ls,))
        if cursor.fetchone()[0] == 0:
            return jsonify({'error': 'Lịch sử không tồn tại'}), 404

        # Xóa lịch sử
        cursor.execute("DELETE FROM LichSuGiaiDau WHERE Idls = ?", (id_ls,))
        con.commit()
        cursor.close()
        
        return jsonify({'message': 'Xóa lịch sử thành công'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
# === CHẠY APP ===
if __name__ == '__main__':
    if con:
        app.run(debug=True)
    else:
        print("❌ Không chạy Flask do kết nối SQL thất bại.")

