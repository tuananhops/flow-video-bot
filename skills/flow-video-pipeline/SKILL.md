---
name: flow-video-pipeline
description: >-
  Dùng khi khách yêu cầu làm video (quảng cáo, tuyên truyền, phim ngắn) bằng
  Google Flow: từ kịch bản đến bản thô trên Drive rồi bản hoàn chỉnh.
---
# Dây chuyền làm video bằng Google Flow

Trả lời khách bằng tiếng Việt, ngắn gọn. Không bỏ bước, không làm bước sau khi bước trước chưa được duyệt.

## Bước 1: Kịch bản (DỪNG chờ duyệt)
1. Đọc thông tin khách gửi (file docx hoặc tin nhắn). Nắm: mục đích, tổng thời lượng, phong cách, nhân vật, giọng nói, bối cảnh.
2. Nếu chưa có kịch bản thì viết theo yêu cầu. Chia thành các cảnh 8 giây (Flow tối đa 10 giây/clip). Video 3-5 phút cần khoảng 22-38 cảnh.
3. QUAN TRỌNG về thời lượng: lời thoại mỗi cảnh phải lấp kín cảnh, khoảng 20-24 chữ tiếng Việt cho cảnh 8 giây. Sau khi cắt khoảng lặng, tổng thời lượng phải bằng kịch bản. Khách không chấp nhận video ngắn hơn kịch bản.
4. Mỗi cảnh ghi: hình ảnh, hành động, lời thoại nguyên văn, giọng đọc.
5. Gửi kịch bản, DỪNG chờ khách xác nhận.

## Bước 2: Nhân vật, giọng, bối cảnh
- Hỏi/kiểm tra khách có nhân vật cố định, đặc điểm giọng nói, bối cảnh tham chiếu không.
- Nếu có: khách gửi ảnh khuôn mặt và ảnh bối cảnh. Trong Flow, tải ảnh cảnh lên mục Cảnh, tạo nhân vật từ ảnh mặt ở mục Nhân vật, dán đặc điểm giọng nói vào phần mô tả giọng nói của nhân vật.
- Nếu không: chuyển thẳng kịch bản thành prompt.

## Bước 3: Prompt và tạo clip trên Flow (flow.google.com)
- Mỗi cảnh một prompt tiếng Anh mô tả hình ảnh, ghi rõ 'Vertical 9:16', nhân vật nhất quán giữa các cảnh, 'speaks continuously for the whole 8 seconds in Vietnamese with <giọng>: "<lời thoại nguyên văn>"'. Ghi 'No background music, no on-screen text' trừ khi kịch bản cần.
- Chế độ thủ công (tắt chip Tác nhân), Video > Thành phần (gắn nhân vật/cảnh nếu có).
- CÀI ĐẶT BẮT BUỘC: tỉ lệ 9:16, độ phân giải 360p, số lượng x1, 8 giây. Model mặc định Omni 1.1 Flash (khoảng 6 credit/clip). Không dùng upscale trả phí.
- Tạo từng clip, đợi xong mới tạo tiếp. Tải về bản 'Kích thước gốc'.

## Bước 4: Bản thô (tự làm trên máy)
1. Phiên âm từng clip bằng faster-whisper (tiếng Việt, mốc thời gian theo từ), so với lời thoại kịch bản.
2. Cắt: khoảng lặng đầu/cuối, khoảng nghỉ > ~0.4 giây (chừa 0.1-0.15 giây đệm), chữ nói thừa sau câu thoại kịch bản. Không cắt vào giữa chữ. Fade âm 15 ms ở mỗi điểm cắt, giữ khớp hình tiếng (encode lại).
3. Ghép theo thứ tự, nâng lên 1080x1920 (lanczos + làm nét nhẹ), H.264 CRF 18, AAC 192k.
4. Tải lên Google Drive của khách/chủ bot vào thư mục 'Video Flow - Ban tho'. Gửi link, báo thời lượng, chữ phát âm sai, chỗ giật hình. DỪNG chờ duyệt.

## Bước 5: Hoàn thiện (sau khi duyệt bản thô)
- Phụ đề tiếng Việt phông đậm, viền, bóng. Từ khoá nhấn mạnh dịch vụ hoặc nỗi lo khách: đổi màu nổi và phóng to, nảy đúng lúc nói. Gửi danh sách từ khoá để duyệt trước.
- Nhạc nền miễn phí bản quyền (tự hạ nhỏ khi có thoại), hiệu ứng âm thanh: whoosh chuyển cảnh, pop khi chữ hiện, ding khi nhấn mạnh.
- Có thể dùng CapCut web nếu được cấp tài khoản Pro (CapCut PC không chạy trên Linux).
- Xuất bản cuối, tải lên Drive, gửi link.
