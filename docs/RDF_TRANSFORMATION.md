# Chuyển dữ liệu đã xử lý sang RDF

## Cách chạy

Từ thư mục `semantic-web`, sau bước chuẩn bị dữ liệu:

```powershell
python -m pip install -r requirements.txt
python scripts/transform.py
```

Script đọc đủ 12 CSV trong `data/`, xuất Turtle vào `output/movies.ttl`. Nó không đọc CSV raw hay gọi API. Đường dẫn mặc định tính theo vị trí script. Chạy lại ghi đè file đầu ra; CSV đầu vào được giữ nguyên.

```powershell
python scripts/transform.py --data-dir data --output output/movies.ttl --base-uri https://example.org/
```

## URI và vocabulary

Namespace `schema:` là `https://schema.org/`. Namespace `kg:` là `<base-uri>ontology/`, dành cho các khái niệm riêng sẽ được định nghĩa trong ontology của project. RDF hiện tại là dữ liệu instance; script chưa tạo OWL ontology hay chạy reasoning.

Mỗi thực thể dùng URI theo ID nguồn: `movie/19995`, `person/65731`, `genre/28`, `company/289`, `country/US`, `language/en`. Tên không được dùng làm khóa, tránh gộp hai người hoặc phim trùng tên. Rating có URI `rating/<movie_id>`.

Credit dùng `cast-credit/<movie_id>-<credit_id>` hoặc `crew-credit/<movie_id>-<credit_id>`. Nếu thiếu credit ID, script dùng SHA-256 của các field trong dòng để tạo URI ổn định. Các credit riêng vẫn trỏ đến cùng một Person. Bản ghi trùng hệt nhau tạo cùng bộ triple; cùng URI credit nhưng nội dung khác nhau gây lỗi.

`https://example.org/` chỉ là URI tạm khi phát triển. Khi có domain public, đổi `--base-uri`; cả URI thực thể và namespace ontology đổi cùng nhau. Cần dùng cùng namespace này khi viết OWL và SPARQL.

## Mapping

| CSV / field | RDF |
| --- | --- |
| movies | `schema:Movie`; `schema:identifier`, `schema:name` |
| original_title, overview, status | `kg:originalTitle`, `schema:abstract`, `kg:status` |
| release_date | `schema:datePublished`, literal `xsd:date` |
| runtime | `schema:duration`, `xsd:duration`; 162 phút → `PT162M` |
| budget, revenue | `kg:budgetUSD`, `kg:revenueUSD`, `xsd:integer` |
| original_language | `kg:originalLanguage` → Language |
| vote_average, vote_count | Movie → `schema:aggregateRating` → `schema:AggregateRating`; `schema:ratingValue` (`xsd:decimal`), `schema:ratingCount` (`xsd:integer`) |
| people | `schema:Person` |
| genres | `kg:Genre`; Movie → `kg:hasGenre` → Genre |
| companies | `schema:Organization`; Movie → `schema:productionCompany` → Organization |
| countries | `schema:Country`; Movie → `schema:countryOfOrigin` → Country |
| languages | `schema:Language`; movie_languages → `schema:inLanguage` |
| cast | Movie → `schema:actor` → Person; Movie → `kg:hasCastCredit` → `kg:CastCredit` |
| cast character, order | Trên CastCredit: `schema:characterName`, `schema:position` (`xsd:integer`) |
| crew | Movie → `kg:hasCrewCredit` → `kg:CrewCredit` |
| crew job, department | Trên CrewCredit: `schema:roleName`, `kg:department` |
| Director / Producer / Writer, Screenplay | Movie → `schema:director` / `schema:producer` / `schema:author` → Person |
| credit person_id, credit_id | Credit → `kg:person` → Person; `kg:sourceCreditId` |

Các bảng lookup đều có `schema:identifier` và `schema:name` nếu tên không trống. Writer và Screenplay đều có quan hệ author để truy vấn chung; job gốc trên credit giữ sự khác biệt. Job khác, nếu CSV được mở rộng, dùng `schema:contributor`.

Rating có `schema:bestRating 10` và `schema:worstRating 0` khi có ratingValue, thể hiện thang điểm TMDB. Giá trị trống không tạo triple, trong khi `order=0` và `vote_count=0` được giữ. Script tái sử dụng kiểm tra số của bước chuẩn bị và kiểm tra ngày ISO. Mọi khóa ngoại phải tồn tại trong bảng thực thể; thiếu file, thiếu cột, ID rỗng/trùng hoặc tham chiếu không tồn tại sẽ dừng trước khi ghi đầu ra.

## Khác với project mẫu

- Dùng `people.csv` làm bảng Person thống nhất, giữ riêng cast/crew credit có URI để bảo toàn ngữ cảnh phim, nhân vật và công việc.
- Dùng `kg:Genre` thay cho class `schema:Genre` tự giả định; không đặt job lên Person.
- Tách ngôn ngữ gốc khỏi danh sách ngôn ngữ được nói. Giữ original title, budget, revenue và status đã chuẩn bị.
- Trang TMDB dùng `rdfs:seeAlso`, không dùng `owl:sameAs`. Bước này chưa tạo liên kết tương đương với Wikidata hoặc DBpedia, và chưa đủ để tuyên bố đạt 5 sao.

## Kiểm tra thực tế

Ngày 06/10/2026, chạy transform trên bộ CSV hiện có với output thử trong `.review/`, sau đó đọc lại Turtle bằng RDFLib: 18.026 triple, 100 Movie, 1.085 Person, 1.000 CastCredit và 604 CrewCredit. Các số lượng thực thể khớp với summary của bước chuẩn bị. File mặc định `output/movies.ttl` sẽ được tạo khi người dùng chạy lệnh ở trên.

Bộ test gồm 11 test (6 chuẩn bị dữ liệu, 5 transform), tất cả đã pass. Test transform kiểm tra datatype, giữ giá trị 0, bỏ giá trị thiếu, phân biệt original/spoken language, dùng chung Person, job thuộc credit, lỗi khóa ngoại, credit trùng/xung đột, URI fallback ổn định và serialize/parse Turtle không mất triple. Đây là kiểm tra pipeline và mapping, chưa phải bằng chứng ontology nhất quán hoặc liên kết LOD chính xác.

## Nội dung dùng trong report

Pipeline chuyển các bảng CSV đã chuẩn hóa thành một RDF graph bằng RDFLib. Các thực thể được định danh bằng URI dựa trên ID hoặc mã của nguồn dữ liệu; quan hệ được tạo từ các bảng liên kết sau khi kiểm tra khóa ngoại. Thuộc tính số, ngày và thời lượng được biểu diễn bằng literal có datatype. Cast và crew được mô hình hóa bằng credit riêng để giữ thông tin phụ thuộc từng phim, đồng thời dùng chung thực thể Person. Graph được serialize sang Turtle để phục vụ xây dựng ontology, truy vấn SPARQL và liên kết LOD ở các bước tiếp theo.
