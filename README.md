# ai-engineering-brain

Một "bộ não thứ hai" (knowledge base) cho **AI Engineering**.
Nó vừa là một Git repo, vừa là một Obsidian vault (chỉ cần "Open folder as vault").

## Knowledge base này dùng để làm gì
- Một nơi để tra lại những gì bạn đã học, được sắp xếp gọn gàng.
- **Lớp context cho Claude Code**: vì mọi thứ đều là markdown nằm trong repo, agent có thể đọc được.
  Ví dụ: "áp dụng routing như mô tả trong `concepts/routing.md`" → agent đọc file đó và làm theo.

## Nguyên tắc vàng
> Lưu **cách tư duy** và **cách tra cứu** — đừng lưu **con số**.

Giá token, model tốt nhất hiện tại, leaderboard → chúng lỗi thời chỉ sau vài tuần. TUYỆT ĐỐI không chép vào đây.
Mô hình tư duy (routing, eval, tiers...) → chúng không đổi. ĐÓ mới là thứ đáng viết ra.
Với những thứ hay thay đổi: chỉ lưu *quy trình tra cứu* + link (xem `references/`).

## Cấu trúc
- `concepts/`     — kiến thức BỀN: mô hình tư duy, nguyên lý.
- `playbooks/`    — quy trình làm việc: "khi cần X thì làm theo các bước này".
- `references/`   — link tới nguồn bên ngoài + GHI CHÚ CÁCH TRA CỨU (không chép số liệu).
- `experiments/`  — kết quả eval do CHÍNH BẠN chạy. Phần giá trị nhất: không ai khác có, không Google ra được.

## Mục lục hiện tại
- concepts: routing · eval · model-tiers · moe · inference-providers
- concepts/agent-infra: state · memory · determinism · observability · recovery · context-engineering · tool-calling · orchestration · guardrails
- concepts/data-engineering: tabular-ops · sampling-and-balance · chunking-and-embedding · golden-dataset · data-quality-checks
- playbooks: choose-cheap-model · build-eval-set
- references: leaderboards · data-engineering-tools
