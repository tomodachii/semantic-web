# Chuẩn bị dữ liệu TMDB 5000 từ Kaggle

## 1. Nguồn và trạng thái thực hiện

Nguồn do nhóm chọn: [TMDB 5000 Movie Dataset — Kaggle](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata/data).

- [tmdb_5000_movies.csv](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata/data?select=tmdb_5000_movies.csv): metadata phim và các danh sách genre, company, country, language.
- [tmdb_5000_credits.csv](https://www.kaggle.com/datasets/tmdb/tmdb-movie-metadata/data?select=tmdb_5000_credits.csv): movie ID, title, cast và crew.

Script: `../scripts/tmdb.py`. Ngày hiện thực: 06/10/2026. Script dùng thư viện chuẩn Python (`csv`, `json`, `argparse`, `decimal`, ...); không gọi TMDB API, không tải dataset tự động, không cần API key. Tên `tmdb.py` giữ gần project tham chiếu, nhưng đầu vào là snapshot CSV đã tải từ Kaggle.

**Trạng thái:** đã kiểm tra bằng fixture nhỏ do test tạo; chưa đọc hoặc chạy trên hai CSV Kaggle thật vì chúng chưa có trong project tại thời điểm viết. Chưa có số liệu thực nghiệm của dataset mới. Những CSV đang có sẵn trong `data/` không phải kết quả của script mới trong lần làm việc này.

Khi tải dataset, ghi thêm version/ngày tải và thông tin license hiển thị trên Kaggle. Thời điểm xử lý trong summary không phải thời điểm TMDB thu thập metadata. Không tự gán giấy phép mới cho dữ liệu nguồn.

## 2. Cách chạy

Tải và giải nén hai file vào:

```text
semantic-web/data/raw/tmdb_5000_movies.csv
semantic-web/data/raw/tmdb_5000_credits.csv
```

Từ `semantic-web`:

```powershell
python scripts/tmdb.py
```

Mặc định: 100 phim đầu tiên **theo thứ tự file movies nguồn**, tối đa 10 cast theo `order`, crew gồm Director/Writer/Screenplay/Producer.

```powershell
# Prepare a different number of films.
python scripts/tmdb.py --limit 200

# Keep every film and every cast member.
python scripts/tmdb.py --limit 0 --cast-limit 0

# Read downloaded files from another directory.
python scripts/tmdb.py --input-dir "C:\Downloads\tmdb" --limit 100

# Write a separate output snapshot.
python scripts/tmdb.py --output-dir data/run-01 --limit 100
```

Nếu chưa có file đầu vào, script báo lỗi chỉ rõ file thiếu. Chạy mặc định sẽ ghi lại các bảng cùng tên trong `data/`; để giữ bộ CSV đang có, dùng `--output-dir data/run-01`. Không sửa hai raw CSV. Khi có lỗi nội dung trong quá trình chuẩn bị, script dừng trước bước ghi các CSV đầu ra.

Chọn 100 phim đầu giúp thao tác đơn giản và tái lập trên cùng snapshot. Đây không phải lấy ngẫu nhiên hay bảo đảm top popular; không diễn giải tập này là đại diện cho toàn bộ điện ảnh. Muốn đổi cách chọn mẫu sau này phải ghi rõ tiêu chí mới.

## 3. Chọn thông tin nào, khác mẫu ở đâu?

Repo mẫu lấy một phần thông tin qua API: metadata cơ bản, top 10 cast, director, genre/company/country/language. Họ không lấy toàn bộ fields API.

Project này giữ phần cốt lõi đó và thêm một ít thông tin hữu ích cho ontology:

| Quyết định | Lý do |
|---|---|
| Thêm `original_title`, `budget`, `revenue`, `status` | Mô tả phim đầy đủ hơn; cho phép câu hỏi về tài chính và trạng thái |
| Giữ Writer, Screenplay, Producer cùng Director | Mô hình hóa một người làm nhiều công việc trong những phim khác nhau |
| Thêm `people.csv` dùng chung | Một person ID chỉ có một thực thể, dùng cho cả cast và crew |
| Giữ `credit_id` và crew `department` | Làm khóa/thông tin của lần tham gia một phim thay vì gắn job lên Person vĩnh viễn |
| Giữ character và cast order | Có thể tạo CastCredit/ActingRole trong OWL |
| Bỏ keywords, homepage, tagline, popularity, gender | Giữ phạm vi nhỏ, tập trung vào quan hệ cần cho semantic queries |

Schema TMDB 5000 được kỳ vọng **không có IMDb ID và country của production company**. Vì vậy script không tạo `imdb_id` giả hay suy ra company country từ production country của phim. Các cột không tồn tại được phát hiện qua kiểm tra header lúc chạy.

Hệ quả cho phần sau:

- Linking có thể dùng TMDB ID + title/year làm chứng cứ và duyệt trường hợp mơ hồ; không áp dụng nguyên điều kiện bắt buộc IMDb ID của một thiết kế khác.
- Không dùng chain Movie→Company→CompanyCountry khi nguồn chưa có company country. Có thể demo inverse Movie–Director, hoặc thiết kế chain Movie→Credit→Person; phải thống nhất ontology trước khi transform RDF.
- Budget/revenue chỉ phục vụ query số liệu. `revenue > budget` không tự chứng minh phim có lãi vì còn các chi phí khác và phần doanh thu phân chia.

## 4. Các bảng đầu ra

12 CSV UTF-8, các quan hệ dùng ID để join:

| File | Cột |
|---|---|
| `movies.csv` | id, title, original_title, overview, original_language, release_date, runtime, vote_average, vote_count, budget, revenue, status |
| `people.csv` | id, name |
| `cast.csv` | movie_id, person_id, person_name, character, order, credit_id |
| `crew.csv` | movie_id, person_id, person_name, job, department, credit_id |
| `genres.csv` | id, name |
| `companies.csv` | id, name |
| `countries.csv` | country_code, name |
| `languages.csv` | language_code, name |
| `movie_genres.csv` | movie_id, genre_id |
| `movie_companies.csv` | movie_id, company_id |
| `movie_countries.csv` | movie_id, country_code |
| `movie_languages.csv` | movie_id, language_code |

Các đơn vị kỳ vọng từ nguồn: runtime là phút, vote_average thang 0–10, budget/revenue là số tiền USD. Đối chiếu mô tả source/version đã tải trước khi chốt vào báo cáo. Language name lấy nguyên trường `name`; có thể không phải tên tiếng Anh.

`movie_languages.csv` mô tả các spoken languages được ghi trong nguồn. `movies.original_language` là ngôn ngữ gốc và không được tự thêm vào spoken languages. Nếu mã original language chưa có trong lookup, script thêm mã với tên trống; không bịa tên hay dịch bằng suy đoán.

`person_name` trong cast/crew giữ để dễ đọc và tương tự mẫu; khi tạo RDF, dùng `person_id` làm khóa. Có thể cùng tên nhưng khác ID. `people.csv` giữ tên từ lần xuất hiện đầu trong phần credits đã chọn, trong khi các bảng credit giữ tên theo nguồn của từng credit.

## 5. Quy trình lấy và làm sạch

1. **Đọc file:** dùng `csv.DictReader`, chấp nhận UTF-8 BOM, kiểm tra các cột cần dùng. Cho phép ô JSON dài đến 10 triệu ký tự để đọc crew lists.
2. **Định danh:** chuẩn hóa movie/person/entity numeric ID thành số nguyên dương biểu diễn dưới dạng chuỗi. Credits ghép với movie qua `movies.id = credits.movie_id`, không ghép theo title hoặc vị trí dòng.
3. **Loại movie ID trùng:** duplicate row giống hệt được giữ một lần và đếm trong summary. Cùng ID nhưng hai row khác nhau thì dừng để kiểm tra, không âm thầm chọn một bản.
4. **Chọn tập phim:** lấy tối đa `--limit` movie ID khác nhau đầu file. `--limit 0` giữ tất cả. Giữ metadata của phim không tìm thấy credits và thống kê trường hợp đó.
5. **Chuẩn hóa văn bản:** bỏ khoảng trắng đầu/cuối, giữ nguyên chữ hoa/thường, Unicode, tên và khoảng trắng bên trong. `None` hoặc ô thiếu được biểu diễn bằng chuỗi trống.
6. **Chuẩn hóa số:** Decimal giúp kiểm tra chính xác; integer field như runtime/budget/revenue/vote_count nhận cả `120.0` nhưng chỉ khi giá trị nguyên. Số âm, NaN, Infinity và giá trị sai kiểu gây lỗi. Vote average phải trong 0–10.
7. **Xử lý zero:** runtime/budget/revenue bằng 0 chuyển thành ô trống theo chính sách coi zero là thiếu thông tin trong bản chuẩn hóa. Giữ zero gốc trong raw để truy vết; đây là giả định làm sạch, không khẳng định mọi zero thực sự là missing. Vote count bằng 0 được giữ, còn vote average của phim không có votes được để trống. Cast order 0 vẫn được giữ vì đây là vị trí đầu tiên hợp lệ.
8. **Ngày:** ngày không rỗng phải parse được thành ngày ISO `YYYY-MM-DD`, rồi xuất lại dạng chuẩn. Không có ngày thì để trống; không tự thêm ngày/tháng.
9. **Danh sách JSON:** genres/companies/countries/languages/cast/crew phải là JSON list chứa object. Dùng `json.loads`, không dùng `eval`. JSON sai thì báo movie ID và field liên quan; không bỏ qua âm thầm.
10. **Entity/relationship tables:** lookup theo ID/code, quan hệ movie–entity được loại trùng theo cặp ID. Lookup genre/company/country/language giữ bản được gặp cuối cùng cho cùng khóa; script chưa có cơ chế review mâu thuẫn tên giữa các bản. Bảng lookup chỉ chứa thực thể liên quan tập phim đã chọn, cộng mã original language cần thiết.
11. **Cast:** sort theo `order`, thứ tự thiếu nằm cuối; giữ số cast theo tham số. Cast records được giữ riêng vì một người có thể đóng nhiều vai.
12. **Crew:** chỉ giữ đúng bốn job đã chọn, giữ department và credit ID. Một người có thể có nhiều job; không gộp các job thành một giá trị trên Person.
13. **Loại duplicate credit:** chỉ loại dòng cast/crew trùng tất cả các cột đầu ra; không gộp những credit có vai diễn hoặc job khác nhau.
14. **Xuất dữ liệu:** dựng xong tất cả bảng rồi ghi CSV và summary. File trống vẫn có header để bước transform biết schema.

Script dừng khi gặp dữ liệu không hợp lệ thay vì đoán cách sửa. Các trường mô tả như overview/status/name có thể thiếu và được giữ trống; movie title và các ID dùng làm khóa là bắt buộc. Đây là kiểm tra dữ liệu đầu vào, chưa phải validation RDF/OWL.

## 6. Thông tin để viết report

Mỗi lần chạy tạo `data/preparation_summary.json` (hoặc thư mục output được chọn), gồm:

- URL nguồn, đường dẫn input và SHA-256 của từng raw file.
- Timestamp xử lý theo UTC.
- Số dòng hai raw CSV và số movie ID khác nhau.
- Limit phim/cast, các crew jobs được chọn.
- Số duplicate input/credit bị loại và số phim thiếu credits, nếu có.
- Số dòng từng CSV đầu ra.
- Số phim thiếu từng field trong movies.csv sau làm sạch.

Dùng hash + version/ngày tải để xác định snapshot đã xử lý. Những counter không xuất hiện trong `cleaning_counts` có nghĩa là không phát sinh trong lần chạy. Summary không thống kê mọi chỉnh sửa từng ô; bảng missing counts cho biết kết quả cuối, không phải số ô bị sửa.

Đoạn mô tả phương pháp có thể dùng sau khi thực sự chạy và điền số liệu:

> Nhóm sử dụng snapshot TMDB 5000 Movie Dataset từ Kaggle, gồm bảng metadata và bảng credits. Hai bảng được liên kết qua TMDB movie ID. Nhóm chọn [N] phim theo thứ tự trong file nguồn, giữ tối đa [K] diễn viên mỗi phim và bốn loại công việc của crew: Director, Writer, Screenplay, Producer. Các danh sách JSON được chuyển thành bảng thực thể và bảng quan hệ. Quá trình làm sạch bao gồm chuẩn hóa văn bản, kiểu số và ngày, loại bản ghi trùng, giữ giá trị thiếu dưới dạng ô trống và không suy diễn các thuộc tính không có trong nguồn. Kết quả gồm 12 bảng CSV làm đầu vào cho bước chuyển đổi RDF. Snapshot nguồn và tham số xử lý được ghi lại để có thể tái lập.

Hạn chế cần nói: tập phim phụ thuộc thứ tự snapshot; giới hạn cast làm mất một phần credits; dataset không có IMDb ID/company country; zero-as-missing là giả định; chưa xác minh độ đúng của metadata ngoài đời và chưa đồng bộ với TMDB hiện tại.

## 7. Kiểm tra đã thực hiện

Chạy từ root project:

```powershell
python -m unittest discover -s tests -v
```

Test dùng fixture synthetic, kiểm tra join theo ID dù thứ tự credits khác và title trùng; cast order 0; duplicate relations; lọc crew; person dùng chung; limit; missing credits; duplicate ID xung đột; sai JSON/ngày/số/header. Test ghi dữ liệu vào thư mục tạm, không ghi các CSV thật trong `data/`.

Sau khi bạn chạy dữ liệu thật, kiểm tra `preparation_summary.json`, xem vài phim/cast/crew và bổ sung thống kê thực vào report. Không dùng số liệu của repo mẫu làm kết quả của pipeline này.
