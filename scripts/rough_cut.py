#!/usr/bin/env python3
"""rough_cut.py - Dựng bản thô từ các clip Google Flow.

Mỗi clip: phiên âm bằng faster-whisper (mốc thời gian theo từ), so với lời thoại
kịch bản, bỏ chữ nói thừa sau câu thoại, cắt khoảng lặng (ffmpeg silencedetect),
rồi ghép tất cả, nâng lên 1080x1920 (lanczos + unsharp), H.264 CRF 18, AAC 192k.

Manifest (JSON hoặc YAML):
  {"clips": [{"path": "clip1.mp4", "line": "Lời thoại cảnh 1"}, ...]}
  (hoặc trực tiếp một list các {path, line}). Đường dẫn tương đối tính theo thư mục manifest.

Dùng: python rough_cut.py manifest.json -o ban_tho.mp4 [--model medium] [--dry-run]
"""
import argparse, difflib, json, math, os, re, subprocess, sys, unicodedata

def load_manifest(p):
    txt = open(p, encoding="utf-8").read()
    if p.endswith((".yaml", ".yml")):
        import yaml
        data = yaml.safe_load(txt)
    else:
        data = json.loads(txt)
    clips = data["clips"] if isinstance(data, dict) else data
    base = os.path.dirname(os.path.abspath(p))
    out = []
    for c in clips:
        path = c.get("path") or c.get("clip")
        out.append({"path": path if os.path.isabs(path) else os.path.join(base, path),
                    "line": c.get("line") or c.get("expected") or ""})
    return out

def norm(w):
    w = unicodedata.normalize("NFC", w.lower())
    return re.sub(r"[^\w]", "", w)

def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", path], capture_output=True, text=True, check=True)
    return float(r.stdout.strip())

def silences(path, db, mind):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af",
                        f"silencedetect=noise={db}dB:d={mind}", "-f", "null", "-"],
                       capture_output=True, text=True)
    out, start = [], None
    for l in r.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", l)
        if m: start = float(m.group(1))
        m = re.search(r"silence_end: ([\d.]+)", l)
        if m and start is not None: out.append((start, float(m.group(1)))); start = None
    if start is not None: out.append((start, 1e9))
    return out

def transcribe(model, path, lang):
    # tự giải mã bằng ffmpeg (tránh lỗi phiên bản PyAV)
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768.0
    segs, _ = model.transcribe(audio, language=lang, word_timestamps=True, beam_size=5)
    return [(w.word.strip(), w.start, w.end) for s in segs for w in s.words if w.word.strip()]

def speech_window(words, line):
    """Khoảng [start, end] chứa lời thoại kịch bản; bỏ chữ thừa trước/sau."""
    if not words: return None
    if not line.strip(): return words[0][1], words[-1][2]
    exp = [norm(w) for w in line.split() if norm(w)]
    got = [norm(w[0]) for w in words]
    sm = difflib.SequenceMatcher(None, got, exp, autojunk=False)
    matched = [i for b in sm.get_matching_blocks() for i in range(b.a, b.a + b.size)]
    if not matched: return words[0][1], words[-1][2]
    first, last = min(matched), max(matched)
    # nhận thêm chữ không khớp nằm sát sau chữ khớp cuối nếu kịch bản còn chữ chưa khớp (phiên âm sai)
    exp_matched = max(b.b + b.size for b in sm.get_matching_blocks() if b.size) 
    extra = len(exp) - exp_matched
    while extra > 0 and last + 1 < len(words) and words[last + 1][1] - words[last][2] < 0.4:
        last += 1; extra -= 1
    return words[first][1], words[last][2]

def segments(win, sil, dur, pad_edge, pad_in, gap):
    s0, e0 = win
    regions, cur = [], s0
    for a, b in sil:
        if b <= s0 or a >= e0: continue
        if b - a < gap: continue
        if a > cur: regions.append([cur, a])
        cur = max(cur, b)
    if cur < e0: regions.append([cur, e0])
    out = []
    for i, (a, b) in enumerate(regions):
        a -= pad_edge if i == 0 else pad_in
        b += pad_edge if i == len(regions) - 1 else pad_in
        out.append([max(0, a), min(dur, b)])
    merged = []
    for a, b in out:
        if merged and a <= merged[-1][1]: merged[-1][1] = max(merged[-1][1], b)
        else: merged.append([a, b])
    return merged

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("manifest"); ap.add_argument("-o", "--output", default="ban_tho.mp4")
    ap.add_argument("--model", default="medium", help="faster-whisper model (medium, large-v3, ...)")
    ap.add_argument("--lang", default="vi"); ap.add_argument("--device", default="auto")
    ap.add_argument("--compute-type", default="int8")
    ap.add_argument("--noise-db", type=float, default=-35); ap.add_argument("--min-silence", type=float, default=0.4)
    ap.add_argument("--pad-edge", type=float, default=0.12); ap.add_argument("--pad-internal", type=float, default=0.15)
    ap.add_argument("--fade", type=float, default=0.015); ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--width", type=int, default=1080); ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--crf", type=int, default=18); ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    clips = load_manifest(a.manifest)
    from faster_whisper import WhisperModel
    model = WhisperModel(a.model, device=a.device, compute_type=a.compute_type)
    F = a.fps
    fl = lambda t: math.floor(t * F + 1e-6) / F
    ce = lambda t: math.ceil(t * F - 1e-6) / F
    fc, n, total, report = [], 0, 0.0, []
    for ci, c in enumerate(clips):
        dur = duration(c["path"])
        words = transcribe(model, c["path"], a.lang)
        heard = " ".join(w[0] for w in words)
        win = speech_window(words, c["line"])
        if win is None:
            print(f"[cảnh {ci+1}] KHÔNG nghe thấy lời thoại, bỏ qua", file=sys.stderr); continue
        segs = segments(win, silences(c["path"], a.noise_db, a.min_silence), dur,
                        a.pad_edge, a.pad_internal, a.min_silence)
        rep = {"clip": os.path.basename(c["path"]), "heard": heard, "expected": c["line"], "segments": []}
        for s, e in segs:
            s, e = fl(s), min(ce(e), dur); d = e - s
            if d <= 2 * a.fade: continue
            total += d; rep["segments"].append([round(s, 3), round(e, 3)])
            fc.append(f"[{ci}:v]trim=start={s:.6f}:end={e:.6f},setpts=PTS-STARTPTS[v{n}]")
            fc.append(f"[{ci}:a]atrim=start={s:.6f}:end={e:.6f},asetpts=PTS-STARTPTS,"
                      f"afade=t=in:d={a.fade},afade=t=out:st={d-a.fade:.6f}:d={a.fade}[a{n}]")
            n += 1
        report.append(rep)
    print(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"Tổng thời lượng dự kiến: {total:.2f}s")
    if a.dry_run or n == 0: return
    fc.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[vc][ac]")
    fc.append(f"[vc]scale={a.width}:{a.height}:flags=lanczos+accurate_rnd+full_chroma_int,"
              "unsharp=5:5:0.5:5:5:0.0,setsar=1,format=yuv420p[vo]")
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for c in clips: cmd += ["-i", c["path"]]
    cmd += ["-filter_complex", ";".join(fc), "-map", "[vo]", "-map", "[ac]", "-c:v", "libx264",
            "-preset", "slow", "-crf", str(a.crf), "-r", str(F), "-profile:v", "high", "-c:a", "aac",
            "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", a.output]
    subprocess.run(cmd, check=True)
    print(f"Đã xuất {a.output}: {duration(a.output):.2f}s")

if __name__ == "__main__":
    main()
