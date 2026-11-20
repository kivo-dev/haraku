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

## چه چیزهایی عمداً هنوز نیست
پنل مدیریت (مرحلهٔ ۲)، حساب کاربری، دستیار هوشمند/MCP، QR، مسیر پیاده، جست‌وجو و Nearby از خود نشان، PostGIS.
هر کدام جای مشخصی دارد؛ ساختار ماژولار است و چیزی بازنویسی نمی‌شود.

## ساختار
`app/models.py` جدول‌ها · `app/routers/` آدرس‌ها · `app/scoring.py` پیشنهادها · `app/search_text.py` جست‌وجوی فارسی ·
`app/geo.py` فاصله · `app/services/neshan.py` آداپتر نشان · `app/seed.py` ورود داده · `tests/`

## دستیار هوشمند گردشگری (`app/ai/`)
ماژولی داخل همین بک‌اند (بدون میکروسرویس). مدل فقط از طریق **ابزارهای کنترل‌شده** به داده‌ی HARAKO و مسیریابی نشان می‌رسد؛ SQL، کلید یا فایل نمی‌بیند.

**وضعیت صادقانه:** منطق هسته (اعتبارسنجی ابزارها، جست‌وجوی فارسی/انگلیسی، ارکستریتور، حافظه‌ی گفتگو، ترتیب برنامه‌ی سفر، تبدیل پیام برای Anthropic/OpenAI، retry، حالت خرابی) با ۳۵ تست `unittest` اجرا و سبز شد. **این‌ها هنوز اجرا نشده‌اند:** لایه‌ی FastAPI (`app/ai/router.py`)، `DbTourismData` (روی دیتابیس واقعی)، و ارتباط با سرویس واقعی LLM و نشان (کلید و شبکه نبود).

### فعال‌سازی
در `.env` (تا `AI_PROVIDER` خالی است دستیار خاموش است و بقیه‌ی برنامه عادی کار می‌کند؛ پاسخ دستیار حالت «جست‌وجوی ساده» می‌گیرد):
```
AI_PROVIDER=anthropic          # یا openai_compatible
AI_MODEL=<نام مدل از پنل ارائه‌دهنده>
AI_API_KEY=<کلید، فقط سمت سرور>
AI_BASE_URL=                   # اختیاری (مثلاً سرور محلی سازگار با OpenAI)
```
بررسی: `GET /v1/assistant/status` → `{"enabled": true, ...}` (بدون هیچ راز).

### آدرس‌ها
`POST /v1/assistant/chat`
```json
{"message": "سه ساعت وقت دارم، جای تاریخی و طبیعت پیشنهاد بده",
 "conversation_id": null, "language": "fa",
 "location": {"lat": 0.0, "lng": 0.0}}
```
`location` فقط وقتی کاربر اجازه داده بفرست. پاسخ: `reply` (متن)، `places[]` (همان شکل `PlaceOut` برای کارت؛ فقط مکان‌هایی که متن نام می‌برد و واقعاً در دیتابیس هستند)، `routes[]` (فاصله، زمان، `geometry` پولی‌لاین نشان)، `itinerary`، `conversation_id` (برای پیام‌های بعدی)، `degraded` (اگر true: هوش مصنوعی در دسترس نبود و `reply` نتیجه‌ی جست‌وجوی ساده است)، `error_code`، `request_id`.

### ابزارها
`search_places` · `nearby_places` · `get_place` · `get_categories` · `search_opportunities` · `get_route` · `plan_itinerary`.
همه: ورودی سخت‌گیرانه (فیلد ناشناخته رد می‌شود)، timeout، لاگ زمان اجرا، سقف تعداد نتیجه. فاصله‌ی «نزدیک» همیشه خط مستقیم برچسب می‌خورد؛ زمان و مسیر فقط از نشان. مدت بازدید و ساعت کاری در دیتا نیست و مدل اجازه‌ی ساختنش را ندارد.

### چه چیزهایی هنوز نیست (عمداً)
`get_user_preferences`, `save_place`, `get_saved_places`, `create_itinerary`, `get_itinerary`: به حساب کاربری نیاز دارند که بک‌اند هنوز ندارد. مکانیزم `requires_auth` و جدا بودن مالک گفتگو آماده است؛ با آمدن احراز هویت `user_id` را در `router.py` پاس بده.
همچنین: streaming، حافظه‌ی گفتگو در دیتابیس (فعلاً در حافظه‌ی پروسه با انقضای ۳۰ دقیقه)، مسیر پیاده/دوچرخه (آداپتر نشان فعلی فقط ماشین)، قاعده‌ی صریح «پوشش عملیاتی منطقه‌ی آزاد» (داده‌اش را نداریم)، هزینه‌ی ریالی/دلاری (فقط توکن شمرده می‌شود).
