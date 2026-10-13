# flow-video-bot: gói kiến thức cho bot làm video bằng Google Flow

Repo này chứa toàn bộ quy trình, quy tắc đã học, ví dụ và script để một AI agent mới làm video bằng Google Flow ngay, không cần dạy lại.

## Giao cho bot mới
1. Clone repo về máy của bot.
2. Bảo bot: **"Đọc AGENTS.md và làm theo."** (Claude Code tự đọc CLAUDE.md, bản sao của AGENTS.md.)
3. Bot cần: ffmpeg, Python + faster-whisper (xem `scripts/README.md`), truy cập Google Flow và Google Drive.

## Cấu trúc
```
AGENTS.md / CLAUDE.md          hướng dẫn cho AI agent
rules.md                       quy tắc đã học
skills/flow-video-pipeline/    SKILL.md: quy trình chi tiết
scripts/                       rough_cut.py dựng bản thô + requirements
examples/gioi-thieu-tro-li/    ví dụ kịch bản 3 cảnh, prompt, manifest
```
Không chứa video, mật khẩu hay thông tin tài khoản.
