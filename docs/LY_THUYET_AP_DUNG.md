# Đọc theory để làm movie knowledge graph

Các trang dưới đây là **số trang PDF tính từ 1**, có thể khác số slide in ở góc. Đã trích văn bản của cả 12 PDF lý thuyết, đọc các nội dung phục vụ project; hình/sơ đồ thuần ảnh có thể không hiện đủ trong phần trích. Hai workbook được đọc phần XML chứa ô để lấy yêu cầu và lịch, không sửa workbook. `pizza.owl` được parse RDF/XML thành 1.944 triples.

## 1. Thứ tự học gắn với sản phẩm

| Tài liệu | Nội dung cần nắm | Áp dụng cụ thể |
|---|---|---|
| `01_Intro.pdf` — 59 trang | Entity, semantic interoperability, tích hợp nguồn, reasoning | Viết problem statement; vì sao title text chưa đủ để đồng nhất phim |
| `02_RDF.pdf` — 63 trang | Triple, IRI/literal/blank node, datatype, serialization, open world, provenance | `transform.py`, URI policy, mapping, role/rating |
| `03_RDFS.pdf` — 53 trang | Class/property hierarchy, domain/range, TBox/ABox, forward chaining | Ontology nền và các hệ quả type |
| `04_LOD.pdf` — 76 trang | Dereferenceable URI, 5★, owl:sameAs, vocabulary reuse, metadata, RDFLib/Jena | Xuất bản RDF, ontology và liên kết ngoài |
| `05_OWL.pdf` — 60 trang | Inverse/functional properties, disjointness, restrictions, equivalent classes | Demo inference và giải thích giới hạn của ràng buộc |
| `06-OWL2.pdf` — 79 trang | Property chains, EL/QL/RL, tableau, consistency và complexity | Chọn OWL-RL subset phù hợp; chain Movie→Company→Country |
| `07-Knowledge-Modeling.pdf` — 83 trang | Competency questions, Methontology, OntoClean, roles, patterns/anti-patterns | Thiết kế từ CQ; không nhầm class/instance hay Person/Role |
| `Ext_SPARQL.pdf` — 55 trang | Graph patterns, FILTER, OPTIONAL, UNION, ASK, DESCRIBE, CONSTRUCT, SERVICE | Query suite, endpoint và demo liên nguồn |
| `Ext_Knowledge-Graphs.pdf` — 90 trang | Wikidata/DBpedia/YAGO, quality–coverage trade-off, provenance, linking | Chọn target, đánh giá coverage và precision |
| `Ext. Labeled-Property-Graphs.pdf` — 70 trang | N-ary facts, reification, named graphs, RDF*/Cypher | Giải thích CastCredit; biết vì sao movie graph Neo4j chưa thay thế RDF/SPARQL trong đề |
| `Ext. App-Linked Widget.pdf` — 48 trang | Tích hợp dữ liệu bằng các thành phần có input/output và mô tả ngữ nghĩa | Tham khảo cách nối nguồn → xử lý → hiển thị; không phải yêu cầu xây framework widget |
| `Ext. App-StatSpace.pdf` — 68 trang | Heterogeneity định dạng/URI/đơn vị, mapping, mediator, query/result rewriting | Chuẩn hóa ID, đơn vị runtime, lưu provenance và remote lookup |
| `pizza.owl` | Ontology thực hành classes, restrictions, equivalent classes | Thực hành Protégé trước khi tự dựng ontology phim |
| `20261-IT6390E.xlsx` | Đề chính có hai lựa chọn và đầu ra | Chọn LOD application, C4:C8; D3 có slide/report/video |
| `QSTT - IT6390E - Capstone.xlsx` | Bản có ghi chú nhóm cho đề LOD | Tách yêu cầu chung với quyết định riêng của nhóm |

Đọc để làm trước: **02 → 03 → 04 → 07 (CQ/patterns) → 05 → 06 (chain/profile) → Ext_SPARQL**. Các phần tableau chi tiết, top-level ontology và các framework ứng dụng là nền tảng/mở rộng; không cần tự hiện thực reasoner hay mediator tổng quát cho capstone này.

## 2. Những chỗ cần mở lại khi làm

| Vấn đề | Tài liệu/trang |
|---|---|
| URI, literal, datatype, Turtle | `02_RDF`, trang 11–26 |
| Quan hệ nhiều ngôi | `02_RDF`, trang 27–29 |
| Open world/non-unique naming | `02_RDF`, trang 30–34 |
| RDF và HTML, content negotiation | `02_RDF`, trang 35–49 |
| Provenance/reification | `02_RDF`, trang 53–57 |
| Domain/range và TBox/ABox | `03_RDFS`, trang 21–32 |
| Suy luận, nhiều domain/range | `03_RDFS`, trang 33–45 |
| Dùng sai sameAs | `04_LOD`, trang 11–13 |
| Linked Data principles, 5★, best practices | `04_LOD`, trang 14, 16–17 |
| Functional/inverse functional | `05_OWL`, trang 24–25 |
| Restrictions và necessary/sufficient conditions | `05_OWL`, trang 30–39 |
| Property chain, OWL profiles | `06-OWL2`, trang 9–13 |
| Competency questions/Methontology | `07-Knowledge-Modeling`, trang 9–12 |
| Roles/rigidity/identity | `07-Knowledge-Modeling`, trang 15–28 |
| Design patterns và lỗi modeling | `07-Knowledge-Modeling`, trang 39–50 |
| ASK/DESCRIBE/CONSTRUCT/SERVICE | `Ext_SPARQL`, trang 36–39 |
| SPARQL mặc định không reasoning | `Ext_SPARQL`, trang 42–45 |
| Linking precision/recall/coverage | `Ext_Knowledge-Graphs`, trang 41–48 |

## 3. Chuyển khái niệm lý thuyết thành câu trả lời bảo vệ

**RDF là gì trong bài này?** Một phim là subject URI, hasDirector là predicate URI, đạo diễn là object URI. Tên phim là literal. Người là node riêng để nhiều phim dùng chung, thay vì lặp tên người trong mỗi dòng và hy vọng chúng cùng chỉ một người.

**TBox/ABox?** `Movie`, `Person`, domain/range, inverse, chain là mô hình (TBox). Phim A, người B, A hasDirector B là assertion (ABox). Tách file để theo dõi nguồn của facts và rules.

**Domain/range có phải validation schema như SQL?** Chúng cho phép suy ra type. Nếu domain hasDirector là Movie thì chủ thể của một triple hasDirector được suy ra là Movie. Không tự động báo lỗi chỉ vì chủ thể chưa khai báo type trước đó. Nhiều domain được hiểu đồng thời, không tự động thành phép OR.

**Ontology hơn sơ đồ ER ở đâu?** Có thể thêm axiom mang nghĩa hình thức để suy ra quan hệ không được ghi trực tiếp: inverse và property chain. Tuy nhiên nhiều truy vấn join vẫn có thể viết trong SQL; không cần tuyên bố SQL không làm được. Lợi ích của bài là định danh toàn cục, vocabulary dùng chung, ngữ nghĩa và liên kết qua nguồn.

**Suy luận khác query join thế nào?** Query đường đi Movie→Company→Country tìm một pattern. Axiom property chain cho phép thêm fact Movie→productionCompanyCountry→Country vào closure, rồi query dùng quan hệ suy ra đó. Cần demo cùng query trước/sau, không đổi query thành đường đi dài rồi gọi kết quả là OWL reasoning.

**Missing không bằng false.** Không có actor trong snapshot không có nghĩa bộ phim không có diễn viên. ASK false không đồng nghĩa phủ định logic. Dataset giới hạn top 10 cast càng cần diễn giải là “không tìm thấy trong tập hiện có”.

**Functional không phải UNIQUE constraint.** Một subject có hai object qua functional object property có thể khiến reasoner kết luận hai object cùng thực thể. Chỉ khi có thêm tri thức khác biệt thích hợp mới phát sinh mâu thuẫn. Bắt dữ liệu thiếu/sai định dạng bằng validator hoặc SHACL.

**SameAs có mạnh không?** Có: nó khẳng định đồng nhất và có thể lan truyền thuộc tính trong suy luận. Sai một link có thể làm trộn facts giữa hai phim; vì vậy title trùng chưa đủ để phát hành link.

**CastCredit để làm gì?** Nhân vật và thứ tự credit thuộc việc một người tham gia một phim. Gắn characterName trực tiếp vào Person sẽ làm lẫn các vai diễn ở nhiều phim. Tạo node credit nối movie/person và giữ thuộc tính của lần tham gia ấy.

**Cần Neo4j không?** Không cần cho pipeline này. Tài liệu property graph giúp hiểu lựa chọn mô hình; sản phẩm theo đề đang cần RDF/ontology/SPARQL/LOD. Một đồ thị vẽ đẹp trong Neo4j không tự đáp ứng các phần còn lại.

## 4. Bài thực hành với pizza.owl, khoảng 45–60 phút

1. Mở `../../theory/pizza.owl` bằng Protégé, xem hierarchy: Pizza, PizzaTopping và các lớp pizza cụ thể.
2. Chọn một lớp có các existential restriction `hasTopping some ...`. Đọc thành câu: có ít nhất một topping thuộc lớp đó.
3. So sánh với `hasTopping only ...` (`allValuesFrom`). Only giới hạn loại giá trị nếu có, tự nó không bảo đảm tồn tại topping.
4. Xem các lớp được định nghĩa bằng equivalent class và intersection. Phân biệt điều kiện cần với điều kiện đủ.
5. Chạy reasoner phù hợp trong Protégé; xem inferred hierarchy và lớp không thỏa được nếu xuất hiện. Các lớp cố ý minh họa lỗi không nên xóa chỉ để có màn hình đẹp.
6. Tự tạo ontology Movie riêng, mượn **cách mô hình hóa** và cách kiểm tra, không đổi tên mọi Pizza thành Movie một cách máy móc.

Ánh xạ tư duy: Pizza→Movie, hasTopping→hasGenre chỉ là ví dụ giúp hình dung quan hệ. Topping vật lý và genre khái niệm có identity khác nhau; đặc tính functional/inverse functional trong Pizza không tự động đúng cho movie genre.

## 5. Lưu ý khi dùng slide làm tài liệu code

Các slide là tài liệu giảng dạy, một số đoạn là minh họa, có lỗi chính tả hoặc thông tin theo phiên bản cũ. Chạy parser và đối chiếu chuẩn khi đưa vào code. Ví dụ thuật ngữ đúng là `rdfs:subClassOf`; không chép nhầm `owl:subClassOf` từ một ví dụ. Trong RDF 1.1, simple string literal có datatype `xsd:string`; language-tagged string là loại khác, cần chú ý khi FILTER.

Không cần mang phần RDF*/SPARQL* vào MVP. Chuẩn/cú pháp và hỗ trợ công cụ cần kiểm tra riêng nếu sử dụng. Giữ Turtle RDF 1.1 và SPARQL 1.1 cho bài hiện tại là phạm vi dễ kiểm chứng.

Tài liệu đối chiếu: [RDF 1.1 Concepts](https://www.w3.org/TR/rdf11-concepts/), [SPARQL 1.1 Query](https://www.w3.org/TR/sparql11-query/), [OWL 2 Profiles](https://www.w3.org/TR/owl2-profiles/), [Linked Data](https://www.w3.org/DesignIssues/LinkedData.html).
