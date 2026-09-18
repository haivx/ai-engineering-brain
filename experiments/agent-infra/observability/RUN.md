# RUN.md — output terminal đã ghi lại

Môi trường: Python 3.9.6, chỉ dùng thư viện chuẩn, chạy từ thư mục này
(`experiments/agent-infra/observability/`). Mỗi khối bên dưới là stdout chính xác
của lệnh ghi phía trên nó (được capture ra file rồi dán nguyên văn, không gõ lại)
— một dòng ghi chú phía trên mỗi khối nói nó minh họa điều gì.

## 1. Lần chạy baseline (threshold = 0.0): log có cấu trúc + điểm eval

Minh họa: logging có cấu trúc chạy bên dưới một bài eval thật — mỗi bước của cả
18 case đều sinh ra một bản ghi JSONL trong `logs/run_baseline.jsonl`, và lần
chạy vẫn rút gọn về một con số (66,7%) ở ngay đầu.

```
$ python3 eval_harness.py --threshold 0.0 --tag baseline
run_id:        run-baseline-b02dafdf
tag:           baseline
threshold:     0.0
cases:         18
passed:        12
failed:        6
errored:       1
pass_rate:     66.7%
log:           logs/run_baseline.jsonl
result:        results/eval_baseline.json

case_id                      expected   predicted  pass   note
billing_invoice              billing    billing    PASS   
billing_generic              billing    billing    PASS   
billing_receipt              billing    billing    PASS   
billing_weak_single          billing    billing    PASS   
technical_login              technical  technical  PASS   
technical_timeout            technical  technical  PASS   
technical_password           technical  technical  PASS   
technical_weak_single        technical  technical  PASS   
account_profile              account    account    PASS   
account_signup               account    account    PASS   
account_delete               account    account    PASS   
account_weak_single          account    account    PASS   
unknown_greeting             unknown    billing    FAIL   
unknown_smalltalk            unknown    billing    FAIL   
unknown_incidental_delete    unknown    account    FAIL   
unknown_incidental_bill      unknown    billing    FAIL   
unknown_incidental_settings  unknown    account    FAIL   
malformed_none_input         None       None       FAIL   ERROR: AttributeError: 'NoneType' object has no attribute 'lower'
```

## 2. Lần chạy đã thay đổi (threshold = 0.2): cùng bộ case, đổi đúng một biến

Minh họa: chỉ `--threshold` thay đổi (0.0 -> 0.2). Cùng 18 case, cùng router.py,
cùng đường code, khác kết quả ở những case nằm sát ngưỡng.

```
$ python3 eval_harness.py --threshold 0.2 --tag stricter
run_id:        run-stricter-97c9cd79
tag:           stricter
threshold:     0.2
cases:         18
passed:        14
failed:        4
errored:       1
pass_rate:     77.8%
log:           logs/run_stricter.jsonl
result:        results/eval_stricter.json

case_id                      expected   predicted  pass   note
billing_invoice              billing    billing    PASS   
billing_generic              billing    billing    PASS   
billing_receipt              billing    billing    PASS   
billing_weak_single          billing    unknown    FAIL   
technical_login              technical  technical  PASS   
technical_timeout            technical  technical  PASS   
technical_password           technical  technical  PASS   
technical_weak_single        technical  unknown    FAIL   
account_profile              account    account    PASS   
account_signup               account    account    PASS   
account_delete               account    account    PASS   
account_weak_single          account    unknown    FAIL   
unknown_greeting             unknown    unknown    PASS   
unknown_smalltalk            unknown    unknown    PASS   
unknown_incidental_delete    unknown    unknown    PASS   
unknown_incidental_bill      unknown    unknown    PASS   
unknown_incidental_settings  unknown    unknown    PASS   
malformed_none_input         None       None       FAIL   ERROR: AttributeError: 'NoneType' object has no attribute 'lower'
```

## 3. So sánh trước/sau: con số, không phải cảm giác

Minh họa: nâng ngưỡng confidence từ 0.0 lên 0.2 cải thiện pass rate về mặt ròng
(+11,1 điểm), nhưng không miễn phí — nó đánh đổi 3 true positive có tín hiệu yếu
(`*_weak_single`) để lấy 5 false positive được sửa trên input thực sự lạc đề
(`unknown_*`). Bảng so sánh cho thấy cả phán quyết ròng LẪN sự đánh đổi cụ thể,
chỉ từ các con số, không cần đọc lại log thô ở bước này.

```
$ python3 compare_runs.py --before baseline --after stricter
Comparing: baseline (threshold=0.0) -> stricter (threshold=0.2)

metric               before      after      delta
passed                   12         14         +2
failed                    6          4         -2
errored                   1          1         +0
pass_rate            66.7%     77.8%    +11.1%

Verdict: IMPROVED (+11.1% pass rate)

Per-case flips (8 of 18 cases changed outcome):
case_id                      direction      before_pred  after_pred   expected
billing_weak_single          PASS -> FAIL   billing      unknown      billing
technical_weak_single        PASS -> FAIL   technical    unknown      technical
account_weak_single          PASS -> FAIL   account      unknown      account
unknown_greeting             FAIL -> PASS   billing      unknown      unknown
unknown_smalltalk            FAIL -> PASS   billing      unknown      unknown
unknown_incidental_delete    FAIL -> PASS   account      unknown      unknown
unknown_incidental_bill      FAIL -> PASS   billing      unknown      unknown
unknown_incidental_settings  FAIL -> PASS   account      unknown      unknown
```

## 4. Kiểm tra khả năng tái lập: pass rate ổn định qua các lần chạy lại

Minh họa: ở đây thậm chí không cần seeding nào, vì router có zero ngẫu nhiên
trong logic quyết định — pass_rate giống nhau từng bit qua các lần chạy lại.
(`run_id` khác nhau ở mỗi lần chạy nhờ `uuid.uuid4()`, nhưng đó là một định danh
để nối dữ liệu, không phải một phần của logic được chấm điểm — ràng buộc "phần
bất định phải được seed để pass-rate ổn định" được thỏa mãn một cách hiển nhiên
bằng cách không có phần bất định nào trên đường đi được chấm điểm.) Các artifact
của lần chạy lại đã bị xóa ngay sau phép kiểm tra này; chúng không thuộc bản
chứng minh được commit.

```
$ python3 eval_harness.py --threshold 0.0 --tag baseline_rerun > /dev/null 2>&1
$ python3 -c "... compare results/eval_baseline.json vs results/eval_baseline_rerun.json pass_rate ..."
baseline pass_rate: 0.6667
baseline_rerun pass_rate: 0.6667
REPRODUCIBLE
```

## 5. Lập luận thật: định vị một lỗi trong vài giây

Cả hai lần chạy ở trên đều cho thấy `malformed_none_input` fail với cùng một dòng
ghi chú: `ERROR: AttributeError: 'NoneType' object has no attribute 'lower'`.
Dòng ghi chú đó chỉ tồn tại vì bản tóm tắt trên console của harness tình cờ hiển
thị nó ra. Hai phép đối chứng bên dưới cho thấy vì sao *log có cấu trúc nằm bên
dưới* mới là phần thực sự quan trọng, chứ không phải dòng print trên console.

### 5a. Một con số pass-rate trần trụi cho bạn biết gì: không gì cả

Minh họa: `naive_baseline_demo.py` chạy đúng 18 case đó qua đúng `router.py` đó,
bọc trong một lệnh `try/except Exception: print("case failed")` trần trụi. Nó đạt
đúng điểm 12/18, nhưng sáu lỗi thì không phân biệt nổi: năm lỗi là phân loại sai,
một lỗi là crash hẳn vì input xấu, và output này không cho bạn biết cái nào là
cái nào, nói gì tới case_id nào hay bước pipeline nào. Bạn sẽ phải đi cắm print
rồi chạy lại mới phát hiện ra rằng cú crash tồn tại như một loại thất bại riêng.

```
$ python3 naive_baseline_demo.py
case failed
case failed
case failed
case failed
case failed
case failed
12/18 passed
```

### 5b. Log có cấu trúc cho bạn biết gì: đúng case, đúng bước, đúng nguyên nhân, chỉ trong một lệnh grep

Minh họa: một lệnh grep theo `case_id` trả lời trong vài giây: case nào đã vỡ
(`malformed_none_input`), nó vỡ ở bước pipeline nào (`normalize`, `step_seq: 1`
— thậm chí chưa từng chạm tới `tokenize`/`score`/`decide`), exception chính xác
là gì, và rằng nó fail trong chưa tới 0,01ms (nên không phải treo). `status:
"error"` cũng khiến nó phân biệt được một cách máy móc với năm bản ghi `status:
"ok"` của các case chạy trót lọt nhưng đoán sai nhãn — thứ mà cả output print của
`naive_baseline_demo.py` lẫn một con số pass-rate trần trụi đều không phân biệt nổi.

```
$ grep '"case_id": "malformed_none_input"' logs/run_baseline.jsonl | python3 -m json.tool --json-lines
{
    "case_id": "malformed_none_input",
    "duration_ms": 0.0026,
    "error": "AttributeError: 'NoneType' object has no attribute 'lower'",
    "input": "None",
    "output": null,
    "run_id": "run-baseline-b02dafdf",
    "status": "error",
    "step": "normalize",
    "step_seq": 1,
    "timestamp": "2026-09-07T16:42:12.303277+00:00"
}
{
    "case_id": "malformed_none_input",
    "duration_ms": null,
    "error": "AttributeError: 'NoneType' object has no attribute 'lower'",
    "input": "None",
    "output": "{'case_id': 'malformed_none_input', 'expected': None, 'predicted': None, 'confidence': None, 'passed': False, 'errored': True, 'failed_step': 'normalize', 'error': \"AttributeError: 'NoneType' object h...<truncated>",
    "run_id": "run-baseline-b02dafdf",
    "status": "error",
    "step": "case_result",
    "step_seq": 2,
    "timestamp": "2026-09-07T16:42:12.303292+00:00"
}
```

## 6. Các file lần chạy này tạo ra

```
$ wc -l logs/run_baseline.jsonl logs/run_stricter.jsonl
      88 logs/run_baseline.jsonl
      88 logs/run_stricter.jsonl
     176 total
```

88 bản ghi mỗi lần chạy = 17 case sạch x 5 bản ghi mỗi case (normalize, tokenize,
score, decide, case_result) = 85, + 1 case lỗi định dạng x 2 bản ghi (lỗi ở
normalize, case_result) = 87, + 1 bản ghi run_summary = 88.

Các file khác trong thư mục này: `router.py` (hệ thống được kiểm thử),
`eval_harness.py` (bộ ghi log có cấu trúc + trình chạy eval), `compare_runs.py`
(diff trước/sau), `naive_baseline_demo.py` (phần đối chứng cho §5a),
`eval_cases.json` (18 case), `logs/run_baseline.jsonl` /
`logs/run_stricter.jsonl` (log có cấu trúc), `results/eval_baseline.json`
/ `results/eval_stricter.json` (tóm tắt eval + kết quả theo từng case).
