from app.database import engine
from app import models

print("Peringatan: Menghapus semua tabel dan isinya...")
# 1. Menghapus semua tabel yang ada
models.Base.metadata.drop_all(bind=engine)

print("Membuat ulang tabel kosong...")
# 2. Membuat tabelnya kembali dari awal
models.Base.metadata.create_all(bind=engine)

print("SELESAI! Database kembali bersih.")