# CLAUDE.md

Hướng dẫn cho mọi agent (Claude Code hay bất kỳ agent nào khác) làm việc trong repo này.

## Repo này là gì

Một "bộ não thứ hai" / knowledge base cho AI Engineering. Nó vừa là một git repo vừa là một Obsidian vault. Nó cũng đóng vai lớp context: trỏ một agent vào repo này và nó có thể đọc `concepts/<file>.md` để làm theo một mô hình tư duy cụ thể.

## Nguyên tắc vàng

Lưu **cách tư duy** và **cách tra cứu** — tuyệt đối không lưu các con số hay thay đổi (giá token, model tốt nhất hiện tại, thứ hạng leaderboard). Những thứ đó lỗi thời trong vài tuần và không thuộc về `concepts/` hay `playbooks/`. Với bất cứ thứ gì hay thay đổi, chỉ lưu quy trình tra cứu + một link, trong `references/`.

## Cấu trúc

- `concepts/` — mô hình tư duy bền. Các đoạn framing ngắn (3–5 câu), không code, không phần chứng minh.
- `playbooks/` — quy trình làm việc: "khi cần X thì làm theo các bước này".
- `references/` — link tới nguồn bên ngoài + ghi chú cách tra cứu. Không chép số liệu.
- `experiments/` — bằng chứng thực hành do chính bạn chạy. Code, log, ảnh chụp màn hình. Thư mục giá trị nhất: không ai khác có, không Google ra được.

## Phương pháp làm việc — proof before prose (bằng chứng trước, văn xuôi sau)

`concepts/*.md` mô tả một mô hình. Nó không được viết ra chỉ từ lý thuyết. Thứ tự bắt buộc là:

1. Dựng một script/module nhỏ chạy được, làm bật ra khái niệm đó.
2. Chạy nó và ghi lại bằng chứng (output log, so sánh trước/sau, một trace ép-lỗi-rồi-resume, v.v.) trong `experiments/<topic>/`.
3. Nếu khái niệm được lợi từ một diagram, hãy thêm một diagram Mermaid, render nó, và xác minh bằng Playwright (render headless → chụp màn hình → kiểm tra bằng mắt rằng nó đúng, không phải lỗi cú pháp). Lưu mã nguồn diagram + ảnh chụp đã xác minh vào `experiments/<topic>/` cạnh bằng chứng chạy.
4. Chỉ khi đó mới viết hoặc cập nhật đoạn framing ngắn trong `concepts/<file>.md`, chưng cất từ những gì bước 1–3 thực sự cho thấy — không phải từ những gì bạn kỳ vọng nó cho thấy.

Một file `concepts/*.md` đưa ra khẳng định ("hệ thống nên X") mà không có thư mục tương ứng trong `experiments/` chống lưng thì là chưa hoàn chỉnh. Khi được yêu cầu "viết concept", hãy kiểm tra experiment trước; nếu nó chưa tồn tại, hãy dựng nó trước khi viết đoạn văn.

Tuyệt đối đừng bịa ra một thư mục cấp cao mới (ví dụ "practice/") cho việc này — `experiments/` vốn đã là thư mục đó.

## Trọng tâm hiện tại: `concepts/agent-infra/`

Các file này mới chỉ là stub framing mở đầu (xem `concepts/agent-infra/README.md`); phần đào sâu còn chờ. Kế hoạch thực hành đang chạy phủ 4 chủ đề, ánh xạ tới các file đích cụ thể:

| Chủ đề thực hành | File concept | Thư mục experiment | Ghi chú |
|---|---|---|---|
| State (working state một lần chạy) | `concepts/agent-infra/state.md` | `experiments/agent-infra/state/` | Phạm vi: thứ gì chết khi một lần chạy kết thúc. |
| Memory (phân tầng xuyên nhiều lần chạy) | `concepts/agent-infra/memory.md` | `experiments/agent-infra/memory/` | Phạm vi: ngắn hạn vs dài hạn, session state vs log durable. Đừng lẫn với `state.md`. |
| Determinism tại ranh giới bất định | `concepts/agent-infra/determinism.md` **(chưa tồn tại — hãy tạo mới)** | `experiments/agent-infra/determinism/` | Khoảng trống: không file nào sẵn có trong `agent-infra/` phủ chuyện này. Hàng xóm gần nhất là `guardrails.md` và `recovery.md`, nhưng không file nào phụ trách nó. |
| Observability + eval-như-hạ-tầng | `concepts/agent-infra/observability.md` | `experiments/agent-infra/observability/` | Nửa eval-harness của phần thực hành này cung cấp đầu vào cho `playbooks/build-eval-set.md` đã có, không phải một file concept mới. `concepts/eval.md` ở cấp gốc vốn đã phụ trách phương pháp luận eval tổng quát — đừng lặp lại ở đây. |
| Khả năng resume / checkpointing | `concepts/agent-infra/recovery.md` | `experiments/agent-infra/recovery/` | `recovery.md` hiện đang framing retry/fallback/loop-guard theo thời gian thực; hãy mở rộng nó để phủ tường minh cả checkpoint-và-resume xuyên qua một lần khởi động lại, không chỉ retry trong một lần chạy. |

## Quy tắc cho các đề xuất trong repo này

- Khi viết vào `concepts/*.md`: bám đúng giọng văn hiện có — một đoạn ngắn, không khối code, không số liệu hay thay đổi, một diagram Mermaid nếu nó giúp ích cho mô hình.
- Khi được yêu cầu "dựng" hay "chứng minh" thứ gì đó: đặt code, log và ảnh chụp vào `experiments/<topic>/`, không bao giờ vào `concepts/`.
- Mọi file `concepts/agent-infra/*.md` được cập nhật đào sâu đều phải link ngược về thư mục `experiments/agent-infra/<topic>/` của nó như phần bằng chứng.
- Đừng bỏ qua bước chứng minh, kể cả với một thay đổi nhỏ — một chỉnh sửa `concepts/` không có experiment đứng sau thì phải được nêu cờ đỏ, không phải cứ thế viết ra.
- Đừng tạo thư mục cấp cao mới; `concepts/`, `playbooks/`, `references/`, `experiments/` đã phủ mọi trường hợp cho tới giờ.
