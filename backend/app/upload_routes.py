import os
import re
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles

from .study_system import ClassNote, SessionStudy

UPLOAD_ROOT = Path(os.getenv('UPLOAD_ROOT', './uploads')).resolve()
CLASS_NOTE_ROOT = UPLOAD_ROOT / 'class-notes'
CLASS_NOTE_ROOT.mkdir(parents=True, exist_ok=True)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024
ALLOWED = {
    'application/pdf': 'pdf',
    'image/jpeg': 'photo',
    'image/png': 'photo',
    'image/webp': 'photo',
    'image/heic': 'photo',
    'image/heif': 'photo',
}


def mount_uploads(app):
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    app.mount('/uploads', StaticFiles(directory=str(UPLOAD_ROOT)), name='uploads')


def _safe_name(name: str) -> str:
    stem = Path(name or 'note').stem[:60]
    stem = re.sub(r'[^A-Za-z0-9_-]+', '-', stem).strip('-') or 'note'
    return stem


def build_upload_router(current_user):
    router = APIRouter()

    @router.post('/uploads/class-note')
    async def upload_class_note(
        file: UploadFile = File(...),
        exam: str = Form(...),
        subject: str = Form(...),
        topic: str = Form(...),
        title: str = Form(...),
        paper: str = Form(''),
        subtopic: str = Form(''),
        u=Depends(current_user),
    ):
        kind = ALLOWED.get((file.content_type or '').lower())
        if not kind:
            raise HTTPException(400, 'Only PDF/JPG/PNG/WEBP/HEIC files are allowed')
        ext = Path(file.filename or '').suffix.lower()
        if kind == 'pdf':
            ext = '.pdf'
        elif ext not in {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}:
            ext = '.jpg'
        user_dir = CLASS_NOTE_ROOT / str(u.id)
        user_dir.mkdir(parents=True, exist_ok=True)
        filename = f'{uuid.uuid4().hex}_{_safe_name(file.filename or title)}{ext}'
        destination = user_dir / filename
        size = 0
        try:
            with destination.open('wb') as out:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > MAX_UPLOAD_BYTES:
                        raise HTTPException(413, 'File is larger than 25 MB')
                    out.write(chunk)
        except Exception:
            destination.unlink(missing_ok=True)
            raise
        finally:
            await file.close()
        url = f'/uploads/class-notes/{u.id}/{filename}'
        s = SessionStudy()
        try:
            row = ClassNote(
                user_id=u.id,
                exam=exam,
                paper=paper,
                subject=subject,
                topic=topic,
                subtopic=subtopic,
                title=title,
                file_type=kind,
                file_url=url,
            )
            s.add(row)
            s.commit()
            s.refresh(row)
            return {'ok': True, 'id': row.id, 'file_type': kind, 'file_url': url}
        except Exception:
            s.rollback()
            destination.unlink(missing_ok=True)
            raise
        finally:
            s.close()

    return router
