# Movie Linked Data — hướng dẫn project Semantic Web

Tài liệu được lập ngày 06/10/2026 từ đề môn học trong `../theory`, mã nguồn và 94 commit của `../Movie-Knowledge-Graph` (HEAD `e9e50af`).

**Mục tiêu:** tự xây dựng một movie knowledge graph, có ontology, pipeline chuyển dữ liệu thành RDF, liên kết với knowledge graph bên ngoài, truy vấn và bằng chứng đáp ứng Linked Open Data 5★.

Đã có bước chuẩn bị dữ liệu: `scripts/tmdb.py` đọc hai CSV của **TMDB 5000 Movie Dataset trên Kaggle**, làm sạch và xuất các bảng trong `data/`. Các bước RDF, ontology, reasoning và linking trong lộ trình vẫn là phần cần hiện thực.

## Chuẩn bị dữ liệu phim

Tải và giải nén `tmdb_5000_movies.csv` cùng `tmdb_5000_credits.csv` từ [dataset Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata/data) vào `data/raw/`.

Chạy từ thư mục `semantic-web`:

```powershell
python scripts/tmdb.py
```

Mặc định lấy 100 phim đầu theo thứ tự file nguồn, tối đa 10 cast mỗi phim, cùng crew có job Director, Writer, Screenplay hoặc Producer. Script chỉ dùng thư viện chuẩn Python; không cần API key hay cài package.

```powershell
python scripts/tmdb.py --limit 200
python scripts/tmdb.py --limit 0 --cast-limit 0
```

`0` nghĩa là giữ toàn bộ phim/cast. Các CSV đầu ra cùng tên trong `data/` được ghi lại khi chạy; hai file nguồn trong `data/raw/` được giữ nguyên. Đường dẫn mặc định tính theo vị trí script nên cũng chạy được từ thư mục khác.

Đọc [Quy trình chuẩn bị và làm sạch dữ liệu](docs/DATA_PREPARATION.md) để xem schema, các lựa chọn khác repo mẫu, cách chạy và nội dung dùng cho report. Chưa chạy trên hai file Kaggle thật; bạn sẽ tải dữ liệu và chạy bước này.

## Lộ trình project

1. Đọc [Hướng dẫn từng bước](docs/HUONG_DAN_5_SAO.md) để bắt đầu và kiểm tra đầu ra sau mỗi bước.
2. Đọc [Phân tích repo và lịch sử commit](docs/PHAN_TICH_REPO_MAU.md) để biết nên học gì và cần sửa gì so với mẫu.
3. Dùng [Bản đồ lý thuyết](docs/LY_THUYET_AP_DUNG.md) khi học RDF/RDFS/OWL, thực hành Protégé và chuẩn bị bảo vệ.

Yêu cầu gốc: `../theory/20261-IT6390E.xlsx`, sheet **Capstone Project**, C4:C8. Sản phẩm nộp ở D3: **slide, report ≤15 trang, video 3–5 phút**. Đây là yêu cầu trong bản tài liệu local; chưa có rubric điểm chi tiết hay xác nhận cập nhật từ giảng viên.

**Việc đầu tiên:** viết 10 câu hỏi mà graph phải trả lời, chốt nguồn dữ liệu và chọn 20 phim làm tập thử. Sau khi pipeline chạy xuyên suốt mới tăng lên khoảng 100–300 phim. Quy mô này là đề xuất thực hành, không phải ngưỡng do thầy quy định.
