import json
import os
import re
import shutil
import subprocess
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from PIL import Image, ExifTags
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


def _format_bytes(size: int) -> str:
    """Format bytes into a human-readable string (KB, MB, GB)."""
    if size < 1024:
        return f"{size} B"
    for unit in ["KB", "MB", "GB", "TB"]:
        size /= 1024.0
        if size < 1024.0:
            return f"{size:.2f} {unit}"
    return f"{size:.2f} PB"


def _format_bitrate(bps: Optional[Any]) -> str:
    """Format bit rate into kbps or Mbps."""
    if bps is None:
        return "N/A"
    try:
        val = float(bps)
        if val <= 0:
            return "N/A"
        if val >= 1_000_000:
            return f"{val / 1_000_000:.2f} Mbps"
        elif val >= 1000:
            return f"{val / 1000:.1f} kbps"
        return f"{int(val)} bps"
    except (TypeError, ValueError):
        return str(bps)


def _format_duration(seconds: Optional[Any]) -> str:
    """Format duration in seconds into HH:MM:SS or MM:SS."""
    if seconds is None:
        return "N/A"
    try:
        sec = float(seconds)
        if sec < 0:
            return "N/A"
        td = timedelta(seconds=sec)
        total_seconds = int(td.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = sec % 60
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:05.2f} ({sec:.2f}s)"
        else:
            return f"{minutes:02d}:{secs:05.2f} ({sec:.2f}s)"
    except (TypeError, ValueError):
        return str(seconds)


def _eval_fraction(frac_str: str) -> Optional[float]:
    """Safely evaluate fractional rate like 24000/1001 or 30/1 into float."""
    if not frac_str or frac_str == "0/0":
        return None
    try:
        if "/" in frac_str:
            num, den = frac_str.split("/", 1)
            den_f = float(den)
            if den_f != 0:
                return float(num) / den_f
        return float(frac_str)
    except (TypeError, ValueError):
        return None


def _dms_to_decimal(dms, ref: str) -> Optional[float]:
    """Convert GPS degrees/minutes/seconds tuple to decimal degrees."""
    try:
        if isinstance(dms, (list, tuple)) and len(dms) >= 3:
            deg = float(dms[0])
            minute = float(dms[1])
            sec = float(dms[2])
            dec = deg + (minute / 60.0) + (sec / 3600.0)
            if ref in ("S", "W", "s", "w"):
                dec = -dec
            return dec
    except Exception:
        pass
    return None


class MediaInspectorMixin:
    """Deep media inspection tool for video, audio, and image files."""

    def _run_ffprobe(self, abs_path: str) -> Optional[Dict[str, Any]]:
        """Run ffprobe on file and return parsed JSON metadata if available."""
        ffprobe_bin = shutil.which("ffprobe") or "ffprobe"
        cmd = [
            ffprobe_bin,
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            "-show_chapters",
            abs_path,
        ]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
            )
            if res.returncode == 0 and res.stdout.strip():
                return json.loads(res.stdout)
        except Exception:
            pass
        return None

    def _inspect_image_pillow(self, abs_path: str) -> Dict[str, Any]:
        """Extract deep image metadata and EXIF via Pillow."""
        if not PIL_AVAILABLE:
            return {}
        try:
            with Image.open(abs_path) as img:
                width, height = img.size
                megapixels = round((width * height) / 1_000_000, 2)
                mode = img.mode
                img_format = img.format or Path(abs_path).suffix.lstrip(".").upper()
                dpi = img.info.get("dpi")
                is_animated = getattr(img, "is_animated", False)
                n_frames = getattr(img, "n_frames", 1)

                has_alpha = False
                if mode in ("RGBA", "LA", "PA") or "transparency" in img.info:
                    has_alpha = True

                bit_depth = 8
                if mode in ("I;16", "I;16B", "I;16L", "I;16S", "RGB;16", "RGBA;16"):
                    bit_depth = 16
                elif mode in ("F", "I"):
                    bit_depth = 32

                # EXIF extraction
                exif_data = {}
                raw_exif = img.getexif()
                if raw_exif:
                    for tag_id, value in raw_exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        if isinstance(value, bytes):
                            try:
                                value = value.decode("utf-8", errors="replace").strip("\x00 ")
                            except Exception:
                                value = f"<binary data: {len(value)} bytes>"
                        exif_data[tag_name] = value

                    if hasattr(raw_exif, "get_ifd"):
                        try:
                            gps_ifd = raw_exif.get_ifd(ExifTags.IFD.GPSInfo)
                            if gps_ifd:
                                gps_parsed = {}
                                for g_tag, g_val in gps_ifd.items():
                                    g_name = ExifTags.GPSTAGS.get(g_tag, str(g_tag))
                                    gps_parsed[g_name] = g_val
                                exif_data["GPSInfo"] = gps_parsed
                        except Exception:
                            pass

                camera = exif_data.get("Model") or exif_data.get("Make")
                lens = exif_data.get("LensModel")
                exposure = exif_data.get("ExposureTime")
                if exposure and isinstance(exposure, (int, float)):
                    if exposure < 1 and exposure > 0:
                        exposure = f"1/{round(1/exposure)}s"
                    else:
                        exposure = f"{exposure}s"
                fnumber = exif_data.get("FNumber")
                if fnumber:
                    fnumber = f"f/{float(fnumber):.1f}"
                iso = exif_data.get("ISOSpeedRatings") or exif_data.get("PhotographicSensitivity")
                focal_length = exif_data.get("FocalLength")
                if focal_length:
                    focal_length = f"{float(focal_length):.1f} mm"
                focal_35mm = exif_data.get("FocalLengthIn35mmFilm")
                if focal_35mm:
                    focal_35mm = f"{focal_35mm} mm (35mm eq.)"

                date_taken = (
                    exif_data.get("DateTimeOriginal")
                    or exif_data.get("DateTimeDigitized")
                    or exif_data.get("DateTime")
                )

                gps_str = None
                gps_info = exif_data.get("GPSInfo")
                if isinstance(gps_info, dict):
                    lat_dms = gps_info.get("GPSLatitude")
                    lat_ref = gps_info.get("GPSLatitudeRef", "N")
                    lon_dms = gps_info.get("GPSLongitude")
                    lon_ref = gps_info.get("GPSLongitudeRef", "E")
                    if lat_dms and lon_dms:
                        lat_dec = _dms_to_decimal(lat_dms, lat_ref)
                        lon_dec = _dms_to_decimal(lon_dms, lon_ref)
                        if lat_dec is not None and lon_dec is not None:
                            gps_str = f"{lat_dec:.6f}, {lon_dec:.6f} (Lat: {lat_dec:.6f}° {lat_ref}, Lon: {lon_dec:.6f}° {lon_ref})"

                return {
                    "format": img_format,
                    "width": width,
                    "height": height,
                    "megapixels": megapixels,
                    "mode": mode,
                    "bit_depth": bit_depth,
                    "dpi": dpi,
                    "has_alpha": has_alpha,
                    "is_animated": is_animated,
                    "n_frames": n_frames,
                    "camera": camera,
                    "lens": lens,
                    "exposure": exposure,
                    "fnumber": fnumber,
                    "iso": iso,
                    "focal_length": focal_length,
                    "focal_35mm": focal_35mm,
                    "date_taken": date_taken,
                    "gps": gps_str,
                    "exif_raw": exif_data,
                }
        except Exception:
            return {}

    def inspect_media(self, path: str, detailed: bool = True) -> str:
        """Inspect media file technical metadata (video, audio, image)."""
        if not path or not str(path).strip():
            return "[Error: inspect_media requires a 'path' argument]"

        if self.is_protected(path):
            return self._deny(path)

        abs_path = os.path.abspath(os.path.join(self.cwd, path))
        if not os.path.exists(abs_path):
            return f"[Error: File '{path}' does not exist]"
        if os.path.isdir(abs_path):
            return f"[Error: Path '{path}' is a directory, not a media file]"

        file_stat = os.stat(abs_path)
        file_size_bytes = file_stat.st_size
        file_size_str = _format_bytes(file_size_bytes)
        file_ext = Path(abs_path).suffix.lower()

        video_exts = {
            ".mp4", ".mkv", ".avi", ".mov", ".webm", ".flv", ".wmv",
            ".m4v", ".ts", ".mts", ".m2ts", ".vob", ".ogv", ".3gp", ".prores"
        }
        audio_exts = {
            ".mp3", ".flac", ".wav", ".ogg", ".m4a", ".aac", ".wma",
            ".aiff", ".aif", ".alac", ".opus", ".ape", ".ac3", ".dts"
        }
        image_exts = {
            ".png", ".jpg", ".jpeg", ".webp", ".gif", ".tiff", ".tif",
            ".svg", ".ico", ".bmp", ".heic", ".heif", ".avif", ".raw",
            ".cr2", ".nef", ".arw", ".dng"
        }

        media_type = "unknown"
        if file_ext in video_exts:
            media_type = "video"
        elif file_ext in audio_exts:
            media_type = "audio"
        elif file_ext in image_exts:
            media_type = "image"

        ffprobe_data = self._run_ffprobe(abs_path)
        pillow_data = self._inspect_image_pillow(abs_path) if (media_type == "image" or file_ext in image_exts) else {}

        if not ffprobe_data and not pillow_data:
            return (
                f"[inspect_media '{path}']\n"
                f"File: {os.path.basename(path)}\n"
                f"Size: {file_size_str} ({file_size_bytes} bytes)\n"
                f"Status: No specialized media metadata could be extracted (ffprobe/Pillow did not recognize the file stream)."
            )

        if ffprobe_data and media_type == "unknown":
            streams = ffprobe_data.get("streams", [])
            has_video = any(s.get("codec_type") == "video" for s in streams)
            has_audio = any(s.get("codec_type") == "audio" for s in streams)
            if has_video and not pillow_data:
                media_type = "video"
            elif has_audio:
                media_type = "audio"
            elif pillow_data:
                media_type = "image"

        format_info = ffprobe_data.get("format", {}) if ffprobe_data else {}
        duration_sec = format_info.get("duration")
        overall_bitrate = format_info.get("bit_rate")
        container_format = format_info.get("format_long_name") or format_info.get("format_name") or file_ext.lstrip(".")

        report = [f"# 🎬 Media Inspection: `{os.path.basename(path)}`\n"]
        report.append(f"- **File Path:** `{abs_path}`")
        report.append(f"- **Media Category:** **{media_type.upper()}**")
        report.append(f"- **File Size:** {file_size_str} ({file_size_bytes:,} bytes)")
        if container_format:
            report.append(f"- **Container / Format:** {container_format}")
        if duration_sec:
            report.append(f"- **Duration:** {_format_duration(duration_sec)}")
        if overall_bitrate:
            report.append(f"- **Overall Bitrate:** {_format_bitrate(overall_bitrate)}")

        # --- VIDEO STREAMS ---
        if ffprobe_data:
            video_streams = [s for s in ffprobe_data.get("streams", []) if s.get("codec_type") == "video"]
            main_videos = [s for s in video_streams if s.get("disposition", {}).get("attached_pic", 0) == 0] or video_streams
            if main_videos and media_type != "image":
                report.append("\n## 📹 Video Stream(s)")
                for idx, vs in enumerate(main_videos, 1):
                    codec = vs.get("codec_name", "unknown").upper()
                    profile = vs.get("profile", "")
                    codec_str = f"{codec} ({profile})" if profile else codec
                    width = vs.get("width")
                    height = vs.get("height")
                    res_str = f"{width}x{height}" if width and height else "N/A"
                    dar = vs.get("display_aspect_ratio") or vs.get("sample_aspect_ratio")
                    fps_val = _eval_fraction(vs.get("r_frame_rate", "")) or _eval_fraction(vs.get("avg_frame_rate", ""))
                    fps_str = f"{fps_val:.3f} fps" if fps_val else "N/A"
                    v_bitrate = _format_bitrate(vs.get("bit_rate"))
                    pix_fmt = vs.get("pix_fmt", "N/A")
                    color_space = vs.get("color_space") or vs.get("colorspace", "N/A")
                    color_primaries = vs.get("color_primaries", "N/A")
                    color_transfer = vs.get("color_transfer", "N/A")
                    bits_raw = vs.get("bits_per_raw_sample") or (10 if "10" in pix_fmt else 8 if "8" in pix_fmt else "N/A")

                    report.append(f"\n### Video Stream #{idx}")
                    report.append(f"- **Codec:** `{codec_str}`")
                    report.append(f"- **Resolution:** `{res_str}`" + (f" (Aspect Ratio: `{dar}`)" if dar else ""))
                    report.append(f"- **Frame Rate:** `{fps_str}`")
                    report.append(f"- **Stream Bitrate:** `{v_bitrate}`")
                    report.append(f"- **Pixel Format & Chroma:** `{pix_fmt}`")
                    report.append(f"- **Bit Depth / HDR:** `{bits_raw}-bit` (Color Space: `{color_space}`, Primaries: `{color_primaries}`, Transfer: `{color_transfer}`)")

            # --- AUDIO STREAMS ---
            audio_streams = [s for s in ffprobe_data.get("streams", []) if s.get("codec_type") == "audio"]
            if audio_streams:
                report.append("\n## 🔊 Audio Stream(s)")
                for idx, audio_s in enumerate(audio_streams, 1):
                    a_codec = audio_s.get("codec_name", "unknown").upper()
                    a_profile = audio_s.get("profile", "")
                    a_codec_str = f"{a_codec} ({a_profile})" if a_profile else a_codec
                    sample_rate = audio_s.get("sample_rate")
                    sr_str = f"{sample_rate} Hz" if sample_rate else "N/A"
                    channels = audio_s.get("channels", "N/A")
                    ch_layout = audio_s.get("channel_layout", "")
                    ch_str = f"{channels} channels ({ch_layout})" if ch_layout else f"{channels} channels"
                    a_bitrate = _format_bitrate(audio_s.get("bit_rate"))
                    a_bits = audio_s.get("bits_per_sample") or audio_s.get("bits_per_raw_sample")
                    bits_str = f"{a_bits}-bit" if a_bits else ""
                    lang = audio_s.get("tags", {}).get("language", "und")
                    title = audio_s.get("tags", {}).get("title", "")

                    report.append(f"\n### Audio Stream #{idx}" + (f" [{lang.upper()}]" if lang != "und" else ""))
                    report.append(f"- **Codec:** `{a_codec_str}`" + (f" ({bits_str})" if bits_str else ""))
                    report.append(f"- **Sample Rate:** `{sr_str}`")
                    report.append(f"- **Channels:** `{ch_str}`")
                    report.append(f"- **Bitrate:** `{a_bitrate}`")
                    if title:
                        report.append(f"- **Track Title:** {title}")

            # --- SUBTITLES ---
            sub_streams = [s for s in ffprobe_data.get("streams", []) if s.get("codec_type") == "subtitle"]
            if sub_streams:
                report.append("\n## 💬 Subtitle Tracks")
                for idx, sub_s in enumerate(sub_streams, 1):
                    s_codec = sub_s.get("codec_name", "unknown").upper()
                    s_lang = sub_s.get("tags", {}).get("language", "und")
                    s_title = sub_s.get("tags", {}).get("title", "")
                    default_flag = " [Default]" if sub_s.get("disposition", {}).get("default") else ""
                    report.append(f"- **Track #{idx}:** `{s_codec}` | Lang: `{s_lang.upper()}`{default_flag}" + (f" ({s_title})" if s_title else ""))

            # --- CHAPTERS ---
            chapters = ffprobe_data.get("chapters", [])
            if chapters:
                report.append(f"\n## 📑 Chapters ({len(chapters)} found)")
                for idx, ch in enumerate(chapters[:15], 1):
                    start = _format_duration(ch.get("start_time"))
                    end = _format_duration(ch.get("end_time"))
                    ch_title = ch.get("tags", {}).get("title", f"Chapter {idx}")
                    report.append(f"- **{ch_title}:** `{start}` -> `{end}`")
                if len(chapters) > 15:
                    report.append(f"- *(+{len(chapters) - 15} more chapters)*")

        # --- IMAGE DETAILS & EXIF ---
        if pillow_data:
            report.append("\n## 🖼 Image & Optics Properties")
            w = pillow_data.get("width")
            h = pillow_data.get("height")
            mp = pillow_data.get("megapixels")
            report.append(f"- **Resolution:** `{w} x {h}` pixels (**{mp} Megapixels**)")
            report.append(f"- **Color Mode:** `{pillow_data.get('mode')}` ({pillow_data.get('bit_depth')}-bit)")
            if pillow_data.get("dpi"):
                report.append(f"- **DPI:** `{pillow_data.get('dpi')}`")
            report.append(f"- **Alpha Channel (Transparency):** {'Yes' if pillow_data.get('has_alpha') else 'No'}")
            if pillow_data.get("is_animated"):
                report.append(f"- **Animation:** Yes ({pillow_data.get('n_frames')} frames)")

            # EXIF / Optics
            exif_highlights = []
            if pillow_data.get("camera"):
                exif_highlights.append(f"- **Camera / Device:** `{pillow_data['camera']}`")
            if pillow_data.get("lens"):
                exif_highlights.append(f"- **Lens:** `{pillow_data['lens']}`")
            if pillow_data.get("exposure") or pillow_data.get("fnumber") or pillow_data.get("iso"):
                exp_parts = []
                if pillow_data.get("exposure"):
                    exp_parts.append(f"Shutter: {pillow_data['exposure']}")
                if pillow_data.get("fnumber"):
                    exp_parts.append(f"Aperture: {pillow_data['fnumber']}")
                if pillow_data.get("iso"):
                    exp_parts.append(f"ISO: {pillow_data['iso']}")
                if pillow_data.get("focal_length"):
                    exp_parts.append(f"Focal Length: {pillow_data['focal_length']}")
                if pillow_data.get("focal_35mm"):
                    exp_parts.append(f"({pillow_data['focal_35mm']})")
                exif_highlights.append(f"- **Exposure Settings:** `{', '.join(exp_parts)}`")
            if pillow_data.get("date_taken"):
                exif_highlights.append(f"- **Date Taken:** `{pillow_data['date_taken']}`")
            if pillow_data.get("gps"):
                exif_highlights.append(f"- **📍 GPS Coordinates:** `{pillow_data['gps']}`")

            if exif_highlights:
                report.append("\n### 📷 Camera & EXIF Metadata")
                report.extend(exif_highlights)

        # --- METADATA TAGS ---
        tags = format_info.get("tags", {}) if format_info else {}
        if tags:
            tag_keys = [
                "title", "artist", "album", "date", "year", "genre",
                "track", "composer", "album_artist", "comment", "encoder",
                "copyright", "replaygain_track_gain", "bpm"
            ]
            found_tags = {}
            for k, v in tags.items():
                low_k = k.lower()
                if low_k in tag_keys or detailed:
                    found_tags[k] = str(v).strip()

            if found_tags:
                report.append("\n## 🏷 Metadata Tags")
                for k, v in found_tags.items():
                    report.append(f"- **{k}:** {v}")

        return "\n".join(report)
