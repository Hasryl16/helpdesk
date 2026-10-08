# HelpDesk Mini

Aplikasi ticketing multi-bisnis (multi-tenant). Customer membuka tiket keluhan, lalu tiket itu menjadi ruang chat real-time dengan agen dari bisnisnya. Data satu bisnis tidak pernah terlihat oleh bisnis lain.

| Lapisan | Teknologi |
|---|---|
| Frontend | Next.js 16 (App Router, TypeScript), Tailwind CSS, SWR |
| Backend | Python, FastAPI, SQLAlchemy 2, Alembic |
| Database | PostgreSQL 16 |
| Auth | JWT access + refresh token (PyJWT), password di-hash dengan bcrypt |
| Real-time | WebSocket bawaan FastAPI |

Fitur bonus yang dikerjakan: Docker Compose, test pytest (fokus isolasi antar-bisnis), upload lampiran gambar di chat.

## Menjalankan dengan Docker (paling cepat)

Butuh Docker dengan Docker Compose.

```bash
cp backend/.env.example backend/.env
# Ganti JWT_SECRET di backend/.env dengan string acak, misalnya hasil dari:
python3 -c "import secrets; print(secrets.token_hex(32))"

docker compose up --build -d
docker compose exec backend python -m app.seed
# Jika seed gagal dengan "relation ... does not exist", migrasi belum selesai: tunggu beberapa detik lalu ulangi.
```

- Aplikasi: http://localhost:3000
- Dokumentasi API (Swagger): http://localhost:8000/docs

Migrasi database berjalan otomatis saat container backend start.

## Menjalankan untuk development (tanpa Docker untuk backend dan frontend)

Butuh Python 3.11+, Node.js 20+, dan Docker (hanya untuk Postgres).

```bash
# 1. Database (Postgres di localhost:5433)
docker compose up -d db

# 2. Backend
cd backend
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env              # lalu isi JWT_SECRET
.venv/bin/alembic upgrade head
.venv/bin/python -m app.seed
.venv/bin/uvicorn app.main:app --reload       # http://localhost:8000

# 3. Frontend (terminal lain)
cd frontend
npm install
cp .env.example .env.local
npm run dev                       # http://localhost:3000
```

Backend harus berjalan dengan **satu worker** (lihat Catatan).

## Akun demo

Semua akun memakai password `password123`.

| Bisnis | Peran | Nama | Email |
|---|---|---|---|
| Toko Maju | Admin | Rina | admin@tokomaju.com |
| Toko Maju | Agent | Budi | agent@tokomaju.com |
| Toko Maju | Customer | Andi | customer1@tokomaju.com |
| Toko Maju | Customer | Sari | customer2@tokomaju.com |
| Klinik Sehat | Admin | Dewi | admin@kliniksehat.com |
| Klinik Sehat | Agent | Eko | agent@kliniksehat.com |
| Klinik Sehat | Customer | Fajar | customer1@kliniksehat.com |
| Klinik Sehat | Customer | Gita | customer2@kliniksehat.com |

Setiap bisnis punya dua tiket contoh: satu `open` milik customer1, dan satu `in_progress` milik customer2 yang sudah di-assign ke agent. Seed aman dijalankan ulang; bisnis yang sudah ada dilewati.

## Environment variable

Backend: `backend/.env` (contoh di `backend/.env.example`).

| Variable | Wajib | Default | Keterangan |
|---|---|---|---|
| `DATABASE_URL` | ya | – | URL SQLAlchemy, contoh `postgresql+psycopg://helpdesk:helpdesk@localhost:5433/helpdesk`. Docker Compose mengisinya sendiri untuk container backend. |
| `JWT_SECRET` | ya | – | Secret penanda tangan JWT. Isi dengan string acak yang panjang. |
| `ACCESS_TOKEN_MINUTES` | tidak | `15` | Umur access token |
| `REFRESH_TOKEN_DAYS` | tidak | `7` | Umur refresh token |
| `CORS_ORIGINS` | tidak | `http://localhost:3000` | Origin frontend, dipisah koma |
| `UPLOAD_DIR` | tidak | `uploads` | Folder penyimpanan lampiran gambar |

Frontend: `frontend/.env.local` (contoh di `frontend/.env.example`).

| Variable | Default | Keterangan |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | URL REST API |
| `NEXT_PUBLIC_WS_URL` | `ws://localhost:8000` | URL WebSocket |

## Test

```bash
cd backend
.venv/bin/pytest
```

Test memakai SQLite sementara, jadi tidak butuh Postgres. `tests/test_isolation.py` dan `tests/test_ws.py` berisi skenario isolasi antar-bisnis: menebak ID tiket bisnis lain, customer membuka tiket customer lain, dan WebSocket ke tiket yang bukan haknya.

## Struktur

```
backend/
  app/
    main.py        app FastAPI, CORS, format error JSON
    config.py      settings dari environment variable
    db.py          engine dan session database
    models.py      tabel businesses, users, tickets, messages
    schemas.py     schema request/response (Pydantic)
    security.py    hash password, buat/baca JWT
    deps.py        get_current_user, require_role
    realtime.py    room WebSocket per tiket
    routers/       endpoint HTTP dan WebSocket (tipis, hanya memanggil service)
    services/      logika bisnis dan filter tenant
    seed.py        data demo
  alembic/         migrasi database
  tests/           pytest
frontend/
  app/             halaman (App Router); app/(app)/ berisi halaman yang wajib login
  lib/             api client, user context, tipe data, hook WebSocket
  components/      komponen UI
```

## API

Dokumentasi lengkap ada di http://localhost:8000/docs.

| Method | Path | Peran | Fungsi |
|---|---|---|---|
| POST | `/auth/register-business` | publik | Buat bisnis + akun admin, langsung mengembalikan token |
| POST | `/auth/login` | publik | Login, mengembalikan access + refresh token |
| POST | `/auth/refresh` | publik (refresh token) | Terbitkan access token baru |
| GET | `/auth/me` | semua | User yang login + bisnisnya |
| GET | `/users` | admin | Daftar user di bisnisnya |
| POST | `/users` | admin | Buat akun agent atau customer |
| GET | `/tickets?status=` | semua | Daftar tiket sesuai peran, urut aktivitas terbaru |
| POST | `/tickets` | customer | Buat tiket + pesan pertama |
| GET | `/tickets/{id}` | sesuai akses | Detail tiket |
| PATCH | `/tickets/{id}` | admin, agent, customer (reopen) | Ubah status atau assignee |
| GET | `/tickets/{id}/messages` | sesuai akses | Riwayat pesan |
| POST | `/tickets/{id}/attachments` | sesuai akses | Upload gambar (multipart `file`) |
| GET | `/tickets/{id}/attachments/{message_id}` | sesuai akses | Ambil gambar |
| WS | `/ws/tickets/{id}?token=<access_token>` | sesuai akses | Kirim/terima pesan dan perubahan tiket |

Semua error memakai format `{"error": {"status": 404, "message": "Ticket not found"}}`:
401 belum login · 403 peran tidak berhak · 404 tidak ada atau milik bisnis lain · 409 konflik (email/nama bisnis sudah dipakai, transisi status tidak valid, tiket closed) · 413 file terlalu besar · 422 input tidak valid.

Protokol WebSocket:
- client → server: `{"body": "teks pesan"}`
- server → client: `{"type": "message", "message": {...}}`, `{"type": "ticket", "ticket": {...}}`, `{"type": "error", "message": "..."}`
- koneksi ditutup dengan code `4401` (token tidak valid) atau `4404` (tidak punya akses ke tiket)

Alur status: `open → in_progress → resolved → closed`, dengan jalur buka kembali `resolved → open`. Tiket `closed` terkunci: tidak bisa menerima pesan baru dan tidak bisa diubah lagi (409).

## Catatan

### Keputusan teknis
- **Multi-tenant dengan kolom `business_id`** (satu database, satu schema). Semua akses tiket lewat satu fungsi, `get_ticket_for_user` di `backend/app/services/tickets.py`, yang memfilter `business_id` (dan `customer_id` untuk customer). Tiket milik bisnis lain dan tiket yang tidak ada sama-sama menghasilkan 404, sehingga keberadaan data tidak bocor. REST, WebSocket, dan lampiran memakai fungsi yang sama.
- `business_id` dan `role` selalu diambil dari user di database berdasarkan `sub` di JWT, tidak pernah dari input client.
- `messages` tidak punya `business_id`: pesan hanya bisa diakses lewat tiketnya, yang sudah dicek lebih dulu.
- JWT menyimpan `type` (`access`/`refresh`) supaya refresh token tidak bisa dipakai sebagai access token.
- Pesan chat dikirim lewat WebSocket, disimpan ke database dulu, baru di-broadcast ke semua yang membuka tiket itu. Perubahan status/assignee lewat `PATCH /tickets/{id}`, lalu di-broadcast juga.
- Handler WebSocket membuka session database singkat untuk setiap operasi, karena koneksi WebSocket bisa hidup lama.
- Frontend: semua halaman adalah client component; token disimpan di `localStorage`; `apiFetch` otomatis memakai refresh token saat dapat 401, dan mengarahkan ke `/login` jika gagal.
- Logout melakukan full page reload supaya cache data user sebelumnya ikut terhapus.
- Lampiran gambar tidak di-serve sebagai file statis; gambar diambil lewat endpoint yang mengecek akses tiket. Jenis file dicek dari isi file (magic bytes), bukan dari header `Content-Type`.

### Tambahan dari model data minimal
- Kolom `messages.attachment_path` (boleh kosong) untuk lampiran gambar, lewat migrasi `0002`.
- Index `users.business_id` dan `messages (ticket_id, created_at)`.

### Asumsi
1. Admin juga boleh chat di tiket bisnisnya.
2. Agent boleh mengambil alih tiket yang sudah di-assign ke agent lain.
3. Staf (admin/agent) juga boleh membuka kembali tiket `resolved → open`.
4. Hanya user ber-role `agent` yang bisa menjadi assignee; admin meng-assign ke agent.
5. Kategori tiket berupa teks bebas (maksimal 50 karakter).
6. Duplikasi data dan transisi status tidak valid memakai `409 Conflict`.
7. Daftar bisnis langsung login (endpoint register mengembalikan token).
8. Admin tidak bisa membuat admin lain lewat `POST /users`.

### Trade-off dan batasan
- Room WebSocket disimpan di memori proses, jadi backend harus jalan dengan satu worker. Untuk banyak worker/server: Redis pub/sub.
- Token di `localStorage` rentan dicuri lewat XSS. Alternatif yang lebih aman: cookie httpOnly + pengecekan di `middleware`/`proxy` Next.js.
- Pengecekan login di sisi client, sehingga halaman sempat menampilkan "Loading..." sebelum redirect.
- Token WebSocket dikirim lewat query string (browser tidak bisa memasang header di WebSocket), sehingga ikut tercatat di log uvicorn. Risikonya dibatasi oleh umur access token yang hanya 15 menit.
- Token WebSocket hanya dicek saat connect. Jika koneksi putus, frontend reconnect dengan token terbaru.
- Refresh token stateless: tidak bisa dicabut sebelum kedaluwarsa.
- Login dengan email yang tidak terdaftar sedikit lebih cepat daripada password salah (bcrypt tidak dijalankan), jadi keberadaan email bisa ditebak dari waktu respons walau pesan error-nya sama. Perbaikannya: tetap jalankan bcrypt terhadap hash dummy.
- ID tiket berurutan dan global, sehingga sebuah bisnis bisa memperkirakan jumlah tiket di platform (isinya tetap tidak bisa diakses). Alternatif: UUID.
- Handler WebSocket memanggil database secara sync di dalam fungsi async; untuk beban tinggi sebaiknya dipindah ke threadpool atau memakai driver async.
- Perubahan tiket tidak memakai row lock: dua PATCH yang datang bersamaan (misalnya agent menutup dan customer membuka kembali) bisa saling menimpa. Perbaikannya: `SELECT ... FOR UPDATE` saat memuat tiket untuk diubah.
- Keunikan email dicek sebelum insert. Dua pendaftaran bersamaan dengan email yang sama bisa membuat salah satunya mendapat error 500, bukan 409; datanya tetap aman karena dijaga unique constraint di database.
- Test memakai SQLite, sedangkan aplikasi memakai Postgres.
- Lampiran disimpan di disk lokal (volume Docker). Alternatif: object storage seperti S3.
- Batas 5 MB dicek setelah upload diterima: FastAPI menyimpan file ke file sementara lebih dulu, juga untuk request tanpa login. Di produksi, batasi ukuran body di reverse proxy (misalnya `client_max_body_size` di nginx).

### Yang belum dikerjakan
- Fitur bonus lain: indikator mengetik dan status dibaca, badge pesan belum dibaca, pagination dan pencarian, notifikasi real-time di daftar tiket, rate limiting login, deploy online.
- Pencabutan refresh token (butuh tabel token atau denylist).
- Test otomatis untuk frontend; saat ini frontend diverifikasi dengan `npm run build` dan uji manual dua browser.
