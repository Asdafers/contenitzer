#!/usr/bin/env python3
from src.lib.database import get_db_session
from src.models.uploaded_script import UploadedScript

with get_db_session() as db:
    scripts = db.query(UploadedScript).order_by(UploadedScript.upload_timestamp.desc()).limit(5).all()
    print('Recent uploaded scripts:')
    for s in scripts:
        print(f'ID: {s.id}, Name: {s.file_name}, Workflow: {s.workflow_id}')