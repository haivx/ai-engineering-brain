# NOTES.md — các lần chạy thực sự cho thấy điều gì

Dành cho người viết `concepts/agent-infra/determinism.md`.
Xem `RUN.md` để đọc output đã ghi lại mà các gạch đầu dòng dưới đây rút ra từ đó.

- Khẳng định cốt lõi đúng y như phát biểu: cô lập lời gọi bất định sau đúng một
  hàm với contract input/output cố định (`boundary.py: non_deterministic_call`)
  khiến mọi thứ còn lại (`assemble_input`, `parse_output`, `decide`) sinh ra
  các log JSON giống nhau từng byte qua hai lần chạy cùng một input, lần nào
  cũng vậy, trong khi output của chính ranh giới (câu chữ, confidence, độ trễ)
  thay đổi mỗi lần. Không có ngoại lệ nào qua ~10 lần chạy.

- Kết quả hữu ích nhất không phải là lần chạy ổn định — mà là phần demo rò rỉ.
  Trong một lần gọi `leak_demo.py`, rò rỉ do parse ngây thơ đã thực sự
  **lật ngược quyết định access-control** (`grant_access` vs `deny_access`)
  với cùng một input, thuần túy vì câu chữ của model tình cờ mở đầu bằng một từ
  khác ("Approve." vs "Yes,"). Phán quyết nền thì không hề đổi. Đây là lập luận
  mạnh hơn nhiều so với "log trông khác nhau" — một bug rò rỉ tính bất định ở
  tầng parse có thể âm thầm thay đổi thứ hệ thống *làm*, chứ không chỉ thứ nó *ghi log*.

- Xác nhận một điểm tinh tế đáng phát biểu cho chính xác trong concept:
  "deterministic bên ngoài ranh giới" không có nghĩa là "cùng một câu trả lời
  mọi lúc" — quyết định cuối cùng của một pipeline kỷ luật hoàn toàn có thể
  khác đi nếu nội dung ngữ nghĩa tại ranh giới khác đi. Thứ phải ổn định là
  *quy trình*: với cùng một output từ ranh giới, code bao quanh luôn làm đúng
  một việc. Stub được dựng có chủ đích sao cho nhãn luôn khôi phục được bất kể
  cách diễn đạt, và chính điều đó khiến "cùng một quyết định ở cả hai lần chạy"
  là một bằng chứng có ý nghĩa chứ không phải sự trùng hợp của stub.

- Rò rỉ do duyệt `set()` đòi hỏi một phương pháp quan sát thực sự khác biệt:
  trong cùng một tiến trình đang chạy, thứ tự duyệt của một set KHÔNG bị xáo lại
  giữa hai lần gọi — nó chỉ thay đổi **giữa các lần gọi tiến trình `python3`
  riêng biệt** (do CPython ngẫu nhiên hóa hash chuỗi theo từng tiến trình). Tôi
  đã phải gọi ra `subprocess` mới minh họa được cái này; kiểu gọi-hai-lần trong
  cùng tiến trình dùng cho các rò rỉ khác sẽ cho ra "giống hệt" và che mất bug.
  Đáng một dòng trong concept: một số tính bất định chỉ lộ ra ở production
  (nhiều lần khởi động lại tiến trình), chứ không lộ ra trong vòng lặp dev gọi
  một hàm hai lần trong cùng một tiến trình.

- Rò rỉ timestamp từ đồng hồ hệ thống là thứ dễ tạo ra nhất và rõ ràng là tệ
  nhất khi nhìn lại — một dòng (`"decided_at": time.time()`) nằm trong đoạn code
  mà ngoài ra trông y hệt logic quyết định thuần túy. Đây là ví dụ cụ thể rất tốt
  cho "ngẫu nhiên ẩn" chẳng liên quan gì tới LLM; kỷ luật determinism-tại-ranh-giới
  là một tính chất chung của luồng dữ liệu, không phải mối bận tâm riêng của LLM.

- Record/replay (phần thưởng thêm) chạy được gần như không cần thêm code: vì
  `run_pipeline()` vốn đã nhận `boundary_fn` làm tham số (cần cho nhánh tùy chọn
  `--live` dù sao đi nữa), chỉ cần cắm vào một closure đọc fixture là *toàn bộ*
  log — kể cả phần `nd` vốn hay thay đổi — trở nên giống nhau từng byte qua các
  lần chạy. Lợi ích thực tế mô tả ở PLAN.md §6 là có thật và rẻ, một khi ranh
  giới đã là một tham số hàm thực thụ thay vì một lời gọi hardcode.

- Bất ngờ / thứ không diễn ra như dự tính: ban đầu tôi cho rằng log bất định
  (`nd`) sẽ khác nhau rõ rệt ở đúng mọi cặp lần chạy, và viết `run_stable.py`
  coi đó là một sự thật hiển nhiên. Với chỉ 4 template × một số thực confidence
  liên tục × một số nguyên độ trễ ngẫu nhiên, trên thực tế chúng luôn khác nhau
  qua các lần chạy được lấy mẫu — nhưng riêng confidence/độ trễ chỉ khiến việc
  trùng lặp gần như bất khả, chứ không phải bất khả tuyệt đối (một lần rút trùng
  ngẫu nhiên về lý thuyết vẫn có thể xảy ra với 4 template và một dải uniform
  hẹp). `run_stable.py` xử lý chuyện này như một ghi chú chứ không phải một
  thất bại, để exit status của script không phụ thuộc vào nó.

- Điều tôi KHÔNG chứng minh được: bản thân phương sai lấy mẫu của một LLM thật.
  Nhánh `--live` có tồn tại và được nối vào cùng contract ranh giới
  (`live_llm_call` trong `boundary.py`), và suy giảm an toàn (không crash, không
  in key) khi `OPENROUTER_API_KEY` không được đặt — xem RUN.md §4 — nhưng tôi đã
  không chạy nó với API OpenRouter thật, theo đúng chỉ dẫn giữ cho bản chứng minh
  mặc định không phụ thuộc mạng. Hành vi "cùng nhãn, khác câu chữ" của stub là
  một sự đơn giản hóa có chủ đích, không phải tính chất đo được của model thật nào.

- Ghi chú về phạm vi: bản chứng minh này nói về CẤU TRÚC (một ranh giới hàm duy
  nhất, code thuần bao quanh, tách bạch tường minh giữa hai nửa của log), chứ
  không nói về việc làm cho bản thân output bất định "deterministic hơn" (ví dụ
  temperature=0, seeding). Đó là những kỹ thuật bổ trợ mà đoạn concept có thể
  nhắc tới như thứ lân cận nhưng khác biệt — chúng giảm *mức độ* dao động của
  ranh giới; còn kỷ luật ranh giới ở đây là về việc khoanh vùng phương sai đang
  tồn tại, dù nhiều hay ít.
