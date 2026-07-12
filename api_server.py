"""
健身数据 API 服务
为 MkDocs 静态站提供数据读写接口，数据存储在 data/ 目录下的 JSON 文件中。
"""
import json
import os
import csv
import io
import uuid
from datetime import datetime
from pathlib import Path

import shutil

from fastapi import FastAPI, HTTPException, Query, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel
from typing import Optional

# ---------- 配置 ----------
DATA_DIR = Path(__file__).parent / "data"
TRAINING_FILE = DATA_DIR / "training_records.json"
METRICS_FILE = DATA_DIR / "body_metrics.json"
PHOTO_DIR = DATA_DIR / "photos"
PHOTO_META_FILE = DATA_DIR / "photo_meta.json"
PHOTO_DIR.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_MB = 10

app = FastAPI(title="健身数据 API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- 工具 ----------
def load_json(path: Path) -> list:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


# ---------- 数据模型 ----------
class Exercise(BaseModel):
    name: str
    sets: Optional[int] = None
    reps: Optional[str] = ""       # "12,10,8,6" 或 "12"
    weight: Optional[str] = ""     # "20kg" 或 ""
    rpe: Optional[str] = ""        # "8" 或 "力竭"
    notes: Optional[str] = ""


class TrainingRecord(BaseModel):
    id: str = ""
    date: str                     # "2026-06-22"
    training_day: str             # "A" / "B" / "C"
    exercises: list[Exercise]
    feeling: Optional[int] = None # 1-10
    cardio_type: Optional[str] = ""
    cardio_duration: Optional[int] = None  # 分钟
    notes: Optional[str] = ""


class BodyMetric(BaseModel):
    id: str = ""
    date: str                     # "2026-06-22"
    waist: Optional[float] = None        # 腰围 cm
    arm: Optional[float] = None          # 臂围 cm
    weight: Optional[float] = None       # 体重 kg
    systolic_bp: Optional[int] = None    # 收缩压 mmHg
    diastolic_bp: Optional[int] = None   # 舒张压 mmHg
    bench_press: Optional[float] = None  # 卧推 kg
    squat: Optional[float] = None        # 深蹲 kg
    deadlift: Optional[float] = None     # 硬拉 kg
    pull_ups: Optional[int] = None       # 引体向上 次数
    grip_strength: Optional[float] = None  # 握力 kg
    plank: Optional[int] = None          # 平板支撑 秒
    notes: Optional[str] = ""


# ---------- 训练记录 API ----------
@app.get("/fitness/training-records")
def get_training_records(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    records = load_json(TRAINING_FILE)
    records.sort(key=lambda r: r.get("date", ""), reverse=True)
    total = len(records)
    return {"total": total, "data": records[offset : offset + limit]}


@app.post("/fitness/training-records")
def add_training_record(record: TrainingRecord):
    if not record.id:
        record.id = uuid.uuid4().hex[:8]
    records = load_json(TRAINING_FILE)
    records.append(record.model_dump())
    save_json(TRAINING_FILE, records)
    return {"ok": True, "id": record.id}


@app.delete("/fitness/training-records/{record_id}")
def delete_training_record(record_id: str):
    records = load_json(TRAINING_FILE)
    new_records = [r for r in records if r.get("id") != record_id]
    if len(new_records) == len(records):
        raise HTTPException(404, "记录不存在")
    save_json(TRAINING_FILE, new_records)
    return {"ok": True}


# ---------- 身体指标 API ----------
@app.get("/fitness/body-metrics")
def get_body_metrics(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    records = load_json(METRICS_FILE)
    records.sort(key=lambda r: r.get("date", ""), reverse=True)
    total = len(records)
    return {"total": total, "data": records[offset : offset + limit]}


@app.post("/fitness/body-metrics")
def add_body_metric(metric: BodyMetric):
    if not metric.id:
        metric.id = uuid.uuid4().hex[:8]
    records = load_json(METRICS_FILE)
    # 同一天已有记录则更新
    existing = next((r for r in records if r.get("date") == metric.date), None)
    if existing:
        records.remove(existing)
    records.append(metric.model_dump())
    save_json(METRICS_FILE, records)
    return {"ok": True, "id": metric.id}


@app.delete("/fitness/body-metrics/{record_id}")
def delete_body_metric(record_id: str):
    records = load_json(METRICS_FILE)
    new_records = [r for r in records if r.get("id") != record_id]
    if len(new_records) == len(records):
        raise HTTPException(404, "记录不存在")
    save_json(METRICS_FILE, new_records)
    return {"ok": True}


# ---------- 导出 API ----------
def to_csv(records: list, columns: list, column_headers: list) -> str:
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(column_headers)
    for r in records:
        row = [r.get(col, "") for col in columns]
        writer.writerow(row)
    return output.getvalue()


@app.get("/fitness/export/training")
def export_training(format: str = Query("csv", regex="^(csv|json)$")):
    records = load_json(TRAINING_FILE)
    records.sort(key=lambda r: r.get("date", ""))
    if format == "json":
        return records

    columns = ["date", "training_day", "feeling", "cardio_type", "cardio_duration", "notes"]
    headers = ["日期", "训练日", "感受", "有氧类型", "有氧时长", "备注"]
    # 展开每个动作到单独行
    rows = []
    for r in records:
        if r.get("exercises"):
            for ex in r["exercises"]:
                row = {
                    "date": r.get("date", ""),
                    "training_day": r.get("training_day", ""),
                    "feeling": r.get("feeling", ""),
                    "cardio_type": r.get("cardio_type", ""),
                    "cardio_duration": r.get("cardio_duration", ""),
                    "notes": r.get("notes", ""),
                    "exercise": ex.get("name", ""),
                    "sets": ex.get("sets", ""),
                    "reps": ex.get("reps", ""),
                    "weight": ex.get("weight", ""),
                    "rpe": ex.get("rpe", ""),
                }
                rows.append(row)
    csv_content = to_csv(
        rows,
        ["date", "training_day", "exercise", "sets", "reps", "weight", "rpe", "feeling", "cardio_type", "cardio_duration", "notes"],
        ["日期", "训练日", "动作", "组数", "次数", "重量", "RPE", "感受", "有氧类型", "有氧时长", "备注"],
    )
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''%E8%AE%AD%E7%BB%83%E8%AE%B0%E5%BD%95.csv"},
    )


@app.get("/fitness/export/body-metrics")
def export_body_metrics(format: str = Query("csv", regex="^(csv|json)$")):
    records = load_json(METRICS_FILE)
    records.sort(key=lambda r: r.get("date", ""))
    if format == "json":
        return records

    columns = ["date", "weight", "waist", "arm", "systolic_bp", "diastolic_bp", "bench_press", "squat", "deadlift", "pull_ups", "grip_strength", "plank", "notes"]
    headers = ["日期", "体重(kg)", "腰围(cm)", "臂围(cm)", "收缩压", "舒张压", "卧推(kg)", "深蹲(kg)", "硬拉(kg)", "引体向上(次)", "握力(kg)", "平板支撑(秒)", "备注"]
    csv_content = to_csv(records, columns, headers)
    return StreamingResponse(
        io.BytesIO(csv_content.encode("utf-8-sig")),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename*=UTF-8''%E8%BA%AB%E4%BD%93%E6%8C%87%E6%A0%87.csv"},
    )


# ---------- 照片 API ----------
@app.get("/fitness/photos")
def list_photos():
    meta = load_json(PHOTO_META_FILE)
    meta.sort(key=lambda r: r.get("date", ""), reverse=True)
    return {"total": len(meta), "data": meta}


@app.post("/fitness/photos")
def upload_photo(
    file: UploadFile = File(...),
    date: str = Query(""),
    title: str = Query(""),
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(400, "仅支持图片格式")
    content = file.file.read()
    if len(content) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(400, f"图片大小不能超过 {MAX_UPLOAD_MB}MB")

    # 按日期组织目录
    upload_date = date or datetime.now().strftime("%Y-%m-%d")
    year_month = upload_date[:7].replace("-", "/")  # 2026/06
    year = upload_date[:4]
    month = upload_date[5:7]
    dir_path = PHOTO_DIR / year / month
    dir_path.mkdir(parents=True, exist_ok=True)

    # 避免重名
    safe_name = file.filename or "photo.jpg"
    stem, ext = os.path.splitext(safe_name)
    ts = datetime.now().strftime("%H%M%S")
    save_name = f"{stem}_{ts}{ext}"
    file_path = dir_path / save_name
    with open(file_path, "wb") as f:
        f.write(content)

    # 保存元数据
    record = {
        "id": uuid.uuid4().hex[:8],
        "date": upload_date,
        "title": title,
        "filename": save_name,
        "path": f"{year}/{month}/{save_name}",
        "size": len(content),
        "created": datetime.now().isoformat(),
    }
    meta = load_json(PHOTO_META_FILE)
    meta.append(record)
    save_json(PHOTO_META_FILE, meta)
    return {"ok": True, **record}


@app.get("/fitness/photos/{path:path}")
def serve_photo(path: str):
    full_path = PHOTO_DIR / path
    if not full_path.resolve().is_relative_to(PHOTO_DIR.resolve()):
        raise HTTPException(403, "路径非法")
    if not full_path.exists():
        raise HTTPException(404, "图片不存在")
    return FileResponse(full_path)


@app.delete("/fitness/photos/{photo_id}")
def delete_photo(photo_id: str):
    meta = load_json(PHOTO_META_FILE)
    target = next((r for r in meta if r.get("id") == photo_id), None)
    if not target:
        raise HTTPException(404, "记录不存在")
    # 删除文件
    file_path = PHOTO_DIR / target["path"]
    if file_path.exists():
        file_path.unlink()
    # 删除元数据
    meta = [r for r in meta if r.get("id") != photo_id]
    save_json(PHOTO_META_FILE, meta)
    return {"ok": True}
