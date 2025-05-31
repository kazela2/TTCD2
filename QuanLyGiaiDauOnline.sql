CREATE DATABASE QL_GIAIDAUONLINE
USE QL_GIAIDAUONLINE

-- B?ng GiaiDau
CREATE TABLE GiaiDau (
    IdGiai INT PRIMARY KEY IDENTITY(1,1),
    TenGiai VARCHAR(100) NOT NULL,
    NgayBatDau DATE,
    NgayKetThuc DATE,
    MoTa TEXT
);

-- B?ng DoiThiDau
CREATE TABLE DoiThiDau (
    IdDoi INT PRIMARY KEY IDENTITY(1,1),
    TenDoi VARCHAR(100) NOT NULL,
    TenHuanLuyenVien VARCHAR(100),
    IdGiai INT NULL,
    FOREIGN KEY (IdGiai) REFERENCES GiaiDau(IdGiai) ON DELETE CASCADE
);


-- B?ng ThanhVienDoi
CREATE TABLE ThanhVienDoi (
    IdThanhVien INT PRIMARY KEY IDENTITY(1,1),
    HoTen VARCHAR(100) NOT NULL,
    ViTri VARCHAR(50),
    SoAo INT,
    IdDoi INT,
    FOREIGN KEY (IdDoi) REFERENCES DoiThiDau(IdDoi) ON DELETE CASCADE
);


-- B?ng TranDau
CREATE TABLE TranDau (
    IdTran INT PRIMARY KEY IDENTITY(1,1),
    IdGiai INT,
    Doi1 INT,
    Doi2 INT,
    TySo VARCHAR(10),
    NgayThiDau DATE,
    DiaDiem VARCHAR(100),
    FOREIGN KEY (IdGiai) REFERENCES GiaiDau(IdGiai),
    FOREIGN KEY (Doi1) REFERENCES DoiThiDau(IdDoi),
    FOREIGN KEY (Doi2) REFERENCES DoiThiDau(IdDoi)
);
select * from TranDau
-- B?ng BangXepHang
CREATE TABLE BangXepHang (
    Idxh INT PRIMARY KEY IDENTITY(1,1),
    IdGiai INT,
    IdDoi INT,
    TranThang INT DEFAULT 0,
    TranThua INT DEFAULT 0,
    TranHoa INT DEFAULT 0,
    Diem INT DEFAULT 0,
    HieuSo INT DEFAULT 0,
    FOREIGN KEY (IdGiai) REFERENCES GiaiDau(IdGiai),
    FOREIGN KEY (IdDoi) REFERENCES DoiThiDau(IdDoi)
);

-- B?ng LichSuGiaiDau
CREATE TABLE LichSuGiaiDau (
    Idls INT PRIMARY KEY IDENTITY(1,1),
    IdGiai INT,
    Nam INT,
    DoiVoDich INT,
    MoTa TEXT,
    FOREIGN KEY (IdGiai) REFERENCES GiaiDau(IdGiai),
    FOREIGN KEY (DoiVoDich) REFERENCES DoiThiDau(IdDoi)
);


INSERT INTO GiaiDau (TenGiai, NgayBatDau, NgayKetThuc, MoTa) VALUES
('Giải Đấu Mùa Hè 2025', '2025-06-01', '2025-06-30', 'Giải đấu lớn diễn ra vào mùa hè năm 2025.'),
('Giải Đấu Mùa Đông 2025', '2025-12-01', '2025-12-20', 'Giải đấu mùa đông với nhiều đội tuyển mạnh tham gia.');
select * from GiaiDau
select * from DoiThiDau
select * from ThanhVienDoi

