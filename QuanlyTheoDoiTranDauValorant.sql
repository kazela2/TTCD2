
CREATE DATABASE QL_GIAIDAU_VALORANT
USE QL_GIAIDAU_VALORANT

-- Bảng QuanTri
CREATE TABLE QuanTri (
    IdQuanTri INT PRIMARY KEY IDENTITY(1,1),
    TenDangNhap VARCHAR(50) NOT NULL UNIQUE,
    MatKhau VARCHAR(255) NOT NULL,
    HoTen NVARCHAR(100) NOT NULL,
    VaiTro VARCHAR(50) DEFAULT 'Admin', -- 'Admin', 'Moderator'
    MoTa NTEXT
);

-- Bảng GiaiDau
CREATE TABLE GiaiDau (
    IdGiai INT PRIMARY KEY IDENTITY(1,1),
    TenGiai NVARCHAR(100) NOT NULL,
    NgayBatDau DATE,
    NgayKetThuc DATE,
    SoTeamThamGia INT DEFAULT 0,
    GiaiThuong DECIMAL(15,2),
    HinhAnh VARCHAR(255),
    MoTa NTEXT
);

-- Bảng Team
CREATE TABLE Team (
    IdTeam INT PRIMARY KEY IDENTITY(1,1),
    TenTeam NVARCHAR(100) NOT NULL,
    TenCaptain NVARCHAR(100),
    EmailLienHe VARCHAR(100),
    Logo VARCHAR(255),
    IdGiai INT,
    NgayDangKy DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (IdGiai) REFERENCES GiaiDau(IdGiai) ON DELETE CASCADE
);

-- Bảng Player
CREATE TABLE Player (
    IdPlayer INT PRIMARY KEY IDENTITY(1,1),
    GameName NVARCHAR(50) NOT NULL,
    TagLine VARCHAR(10), -- #VN1, #NA1, etc.
    HoTenThat NVARCHAR(100),
    ViTri NVARCHAR(30), -- Duelist, Controller, Initiator, Sentinel, IGL
    RankHienTai NVARCHAR(30), -- Iron → Radiant
    MainAgent NVARCHAR(30), -- Jett, Sage, Sova, Omen, etc.
    IdTeam INT,
    FOREIGN KEY (IdTeam) REFERENCES Team(IdTeam) ON DELETE CASCADE
);

-- Bảng TranDau
CREATE TABLE TranDau (
    IdTran INT PRIMARY KEY IDENTITY(1,1),
    IdGiai INT,
    Team1 INT,
    Team2 INT,
    TiSoTeam1 INT DEFAULT 0,
    TiSoTeam2 INT DEFAULT 0,
    NgayThiDau DATETIME,
    VongDau NVARCHAR(50), 
    TrangThai NVARCHAR(20) DEFAULT N'Chưa diễn ra',
    TeamThang INT,
    GhiChu NTEXT,
    FOREIGN KEY (IdGiai) REFERENCES GiaiDau(IdGiai),
    FOREIGN KEY (Team1) REFERENCES Team(IdTeam),
    FOREIGN KEY (Team2) REFERENCES Team(IdTeam),
    FOREIGN KEY (TeamThang) REFERENCES Team(IdTeam)
);

-- Bảng Map
CREATE TABLE Map (
    IdMap INT PRIMARY KEY IDENTITY(1,1),
    TenMap VARCHAR(50) NOT NULL, -- Bind, Haven, Split, Ascent, etc.
    TrangThai BIT DEFAULT 1
);

-- Bảng ChiTietMap (kết quả từng map)
CREATE TABLE ChiTietMap (
    IdChiTiet INT PRIMARY KEY IDENTITY(1,1),
    IdTran INT,
    IdMap INT,
    ThuTuMap INT, -- Map 1, 2, 3...
    ScoreTeam1 INT DEFAULT 0, -- Số round thắng
    ScoreTeam2 INT DEFAULT 0,
    TeamThang INT,
    FOREIGN KEY (IdTran) REFERENCES TranDau(IdTran),
    FOREIGN KEY (IdMap) REFERENCES Map(IdMap),
    FOREIGN KEY (TeamThang) REFERENCES Team(IdTeam)
);

-- Bảng BangXepHang
CREATE TABLE BangXepHang (
    IdXH INT PRIMARY KEY IDENTITY(1,1),
    IdGiai INT,
    IdTeam INT,
    TranDa INT DEFAULT 0,
    TranThang INT DEFAULT 0,
    TranThua INT DEFAULT 0,
    MapThang INT DEFAULT 0,
    MapThua INT DEFAULT 0,
    Diem INT DEFAULT 0,
    HangHienTai INT,
    FOREIGN KEY (IdGiai) REFERENCES GiaiDau(IdGiai),
    FOREIGN KEY (IdTeam) REFERENCES Team(IdTeam)
);



-- Thêm dữ liệu map Valorant
INSERT INTO Map (TenMap) VALUES 
('Bind'), ('Haven'), ('Split'), ('Ascent'), 
('Icebox'), ('Breeze'), ('Fracture'), ('Pearl'), 
('Lotus'), ('Sunset');

-- Tạo một số indexes cơ bản
CREATE INDEX IX_TranDau_NgayThiDau ON TranDau(NgayThiDau);
CREATE INDEX IX_Team_TenTeam ON Team(TenTeam);
CREATE INDEX IX_Player_GameName ON Player(GameName);

