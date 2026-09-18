# Harness render/verify cho diagram

Đây là công cụ dùng chung cho các thư mục `experiments/agent-infra/*/` để thỏa
mãn bước 3 trong phương pháp làm việc ở `planning/PLAN.md`: mọi diagram Mermaid
đều phải được **render và xác nhận bằng mắt** trước khi phần văn xuôi concept
phụ thuộc vào nó được viết ra. Nó tồn tại vì Mermaid mặc định không báo lỗi ồn
ào — xem "Vì sao một ảnh chụp màu xanh không phải bằng chứng" bên dưới.

## Ở đây có gì

- `mermaid.min.js` — mermaid v11, được vendor từ
  `https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js` để việc render
  chạy offline/tái lập được và không thêm dependency nào vào repo này.
- `render.mjs` — một script Node không phụ thuộc gì. Cho một file `.mmd`, nó sinh
  ra một trang HTML tự chứa, nạp bản mermaid đã vendor, render diagram, và phơi ra
  một kết quả có cấu trúc `window.__harness` cùng một banner trạng thái to rõ.
- `fixtures/` — một diagram chắc chắn đúng và một diagram **chắc chắn hỏng**, kèm
  bản HTML/PNG đã render được commit lại làm bằng chứng rằng harness thật sự phân
  biệt được hai trường hợp (xem "Tự kiểm thử" bên dưới). Hãy giữ fixture này — một
  bộ kiểm chứng chưa bao giờ được chứng minh là biết báo lỗi thì không đáng tin.

## Cách chạy nó trên một file `.mmd`

```bash
# 1. Sinh trang render cạnh file .mmd (hoặc ở đâu tùy bạn) — script luôn
#    tham chiếu mermaid.min.js đã vendor bằng đường dẫn tương đối.
node experiments/agent-infra/_diagram-harness/render.mjs \
  experiments/agent-infra/state/diagram.mmd \
  experiments/agent-infra/state/_render.html

# 2. Serve nó lên. Trình duyệt Playwright MCP dùng trong session này bị CHẶN
#    giao thức file:, nên bạn không thể browser_navigate thẳng tới một URL
#    file:// — nó sẽ báo "Access to file: protocol is blocked".
#    Hãy serve thư mục qua HTTP thường (static server nào cũng được;
#    python3 thì luôn có sẵn ở đây):
python3 -m http.server 8743 --directory experiments/agent-infra
```

Sau đó, với các tool Playwright MCP:

3. `browser_navigate` tới `http://127.0.0.1:8743/state/_render.html` (đường dẫn
   tính tương đối so với thư mục bạn truyền vào `--directory`).
4. `browser_evaluate` với một hàm poll cho tới khi xong, ví dụ:
   ```js
   async () => {
     for (let i = 0; i < 50; i++) {
       if (window.__harness && window.__harness.done) return window.__harness;
       await new Promise(r => setTimeout(r, 100));
     }
     return { ...window.__harness, timedOut: true };
   }
   ```
   Kiểm tra `result.status === "ok"` và `result.error === null`. Đồng thời xác
   nhận URL của trang trong chính response của tool khớp với file bạn vừa điều
   hướng tới (xem cảnh báo "Trình duyệt dùng chung" bên dưới) trước khi tin kết quả.
5. `browser_console_messages` (mức `error`) như một lớp kiểm tra thứ hai — trang
   cũng dồn các lời gọi `console.error` vào `window.__harness.consoleErrors`,
   nhưng kiểm tra console của chính trình duyệt là một phép đối chiếu độc lập tốt.
6. `browser_take_screenshot` để lưu ảnh PNG. Hãy làm **sau** bước 4/5 để chắc
   rằng thứ bạn chụp là trạng thái đã hoàn tất và đã được đánh giá, chứ không
   phải một trang render dở.
7. Tự nhìn ảnh chụp và so với những gì `NOTES.md`/`RUN.md` của experiment khẳng
   định — harness bắt được lỗi "cái này không parse được", chứ không bắt được
   "diagram này nói sai về experiment". Phép kiểm tra thứ hai đó là bước quan sát
   bằng mắt của con người/agent, không phải thứ `render.mjs` tự động hóa được.

## Vì sao một ảnh chụp màu xanh không phải bằng chứng

Mermaid không ném ra exception JS thông thường với phần lớn lỗi cú pháp.
`mermaid.render()` có thể resolve "thành công" trong khi đoạn SVG nó trả về chỉ
là đồ họa báo lỗi của chính mermaid — một icon quả bom và dòng chữ "Syntax error
in text". Một script chỉ kiểm tra "có chụp được ảnh mà trang không sập không" sẽ
vui vẻ báo một diagram hỏng là pass.

`render.mjs` phòng chuyện này theo hai cách:
1. Nó bọc lời gọi render trong try/catch — `mermaid.render()` *thường xuyên* có
   reject khi gặp lỗi parse (xem `fixtures/known-broken.*`), và thông điệp được
   ném ra sẽ được ghi vào `window.__harness.error`.
2. Độc lập với (1), nó soi nội dung văn bản và class phần tử của SVG kết quả để
   tìm các dấu hiệu lỗi của chính mermaid ("Syntax error in text", `.error-icon`,
   v.v.) — đây là nhánh bắt được những lỗi mà mermaid nuốt chửng thay vì ném ra.

Cả hai nhánh đều đặt `window.__harness.status = "fail"` và tô đỏ banner trên
trang kèm thông điệp lỗi cụ thể, nên thất bại là ồn ào cả trong kết quả có cấu
trúc *lẫn* trong chính ảnh chụp.

## Tự kiểm thử (vì sao bạn có thể tin công cụ này)

`fixtures/known-good.mmd` (một flowchart 3 node) và `fixtures/known-broken.mmd`
(cố ý viết sai) đều đã được chạy qua toàn bộ quy trình ở trên. Kết quả đã commit:

| fixture | `window.__harness.status` | banner trong ảnh chụp |
|---|---|---|
| `known-good.html` / `.png` | `"ok"` | màu xanh "RENDER: OK" |
| `known-broken.html` / `.png` | `"fail"` | màu đỏ "RENDER: FAIL — exception: Parse error on line 2: ..." kèm đồ họa lỗi icon quả bom của chính mermaid |

Trong trường hợp này mermaid thật sự đã ném exception với fixture hỏng (bắt được
bởi nhánh 1 ở trên); nhánh dự phòng soi SVG (nhánh 2) tồn tại cho những tình huống
— đã được ghi nhận trong chính task sinh ra harness này — mà mermaid resolve mà
không ném gì nhưng vẫn phát ra đồ họa báo lỗi nội tuyến. Một bộ kiểm chứng không
thể chứng minh là biết báo lỗi thì chẳng chứng minh được gì, nên cặp fixture này
được commit lại chứ không vứt đi sau khi dùng.

## Giới hạn đã biết: trình duyệt Playwright MCP là dùng chung

Các tool MCP `browser_navigate` / `browser_evaluate` / `browser_take_screenshot`
trong session này điều khiển **chung một instance trình duyệt** — nếu một agent
khác trong nhóm điều hướng nó vào giữa lệnh `browser_navigate` của bạn và lời gọi
tool kế tiếp, lời gọi kế tiếp của bạn có thể âm thầm chạy trên trang *của họ*.
Luôn đối chiếu dòng `Page URL:` trong response của từng tool MCP với URL bạn mong
đợi trước khi tin output của `browser_evaluate`/`browser_take_screenshot`. Nếu
không khớp, hãy điều hướng lại và thử lại.

## Vì sao không có batch runner viết bằng script (không qua MCP)

Task cho phép "một cách tiếp cận node/playwright bằng script ... cho việc chạy
theo lô" như một lựa chọn thay thế, nhưng để thực sự chạy Node API của Playwright
thì cần `require("playwright")`, mà cái đó lại cần cài package npm `playwright`
vào một chỗ mà cơ chế phân giải module của `node` nhìn thấy — nghĩa là một thư mục
`node_modules/` bên trong repo này, đúng thứ chúng ta được dặn là không được thêm
vào. (`npx -p playwright node script.js` *không* phơi package ra cho một lời gọi
`require()` thường — đã kiểm chứng bằng thử nghiệm — nên không có cách nào lấy
Node API chỉ từ cache của npx.) Các tool Playwright MCP vốn đã có sẵn cho agent
này không gặp vấn đề đó, nên chúng là cách duy nhất được dùng ở đây.
