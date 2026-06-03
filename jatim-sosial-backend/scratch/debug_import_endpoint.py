import asyncio
import os
import sys

sys.path.append("/app")

from database import SessionLocal
import main
import models
from fastapi import UploadFile
import io

async def run_import():
    db = SessionLocal()
    try:
        # Clear existing tables first so we can see a fresh import!
        print("Clearing tables...")
        db.query(models.LogHistori).delete()
        db.query(models.KeluargaHistory).delete()
        db.query(models.Foto).delete()
        db.query(models.Perhitungan).delete()
        db.query(models.Keluarga).delete()
        db.commit()
        
        # Read the CSV file
        csv_path = "df_sample_10_skor.csv"
        with open(csv_path, "rb") as f:
            content = f.read()
            
        print("Simulating import...")
        # Create UploadFile-like object
        class MockFile:
            def __init__(self, content):
                self.file = io.BytesIO(content)
                self.filename = "df_sample_10_skor.csv"
            async def read(self):
                return content
            async def seek(self, offset):
                self.file.seek(offset)
                
        mock_file = MockFile(content)
        
        # Mock background tasks
        class MockBackgroundTasks:
            def add_task(self, func, *args, **kwargs):
                print(f"[Mock Background Task] Scheduled {func.__name__} with args {args}")
                
        bg_tasks = MockBackgroundTasks()
        
        # Get admin user
        admin = db.query(models.User).filter(models.User.username == "admin_jatim").first()
        if not admin:
            print("Admin user not found!")
            return
            
        # Call the actual import function!
        result = await main.import_csv(
            file=mock_file,
            background_tasks=bg_tasks,
            current_user=admin,
            db=db
        )
        
        print("\n--- IMPORT RESULT ---")
        print(f"Status: {result.get('status')}")
        print(f"Pesan: {result.get('pesan')}")
        print("\n--- LOG PROSES FOTO ---")
        for log in result.get("log_proses_foto", []):
            print(log)
            
        # Query the database to see what was saved in the foto table!
        fotos = db.query(models.Foto).all()
        print(f"\nSaved {len(fotos)} photos in database:")
        for f in fotos:
            print(f"Keluarga ID: {f.keluarga_id}, URL: {f.url_foto}, Original: {f.nama_file_asli}")
            
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_import())
