# scripts/rough_cut.py

Dựng bản thô từ các clip Flow: phiên âm (faster-whisper), so với lời thoại kịch bản, cắt chữ thừa + khoảng lặng (>0.4s, đệm 0.12/0.15s, fade 15ms), ghép, nâng 1080x1920 (lanczos + unsharp), H.264 CRF 18, AAC 192k.

## Cài đặt
```bash
sudo apt install -y ffmpeg
python3 -m venv .venv && . .venv/bin/activate
pip install -r scripts/requirements.txt
```

## Dùng
```bash
python scripts/rough_cut.py examples/gioi-thieu-tro-li/manifest.json -o ban_tho.mp4
# --model large-v3 (chính xác hơn), --dry-run (chỉ in đoạn cắt), --noise-db -35, --min-silence 0.4
```
Manifest JSON/YAML: `{"clips": [{"path": "...mp4", "line": "lời thoại kịch bản"}]}` (đường dẫn tương đối theo thư mục manifest).
Script in ra lời nghe được vs kịch bản để báo khách chỗ phát âm sai, và tổng thời lượng.
