# Đọc repo Movie-Knowledge-Graph và lịch sử phát triển

Ngày kiểm tra: 06/10/2026. Repo tham chiếu: `../../Movie-Knowledge-Graph`, HEAD `e9e50af`. Không sửa repo mẫu.

**Kết luận:** repo sát đề LOD application: dữ liệu bảng → RDF → ontology → liên kết → truy vấn. Nên học pipeline và thứ tự làm, đồng thời kiểm tra lại các kết luận về 5★ và suy luận.

## 1. Phạm vi khảo sát và kết quả thực đo

Đã khảo sát cấu trúc thư mục, các script, ontology, 15 query, README/concept, workflow xuất bản và nội dung báo cáo; đọc lịch sử 94 commit và diff các mốc quan trọng. Đã đọc toàn bộ hàng của 11 CSV và parse toàn bộ 4 file Turtle, ontology mẫu và `pizza.owl`. PDF lý thuyết/báo cáo được trích văn bản theo trang; sơ đồ/ảnh trong PDF không được kiểm tra trực quan từng trang. `.sty`, hình minh họa và GIF là tài sản trình bày, không phải bằng chứng chương trình đã chạy đúng.

| Thành phần | Kết quả local |
|---|---:|
| `movies.csv` | 100 dòng, 100 movie ID khác nhau |
| `cast.csv` | 975 dòng |
| `crew.csv` | 110 dòng |
| `companies.csv` | 226 dòng |
| `genres.csv` | 17 dòng |
| `countries.csv` | 26 dòng |
| `languages.csv` | 24 dòng |
| `movie_companies.csv` | 298 dòng |
| `movie_countries.csv` | 151 dòng |
| `movie_genres.csv` | 268 dòng |
| `movie_languages.csv` | 146 dòng |
| `ontology/ontology.owl` | 238 triples; nội dung là Turtle |
| `output/movies.ttl` | 10.957 triples |
| `output/movie_links.ttl` | 168 triples, 87 local movie subjects |
| `output/inferred_graph.ttl` | 45.035 triples |
| `output/inferred_graph_clean.ttl` | 39.116 triples |
| `movie_candidates.csv` | 91 dòng: 81 approved, 8 review, 2 rejected |

11 CSV không có dòng trùng hoàn toàn trong snapshot hiện tại. Điều đó không có nghĩa crawler đã có cơ chế chống trùng cho những lần lấy dữ liệu khác.

Chạy trực tiếp query 1–14 bằng RDFLib trên graph gốc + ontology + links, rồi trên file inferred đã lưu:

| Query | Gốc + ontology + links, chưa suy luận | Inferred đã lưu | Ý nghĩa |
|---|---:|---:|---|
| Q1–Q3 | Mỗi query 20 dòng | Mỗi query 20 dòng | Truy vấn cơ bản |
| Q4 | 5 dòng | 5 dòng | Vai diễn |
| Q5 | 42 triples | 159 triples | DESCRIBE; số triple mô tả |
| Q6–Q8 | Mỗi query 20 dòng | Mỗi query 20 dòng | Lọc/xếp hạng |
| Q9 | 3 dòng | 3 dòng | Nhiều điều kiện |
| Q10 | 4 dòng | 20 dòng | Cần kiểm tra alias sau sameAs, không suy ra thêm 16 người |
| Q11 | 0 dòng | 15 dòng | Inverse property có hiệu lực trong snapshot |
| Q12 | 0 dòng | 1 dòng | Property chain có hiệu lực trong snapshot |
| Q13, Q14 | false, false | false, false | Chưa chứng minh lợi ích suy luận |

Đây là kiểm tra file inferred có sẵn, **chưa tái tạo closure từ đầu** và chưa xác minh dữ liệu ngoài thực tế. Q15 chưa chạy remote; không có kết luận endpoint live hoạt động.

## 2. Mỗi thư mục làm gì?

| Đường dẫn | Vai trò | Học để tự làm |
|---|---|---|
| `docs/CONCEPT.MD` | Phạm vi và vocabulary | Viết competency questions trước ontology |
| `scripts/tmdb.py` | 5 trang popular; details + credits; top 10 cast; chỉ director trong crew | Thu thập theo ID, giữ nguồn và snapshot |
| `data/` | 11 CSV entity/relationship | Tách quan hệ nhiều–nhiều thành bảng |
| `scripts/transform.py` | CSV → RDFLib → Turtle | URI theo ID, datatype, role và rating |
| `ontology/ontology.owl` | Class, domain/range, restriction, inverse, chain | Phải giải thích từng axiom bằng ngôn ngữ thường |
| `scripts/link_movies.py` | Tìm Wikidata, tạo DBpedia candidate, ghi links | Ghép ID và lưu quyết định duyệt |
| `scripts/ask.py` | CLI local/remote, OWL-RL tùy chọn | Tách query khỏi code Python |
| `queries/` | 15 câu hỏi từ đơn giản đến liên kết | Cần đầu ra kỳ vọng, không chỉ query chạy không lỗi |
| `output/` | Graph gốc, liên kết, graph suy luận và bản lọc | Cần script tái tạo từng artifact |
| `scripts/build_site.py` | Sinh trang resource, ontology, search, download | Công bố URI và dữ liệu cùng namespace |
| `.github/workflows/pages.yml` | Build và deploy static site | Web tĩnh không chạy Fuseki |
| `report/` | Báo cáo LaTeX 11 trang PDF và ảnh demo | Cấu trúc phương pháp → kết quả → hạn chế |

## 3. Lịch sử commit: thứ tự thực tế

94 commit có ngày từ 17/09 đến 05/10/2026 theo lịch sử local.

| Giai đoạn | Commit tiêu biểu | Thay đổi và bài học |
|---|---|---|
| 17–18/09: dựng nền | `ebd2860`, `5668080`, `86036c1` | Khởi tạo, conceptualization, crawler. Bắt đầu nhỏ |
| 18/09: CSV và RDF | `4fdf311`, `ee2a762`, `3d9db69`, `d4e730e` | Làm sạch, transform, query, dữ liệu 20 phim |
| 19/09: môi trường | `b675def`, `9f2599d` | API key sang environment, thêm bước OWL |
| 21/09: ontology/reasoning | `b04f412`, `2caadd5`, `efaf42b`, `aff978a` | OWL-RL, ontology, namespace riêng, Q11–Q14 |
| 21/09: điều chỉnh quy mô | `893f216`, `9bc647f`, `54aa87b` | Từ 200 về 100 phim; graph vừa đủ demo quan trọng hơn số lượng |
| 21–22/09: truy vấn remote | `11635b1`, `0ba2594`, `70e3d10` | Đổi cách query và xử lý rate limit |
| 22/09: liên kết | `25eec1a`, `2ba4e6a`, `0dc3fd8` | Thêm linking và kiểm tra năm; cần đối chiếu code với commit message |
| 23/09: lưu graph suy luận | `669e962`, `4f74cfc` | Commit file 45K và 39K triples; nên có script tạo lại |
| 03/10: tổ chức project | `1ff2855`, `16f87ca` | Tương thích Linux, chuyển scripts/ontology/docs |
| 05/10: xuất bản | `e04e691` | Thêm static browser và workflow |
| 05/10: báo cáo | `e8bf1f0` đến `cf03eaa`, `e9e50af` | Hoàn thiện từng section, ảnh, appendix, README |

Có thể tự xem lại một mốc, không checkout đè file:

```powershell
git -C ..\Movie-Knowledge-Graph log --reverse --oneline
git -C ..\Movie-Knowledge-Graph show 0dc3fd8 -- link_movies.py
git -C ..\Movie-Knowledge-Graph show e04e691 -- scripts/build_site.py
```

Đường dẫn trong `git show` phụ thuộc thời điểm commit: trước `16f87ca`, script còn ở root.

## 4. Những điểm cần làm tốt hơn mẫu

**A. Namespace khi xuất bản chưa nhất quán.** `build_site.py` đổi URI hiển thị sang GitHub Pages, nhưng phần download dùng `shutil.copy2` để chép nguyên RDF vẫn mang `https://example.org/`. Cần graph phát hành chứa đúng public URI; HTML, JSON-LD, Turtle, query và ontology phải thống nhất. Các đường dẫn trang ontology cũng cần khớp URI vocabulary thực tế.

**B. Điều kiện linking trong code khác mô tả.** `score_candidate()` chỉ cần `identifier_matches` không rỗng và năm trùng để cho 1.0; nghĩa là **một trong hai ID**, không bắt buộc cả IMDb và TMDB. README và tên commit `0dc3fd8` dễ khiến người đọc hiểu là cả hai. 81 dòng approved trong CSV hiện có đều ghi cả hai ID, nhưng đó là đặc điểm snapshot, không phải điều code bảo đảm.

**C. DBpedia URI được đoán từ enwiki sitelink.** Hàm `dbpedia_uri()` tạo URI từ tiêu đề Wikipedia, chưa kiểm chứng resource thực sự có dữ liệu DBpedia đúng phim. Phải xác minh URI/redirect/type/ID trước khi phát hành `owl:sameAs`.

**D. Linkset không khớp hoàn toàn candidate log.** CSV ghi 81 approved, linkset có 87 local movie subjects và 168 triples. Chưa xác định đầy đủ nguyên nhân; cần lưu quyết định duyệt tay và tái tạo linkset từ một sổ quyết định cuối cùng.

**E. Q13–Q14 không phải bằng chứng suy luận mạnh.** Cả trước và sau đều false. Functional property có thể dẫn đến đồng nhất đối tượng, không phải phát hiện hai chuỗi URL khác nhau bằng `FILTER !=`. Nên dùng Q11/Q12 hoặc fixture kiểm soát với kết quả trước/sau rõ ràng.

**F. SameAs làm tăng alias trong kết quả.** Q11 trả 15 dòng không đồng nghĩa 15 phim khác nhau. Q10 cũng tăng số dòng sau inference. Lọc local URI và `COUNT(DISTINCT ?movie)` khi báo cáo số phim; không chỉ đếm tất cả URI mang type Movie.

**G. OWL không thay thế validation dữ liệu.** `minCardinality 1` không tự báo thiếu tên dưới open-world semantics. Dùng kiểm tra CSV/SPARQL hoặc SHACL để bắt missing value; dùng OWL để suy ra tri thức.

**H. Không tự thêm thuật ngữ vào namespace bên ngoài.** Repo khai báo `schema:Genre`; nên dùng `kg:Genre` hoặc `skos:Concept` và mô tả mapping. Tài liệu [schema:genre](https://schema.org/genre) nêu giá trị Text/URL. Tránh đóng khung global `schema:name`, `schema:identifier` chỉ cho movie nếu graph còn nhiều loại thực thể.

**I. Không ép `schema:sameAs` thành quan hệ đối xứng có domain Movie.** Với khai báo mẫu, liên kết ngược có thể khiến các URI trang web nhận type Movie. Dùng `owl:sameAs` cho đồng nhất thực thể đã kiểm chứng và `rdfs:seeAlso` cho trang thông tin khi thích hợp.

**J. Reproducibility còn thiếu.** `ask.py --reasoning` suy luận trong bộ nhớ, không serialize file inferred. Không thấy script riêng tái tạo bản clean trong HEAD. Project mới cần `reason.py`, lưu graph gốc, graph bổ sung và closure; không xóa tùy ý các triple hợp lệ chỉ để giảm kích thước.

**K. Chưa đủ bằng chứng open license.** Repo không có file LICENSE dữ liệu rõ ràng trong danh sách file khảo sát. API công khai, file CSV và link Wikidata không tự chứng minh tiêu chí Open Data. Chọn nguồn và mô tả quyền phát hành ngay đầu project.

**L. Query remote được điều phối bởi ứng dụng.** `ask.py` dùng regex thay mẫu `owl:sameAs` thành `VALUES`, rồi gửi query tới endpoint. Đây là cách truy vấn hai bước có giá trị, nhưng không phải một SPARQL federated query dùng `SERVICE`. Báo cáo phải mô tả đúng cách đã làm.

Các điểm trên là nhận xét dựa trên code và snapshot local, không phải kết luận chấm điểm của giảng viên.
