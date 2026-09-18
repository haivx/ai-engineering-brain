# Agent Infra

Các mô hình tư duy cho tầng hạ tầng nằm dưới một agent — state, memory,
determinism, observability, khả năng resume — mỗi thứ chỉ được chưng cất
từ một experiment đã chứng minh trong thư mục
`experiments/agent-infra/<topic>/` tương ứng, đúng theo quy tắc
proof-before-prose của repo này.

## Ở đây có gì

- `state.md` — working state, phạm vi một lần chạy. Chết khi lần chạy kết
  thúc; tách phần scratch dùng-một-lần khỏi một log durable append-only để
  một cú crash không bao giờ làm mất tiến độ đã commit.
- `memory.md` — state xuyên nhiều lần chạy (một session), nằm giữa phạm vi
  của `state.md` và log durable vĩnh viễn. Session state có tuổi thọ hữu
  hạn và phải được promote vào log durable trước khi bị xóa, nếu không nó
  lặp lại đúng thất bại của `state.md` ở cấp cao hơn một bậc.
- `determinism.md` — cô lập một lời gọi bất định sau một ranh giới hàm duy
  nhất để mọi thứ quanh nó vẫn tái lập được, và chuyện gì xảy ra khi sự cô
  lập đó bị rò rỉ.
- `observability.md` — cái trace có cấu trúc nằm dưới con số tổng của một
  bài eval. Chỉ phụ trách tracing/instrumentation; phương pháp luận eval
  nằm ở `concepts/eval.md`, còn nửa eval-harness cung cấp đầu vào cho
  `playbooks/build-eval-set.md`.
- `recovery.md` — checkpoint-và-resume xuyên qua một lần khởi động lại tiến
  trình thật: một checkpoint chỉ đáng tin khi đi kèm với các lần commit atomic.

`state.md` và `memory.md` được tách riêng một cách có chủ đích: "thứ gì
chết khi một lần chạy kết thúc" so với "thứ gì tồn tại qua nhiều lần chạy,
và trong bao lâu". Không file nào bao phủ phạm vi của file kia.

## Vẫn mới chỉ là khung mở đầu (chưa có experiment)

Những file này đến từ khung dựng cụm ban đầu và vẫn chỉ là các đoạn framing
ngắn. Theo quy tắc proof-before-prose của repo, mỗi file chỉ được đào sâu
khi đã có một experiment đáp xuống `experiments/agent-infra/<topic>/` — không
sớm hơn:

- `context-engineering.md` — thứ gì được đưa vào context ở mỗi bước
- `tool-calling.md` — giao diện từ model ra thế giới
- `orchestration.md` — vòng lặp đơn so với multi-agent, sub-agent
- `guardrails.md` — xác thực trước khi hành động

## Tổng kết: cái nào trong số này sẽ hỏng âm thầm trước tiên?

Rò rỉ determinism hỏng sớm nhất về mặt thời gian — không cần bất kỳ sự cố
nào xảy ra trước. Experiment về determinism cho thấy một parser ngây thơ đã
lật ngược một quyết định access-control thật (cho phép hay từ chối) với cùng
một input, thuần túy do cách diễn đạt tình cờ, mà không có exception nào được
ném ra (`experiments/agent-infra/determinism/RUN.md`, §2). Điều đó có thể xảy
ra ngay ở lần chạy bình thường đầu tiên của một hệ thống vốn khỏe mạnh.

Các pattern "dạng state" còn lại cần có gì đó hỏng trước — một cú crash, một
lần hết hạn, một lần khởi động lại — và khác nhau ở chỗ hậu quả ồn ào tới đâu:

- Thất bại phân tầng state và memory thì âm thầm nhưng có điều kiện:
  anti-pattern gộp-một-khối trông *hay hơn* thiết kế đúng khi hệ thống khỏe
  mạnh (`state/NOTES.md`), và chỉ lộ ra mất mát đúng vào khoảnh khắc
  crash-rồi-xóa-sạch. Thất bại phân tầng session trong `memory.md` cũng cùng
  hình dạng ấy, chỉ khác là bị chặn sau một lần hết hạn thay vì một cú crash.
- Thất bại recovery chia làm hai. Mất hẳn checkpointing thì *ồn ào*: các bước
  chạy lại rành rành trong log (`recovery/RUN.md`, §5). Còn ghi không atomic
  trong cùng experiment ấy thì âm thầm: một file hỏng nằm trên đĩa mà chẳng có
  gì đánh dấu nó là rác (`recovery/NOTES.md`).

Việc những chuyện này có bao giờ được *phát hiện* hay không lại do một pattern
thứ năm quyết định, và bản thân nó không phải một kiểu thất bại: observability.
Experiment về observability chứng minh điều này một cách độc lập — một harness
có cấu trúc và một phiên bản ngây thơ bọc lệnh print đều cho 12/18 y hệt nhau
trên cùng 18 case, và phiên bản ngây thơ không phân biệt nổi một cú crash với
một câu trả lời sai (`observability/RUN.md`, §5). Một hệ thống không có trace
có cấu trúc sẽ hiển thị "điểm số tệ hơn một chút" cho cả một regression thật
lẫn một cú crash ở mức code, không tài nào phân biệt — và cũng experiment ấy
cho thấy một con số tổng trần trụi có thể che giấu một đánh đổi thật ngay cả
khi chẳng có gì crash (+11,1 điểm ròng, nhưng 3 true positive bị đánh đổi âm
thầm để sửa được 5 false positive).

Vậy nên thứ tự trung thực là: rò rỉ determinism làm hỏng hành vi trước tiên,
với zero điều kiện tiên quyết. Observability quyết định liệu sự hỏng hóc đó —
hay cú xóa sạch do phân tầng state, hay file checkpoint hỏng — có bao giờ được
nhận ra, thay vì bị nuốt chửng âm thầm vào một con số tổng trông vẫn còn hợp
lý. Bỏ qua ranh giới determinism làm hỏng một quyết định ngay từ lần chạy đầu;
bỏ qua phân tầng hay tính atomic là gieo sẵn một thất bại cho cú crash kế tiếp;
bỏ qua observability là bảo đảm rằng khi nó xảy ra, không ai biết vì sao.
