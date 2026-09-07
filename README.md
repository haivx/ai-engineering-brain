# ai-engineering-brain

Bộ não thứ hai (knowledge base) cho mảng **AI Engineering**.
Là repo Git + đồng thời là một Obsidian vault (chỉ cần "Open folder as vault").

## KB này dùng để làm gì
- Nơi tra cứu kiến thức đã học, có tổ chức.
- **Context layer cho Claude Code**: vì toàn bộ là markdown trong repo, agent đọc được.
  Ví dụ: "áp routing như trong `concepts/routing.md`" → nó tự đọc và làm theo.

## Nguyên tắc vàng
> Lưu **cách tư duy** và **cách tra**, đừng lưu **con số**.

Giá token, model đang tốt nhất, bảng xếp hạng → phân rã trong vài tuần. KHÔNG chép vào đây.
Mô hình tư duy (routing, eval, tier...) → không đổi. ĐÂY mới là thứ đáng viết.
Phần volatile: chỉ lưu *quy trình tra* + link (xem `references/`).

## Cấu trúc
- `concepts/`     — kiến thức BỀN: mô hình tư duy, nguyên lý.
- `playbooks/`    — quy trình làm việc: "khi cần X thì làm theo các bước sau".
- `references/`   — link tới nguồn ngoài + GHI CHÚ CÁCH TRA (không chép số liệu).
- `experiments/`  — kết quả eval bạn TỰ chạy. Phần giá trị nhất: không ai có, không tra Google được.

## Mục lục hiện có
- concepts: routing · eval · model-tiers · moe · inference-providers
- playbooks: choose-cheap-model · build-eval-set
- references: leaderboards
