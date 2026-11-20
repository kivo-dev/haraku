# HARAKO Backend — نسخهٔ ۰٫۱ (هسته)

FastAPI · SQLAlchemy 2 · PostgreSQL (روی لپ‌تاپ: SQLite) · Alembic · Docker Compose

> **وضعیت صادقانه:** این کد در محیطی نوشته شد که نصب بسته‌ها بسته بود. منطق (جست‌وجوی فارسی، فاصله، امتیازدهی پیشنهاد، تبدیل پاسخ‌ها) با `pytest` تست شده؛ ولی **خود سرور (FastAPI + دیتابیس) هنوز یک بار هم اجرا نشده.** بار اول ممکن است خطای کوچکی بدهد؛ متن خطا را بفرست تا درست شود.

## اجرا روی کامپیوتر خودت
```bash
python -m venv .venv && source .venv/bin/activate      # ویندوز: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                    # بعد فایل .env را ویرایش کن
python -m app.seed                                      # ورود داده‌های نمونه
uvicorn app.main:app --reload                           # http://localhost:8000/docs
pytest                                                  # تست‌ها
```
با Docker: `docker compose up --build` و بار اول `docker compose exec api python -m app.seed`.

## وصل کردن به فرانتند
در پوشهٔ فرانتند، فایل `.env.local`:
```
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/v1
```
`CORS_ORIGINS` در `.env` بکند باید آدرس فرانتند باشد (پیش‌فرض `http://localhost:3000`).

## آدرس‌ها (همه GET، پیشوند `/v1`)
| آدرس | کار |
|---|---|
| `/places?category=&q=&lat=&lng=&radius_km=&limit=&offset=` | فهرست مکان‌ها. با `lat`+`lng` بر اساس فاصله مرتب می‌شود و `distanceKm` پر می‌شود («نزدیک من») |
| `/places/{id}` | جزئیات یک مکان (با `images`) |
| `/categories` | دسته‌ها |
| `/suggestions?limit=&lat=&lng=&exclude=&seed=` | «پیشنهادهای ما». هر بار می‌تواند چیز تازه بدهد (بدون کش). قواعد: `app/scoring.py` |
| `/opportunities?sector=&q=` ، `/opportunities/{id}` | فرصت‌های اقتصادی |
| `/route?from_lat=&from_lng=&to_place=` (یا `to_lat`/`to_lng`) | مسیر ماشین از نشان. بدون کلید: خطای ۵۰۳ |
| `/health` (بدون `/v1`) | سالم بودن سرور و دیتابیس |

شکل پاسخ‌ها همان است که `normalize.ts` در فرانتند می‌فهمد.

## داده را چطور وارد کنم؟ (تا وقتی پنل مدیریت نیامده)
فایل `data/seed.json` را ویرایش کن و دوباره `python -m app.seed` بزن (بر اساس `id` اضافه یا به‌روز می‌کند).
هر مکان: `id` (همان اسم فایل عکس)، `category`، `name/area/summary` (`fa`+`en`)، **`lat`/`lng`**، `featured`، `status` (`published` تا دیده شود)، `verification`.
**مختصات دقیق مهم‌ترین چیز است:** بدون آن «نزدیک من»، فاصله و مسیر برای آن مکان کار نمی‌کند.
`image` را خالی بگذار تا فرانتند از `public/images/places/<id>.jpg` استفاده کند.
چهار مکان و چهار فرصت داخل فایل **نمونهٔ ساختگی** هستند (`source: seed-sample`، بدون مختصات). قبل از انتشار: `python -m app.seed --purge-samples`.

## نشان (فقط مسیر‌یابی، فعلاً)
- در `.env`: `NESHAN_SERVICE_KEY=` را پر کن. **کلید سرویس فقط سمت بکند.** هرگز در فرانتند، چت، یا Git نگذارش. (مخزن شما Public است؛ `.env` در `.gitignore` هست. اگر کلیدی جایی لو رفت، عوضش کن.)
- نشان، تا جایی که می‌دانم، برای نقشه (مرورگر/SDK) و برای سرویس‌ها (سرور) کلید جدا می‌دهد. کلید نقشه را بعداً به دامنهٔ اپ محدود کن.
- **آدرس و پاسخ نشان از حافظه نوشته شده و با مستندات تطبیق داده نشده.** یک بار اجرا کن: `python -m app.services.neshan_check 39.29,44.51 39.39,44.38` و خروجی JSON (که کلید ندارد) را بفرست.
- هیچ داده‌ای از نشان در دیتابیس ذخیره نمی‌شود (شرایط استفاده هنوز بررسی نشده).
- درخواست مسیر برای هر IP در دقیقه محدود است (`ROUTE_REQUESTS_PER_MINUTE`)، چون سهمیه‌ٔ نشان پول/محدودیت دارد.

## مهاجرت دیتابیس (Alembic) — برای PostgreSQL واقعی
در حالت `APP_ENV=dev` جدول‌ها خودکار ساخته می‌شوند. برای انتشار:
```bash
APP_ENV=prod
alembic revision --autogenerate -m "init"     # یک بار، فایل ساخته‌شده را بخوان
alembic upgrade head
```

## پنل مدیریت (`/admin`)
یک مدیر، ورود با نام کاربری و رمز از `.env`. **تا وقتی این سه خط پر نباشد پنل خاموش است** (در لاگ سرور دلیلش نوشته می‌شود).
```
ADMIN_USERNAME=اسم-دلخواه
ADMIN_PASSWORD=رمز-حداقل-۱۰-کاراکتر
ADMIN_SECRET_KEY=یک-رشته-تصادفی-حداقل-۳۲-کاراکتر
```
رشتهٔ تصادفی: `python3 -c "import secrets;print(secrets.token_hex(32))"`. بعد از تغییر `.env` سرور را دوباره روشن کن و برو `http://localhost:8000/admin`.
- مکان جدید: «مکان‌ها» ← New. `id` یک اسم انگلیسی کوتاه و بدون فاصله است (مثل `chashmeh-soraya`) و **همان اسم فایل عکس** در فرانتند است. فقط مکانی که `status = published` باشد در اپ دیده می‌شود.
- `lat` و `lng` را (اعشاری، مثل 39.29 و 44.51) پر کن؛ بدون آن «نزدیک من» و مسیر کار نمی‌کند.
- `image_url` را خالی بگذار تا فرانتند از `public/images/places/<id>.jpg` بخواند. آپلود عکس از پنل هنوز نیست.
- فیلدهای جست‌وجو خودکار ساخته می‌شوند.
- بعد از ریست رمز یا تلاش اشتباه: ۵ ورود اشتباه پشت‌سرهم ← ۱۰ دقیقه بسته می‌شود. برای اینترنت واقعی حتماً HTTPS بگذار.
- فرانتند صفحه‌ها را تا ۵ دقیقه کش می‌کند؛ تغییر ممکن است با کمی تأخیر دیده شود.

## چه چیزهایی عمداً هنوز نیست
حساب کاربری، دستیار هوشمند/MCP، QR، مسیر پیاده، جست‌وجو و Nearby از خود نشان، PostGIS.
هر کدام جای مشخصی دارد؛ ساختار ماژولار است و چیزی بازنویسی نمی‌شود.

## ساختار
`app/models.py` جدول‌ها · `app/routers/` آدرس‌ها · `app/scoring.py` پیشنهادها · `app/search_text.py` جست‌وجوی فارسی ·
`app/geo.py` فاصله · `app/services/neshan.py` آداپتر نشان · `app/seed.py` ورود داده · `tests/`
