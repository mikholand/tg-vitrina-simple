# CLAUDE.md

Этот файл — рабочая карта проекта для Claude Code. Он описывает реальное
устройство кодовой базы по состоянию на момент написания (проверено чтением
исходников, а не по аналогии с типовыми проектами). Для глубокого обзора
общей архитектуры и бизнес-обоснований см. также [README.md](README.md) и
[docs/architecture.md](docs/architecture.md) — здесь они не пересказываются
полностью, только самое важное + ссылка.

## 1. Назначение проекта

`tg-vitrina-simple` — self-hosted витрина для **одного** Telegram-канала:
превращает обычные посты канала в каталог товаров внутри Telegram Mini App,
с оформлением заказа и уведомлением продавца. Один деплой = один магазин =
один канал (намеренное ограничение, см. «Single-shop design» в
docs/architecture.md — это не недоделанная мультитенантность, а осознанный
выбор).

Пользователи:
- **Покупатель** — открывает Mini App из Telegram (или просто сайт в
  браузере) и оформляет заказ.
- **Продавец/админ/модератор** (`UserRole`) — управляет каталогом,
  категориями, баннерами, контактами, командой через тот же Mini App
  («кабинет продавца», `/seller/*` маршруты).

## 2. Ключевые возможности

- Импорт товаров из постов канала: `bot` (aiogram) — в реальном времени,
  `userbot` (Pyrogram) — историческая синхронизация (resumable backfill).
- Автоматическое извлечение структуры товара из текста поста через LLM
  (OpenRouter) — черновик (`status=draft`), который продавец проверяет
  вручную.
- Каталог с категориями (дерево), поиском и пагинацией; избранное (в т.ч.
  анонимное, с переносом при входе); корзина и чекаут, включая **гостевой
  чекаут с обычного сайта** вне Telegram (нужны имя+телефон).
- Уведомления о заказах в Telegram-чат продавца (команда бота
  `/setorderchat`).
- Кабинет продавца: товары (CRUD, фото/видео, publish/hide/delete),
  категории, баннеры, контакты, команда (инвайт-ссылки), настройки
  магазина, статистика просмотров, ручной запуск/остановка синхронизации.
- Роли выдаются по Telegram id (`SUPER_ADMIN_IDS` → авто-повышение до admin при логине)
  или через инвайт-ссылки (промо до moderator).
- SEO: динамические `robots.txt`/`sitemap.xml`, meta-теги на страницах.
- Публикация товара обратно в канал (кнопка-ссылка «Открыть в витрине»).

## 3. Технологический стек

**Backend** (`backend/`, Python ≥3.12, менеджер зависимостей — `uv`):
- FastAPI + `granian` (ASGI-сервер, не uvicorn) — см. `app/__main__.py`.
- DI: **Dishka** (`Provider`/`Scope`, не FastAPI `Depends` напрямую для
  бизнес-объектов) — `app/di/providers.py`, `app/di/container.py`.
- SQLAlchemy 2.0 (async, `asyncpg` в рантайме, `psycopg2` для Alembic),
  Alembic — линейная цепочка миграций.
- `aiogram` 3.x — Telegram-бот; `pyjwt` — сессионные JWT; `structlog` — JSON-
  логирование; `Pillow` — перекодирование изображений в WebP; `openai`
  Python SDK — клиент для OpenRouter (не OpenAI!); `pydantic`/
  `pydantic-settings` — DTO и конфиг.
- Тесты: `pytest` + `pytest-asyncio` + `aiosqlite` (in-memory SQLite, без
  Postgres). Линт: `ruff`. Типы: `mypy` (настроен, но **не** в CI).

**Frontend** (`frontend/`, Vue 3 + TypeScript, Vite 6):
- Vue 3 Composition API, только `<script setup lang="ts">`.
- `vue-router` 4, `pinia` 2 (setup-стиль сторов), `axios`.
- `primevue` 4 (тема Aura, кастомный `definePreset`) + `tailwindcss` 3
  (`tailwindcss-primeui`) + собственные CSS-переменные-токены `--sf-*`.
- `zod` — валидация ответов backend на границе `entities/*/api.ts`.
- `unplugin-auto-import` + `unplugin-vue-components` — `ref`/`computed`/
  router-композаблы и все PrimeVue-компоненты доступны в `.vue` без импорта.
- ESLint 9 (flat config) + Prettier; `vue-tsc` — часть `npm run build`.
- Нет vitest/jest — модульных тестов фронтенда не настроено.

**Userbot** (`userbot/`) — отдельный процесс/образ на Pyrogram (своя
`pyproject.toml`/`uv.lock`, нужен C-тулчейн для `tgcrypto`).

**Инфраструктура**: Docker Compose (многосервисный стек), Traefik (dev/prod
реверс-прокси перед всем стеком), nginx (внутри образа `frontend`, same-
origin проксирование `/api`, `/media`, `/robots.txt`, `/sitemap.xml` на
backend), GitHub Actions CI (`.github/workflows/ci.yml`).

## 4. Архитектура и основные компоненты

Пять процессов на одной базе Postgres (подробная диаграмма — в
docs/architecture.md):

| Процесс     | Образ/команда                          | Роль |
|-------------|------------------------------------------|------|
| `backend`   | `backend/Dockerfile`, `python -m app`    | FastAPI API, отдаёт весь HTTP |
| `bot`       | тот же образ, `python -m app.telegram`   | aiogram: приём постов канала в реальном времени, `/start`, `/setorderchat` |
| `extractor` | тот же образ, `python -m app.extractor`  | опрашивает `raw_posts`, вызывает LLM, создаёт черновики `Product` |
| `userbot`   | `userbot/Dockerfile`, Pyrogram           | историческая синхронизация через внутренний HTTP API backend'а |
| `frontend`  | `frontend/Dockerfile`, nginx             | статическая Vue3-сборка + same-origin проксирование |

`backend`, `bot` и `extractor` — **один и тот же образ**, различается только
`command:` в `docker-compose.yml`.

### Backend: слоёная архитектура (строго соблюдается)

```
API-роутер (app/api/**, FastAPI + DishkaRoute)
      ↓ вызывает один метод сервиса
Сервис (app/services/*.py) — вся бизнес-логика, оркестрация
      ↓ использует 1+ репозиториев/клиентов через конструктор
Репозиторий (app/repositories/*.py) — один на сущность, чистый SQL (select/update/delete)
      ↓ читает/пишет
Сущность (app/entities/*.py) — SQLAlchemy declarative модели, Base+TimestampMixin
```

DTO (`app/dto/*.py`) — pydantic-схемы запросов/ответов, **отдельно** от
entity (`ProductSchema.model_validate(product)`, `from_attributes=True`).

**Важно: в ORM нигде нет `relationship()`.** Связанные данные (например,
`category_ids` товара) получаются отдельным запросом в репозитории
(`ProductRepository.get_category_ids`), а не ленивой загрузкой. Это
осознанная конвенция проекта — не предлагать `relationship()` при доработке.

DI (Dishka): провайдеры в `app/di/providers.py`, группы — `CoreProvider`
(Scope.APP: settings, engine, session_factory, `Bot`, `BotClient` — живут
весь процесс), `SessionProvider`/`RepositoryProvider`/`ClientProvider`/
`ServiceProvider` (Scope.REQUEST). В роутере — `FromDishka[X]` + `route_class=
DishkaRoute`. Вне HTTP-запроса (хендлеры бота, цикл экстрактора) DI-скоуп
открывается руками: `async with container() as request_container: await
request_container.get(X)`.

### Аутентификация

Нет отдельного логина вне Telegram: `POST /auth/telegram/login` принимает
`init_data`, проверяет подпись через aiogram
(`safe_parse_webapp_init_data`, см. `app/services/telegram_auth.py`), делает
upsert `User` по Telegram id, выпускает HS256 JWT
(`app/shared/security.py`, `user_id`+`role`, срок — `JWT_EXPIRE_MINUTES`,
по умолчанию 43200 мин = 30 дней). Токен живёт в `sessionStorage`
фронтенда, шлётся как `Authorization: Bearer`. Авто-повышение до admin по
`SUPER_ADMIN_IDS` происходит на каждом логине, пока не закрепится.

Зависимости в `app/api/deps.py`: `CurrentUser` (обязательна валидная
сессия) / `OptionalUser` (сессии может не быть — гостевые сценарии) /
`CurrentSeller` (seller или admin) / `CurrentStaff` (+ moderator) /
`RequireInternalToken` (заголовок `X-Internal-Token`, только для
userbot↔backend). Выбирать нужную по аналогии с соседними эндпоинтами того
же роутера.

### Frontend: слои (Feature-Sliced-Design-подобно)

`app/` (бутстрап, роутер) → `widgets/` (композиция на несколько страниц,
напр. `BottomNav`) → `features/` (разовые интерактивные виджеты, напр.
`ProductEditor`) → `entities/` (одна папка на предметную область: `api.ts` +
`schema.ts` [zod] + `types.ts`, опционально `store.ts` [Pinia] и `ui/*.vue`)
→ `pages/` (компоненты маршрутов) → `shared/` (http-клиент, обёртка
Telegram SDK, общие UI-атомы). Алиасы путей `@`, `@app`, `@entities`,
`@features`, `@pages`, `@widgets`, `@shared` — см. `vite.config.ts`.

Каждый ответ API разбирается через zod-схему в `entities/*/api.ts` —
сырой `response.data` наружу не отдаётся.

## 5. Структура репозитория

```
backend/app/
  api/            FastAPI-роутеры (+ api/seller/*, api/internal_sync.py)
  asgi/app.py     создание FastAPI-приложения, middleware, роутинг
  clients/        внешние API: bot.py (aiogram-обёртка), openrouter.py
  core/           config.py (pydantic-settings), db.py, logging.py (structlog),
                  start_param.py (кодирование deep-link'ов)
  di/             container.py, providers.py (Dishka)
  dto/            pydantic-схемы запрос/ответ
  entities/       SQLAlchemy-модели
  extractor/__main__.py   цикл опроса raw_posts → LLM → Product(draft)
  repositories/   один файл на сущность, чистый SQL
  services/       бизнес-логика
  shared/         stock.py, media.py, pagination.py, security.py, slug.py,
                  uploads.py, categories_seed.py
  telegram/       __main__.py (bot-процесс), handlers.py (приём постов),
                  commands.py (/start, /setorderchat), media_group.py
backend/migrations/versions/   линейная цепочка Alembic (0001…0012)
backend/tests/    test_<область>.py + conftest.py (полный DI+SQLite харнесс)

frontend/src/
  app/            main.ts, App.vue, router/index.ts, styles/main.css
  entities/       product, cart, category, user, favorite, banner, contact,
                  invite, moderator, raw-post, seller-settings, store-info, sync
  features/       product-editor, product-delete, contact-picker
  pages/          home, catalog, product, cart, favorites, seller/*
  widgets/nav/    BottomNav.vue
  shared/         api/http.ts, telegram/sdk.ts, seo/useSeoMeta.ts, ui/*

userbot/app/      config.py, backend_client.py, history.py, media.py,
                  sync_runner.py, logging.py  (отдельная кодовая база/venv)

docs/architecture.md   поток данных, resumable sync, single-shop rationale
traefik/               traefik.dev.yml / traefik.prod.yml
scripts/               ACME-обслуживание (вне основного приложения)
media/                 примонтированное хранилище загрузок (gitignored)
```

## 6. Основные бизнес-сценарии

**а) Пост канала → черновик товара.**
`telegram/handlers.py: build_channel_router` принимает `channel_post`,
агрегирует альбомы через `MediaGroupAggregator`, скачивает фото в
`MEDIA_ROOT/raw_posts/{channel}/{message}/`, создаёт `RawPost` (дедуп по
`channel_id+message_id` или `media_group_id`). Для истории — тот же путь,
но через `userbot/app/sync_runner.py: SyncRunner.run_pass`, который шлёт
батчи в `POST /api/v1/internal/sync/ingest`
(`app/api/internal_sync.py` → `SyncOrchestrationService.ingest_batch`).
Затем `extractor/__main__.py` опрашивает и вызывает
`ExtractionService.process_pending`: берёт пачку `NEW` (`claim_new_batch`),
**пропускает**, если найденный по `source_post_id` товар уже
`edited_by_seller=True` (железное правило — экстрактор никогда повторно не
трогает товар, отредактированный продавцом, проверяется дважды: до вызова
LLM и внутри `ProductService.create_or_update_from_extraction`), иначе шлёт
текст в OpenRouter (`services/prompts.py` шаблоны), парсит строгий JSON в
`ProductExtractionSchema`, резолвит категорию
(`CategoryService.resolve_label` — LLM не может придумать несуществующую
категорию, при промахе — fallback «Другие»), создаёт/обновляет `Product`
со `status=draft`.

**б) CRUD товара продавцом + правила остатков.**
`api/seller/products.py` (доступ `CurrentStaff`) →
`ProductService.create_by_seller`/`update_by_seller`, оба проходят через
`ProductService._normalize_stock` — единственный источник правды по
количеству/наличию (см. §16). Медиа — отдельными эндпоинтами
(`shared/uploads.py`: фото всегда перекодируется в WebP через Pillow,
проверяются лимиты размера).

**в) Чекаут.**
`POST /catalog/orders` (`OptionalUser` — работает с сессией Telegram и без
неё) → `OrderService.checkout`: схлопывает дублирующиеся строки корзины,
одним запросом подтягивает опубликованные товары
(`get_published_many`), валидирует/пересчитывает цену по серверным данным
(клиентской цене не доверяет), резервирует остаток условным `UPDATE`
(`OrderRepository.try_decrement_stock` — безопасно при гонке), требует
`contact_name`+`contact_phone`, если нет Telegram-сессии (гостевой чекаут
с сайта), сохраняет `Order`+`OrderItem` (snapshot, не ссылка), затем
best-effort уведомляет Telegram-чат
(`StoreProfile.order_notification_chat_id`, настраивается командой бота
`/setorderchat` — `telegram/commands.py: try_configure_order_chat`, только
для admin). Сбой уведомления никогда не откатывает уже созданный заказ.

**г) Авторизация в Mini App.**
Фронтенд при старте (`router/index.ts: ensureAuthInitialized`) →
`POST /auth/telegram/login` с `init_data` →
`TelegramAuthService.login`. Токен — в `sessionStorage`; axios-интерцептор
(`shared/api/http.ts`) на любой 401 один раз молча пере-логинивается через
Telegram и повторяет запрос.

**д) Историческая синхронизация (resumable backfill)** — курсор/stop_id
механика полностью описана в docs/architecture.md, не дублируется здесь.

## 7. Работа с данными и БД

- Postgres 16, SQLAlchemy 2.0 async. Одна `AsyncSession` на запрос
  (`SessionProvider`, Scope.REQUEST, `session.begin()` оборачивает весь
  запрос в одну транзакцию — явных `session.commit()` в сервисах нет).
- **Никаких `relationship()`** — см. §4. Новой связи — новый метод
  репозитория, а не `relationship`/`joinedload`.
- Миграции — Alembic, строго линейная цепочка
  `backend/migrations/versions/00NN_описание.py`. Выполняются
  автоматически при старте контейнера `backend` (`alembic upgrade head &&
  python -m app`) и вручную через `make migrate`.
- Singleton-строки: `store_profile` и `sync_state` (фиксированный id) —
  следствие single-shop дизайна, не ошибка.
- Конкурентность: декремент остатка — условный `UPDATE ... WHERE quantity
  >= :n` (`OrderRepository.try_decrement_stock`), не read-then-write —
  этот паттерн нужно повторять для любой похожей логики «списать
  ограниченный ресурс».
- Нет `shop_id`/tenant-колонки ни на одной таблице — намеренно, см. §16.
- Тесты — только in-memory SQLite (`aiosqlite`), никогда реальный Postgres
  (нужен compile-override `BigInteger→INTEGER` для автоинкремента, см.
  `tests/conftest.py`).

## 8. API и взаимодействие компонентов

Всё под `/api/v1` (`API_PREFIX`, `app/asgi/app.py`). Группы роутеров:
`/auth`, `/catalog/*` (публичная витрина + `robots.txt`/`sitemap.xml`),
`/favorites`, `/invites/redeem` (публичный), `/internal/sync/*`
(только userbot, заголовок `X-Internal-Token`), `/seller/*` — products,
raw-posts, categories, sync, stats, banners, orders (доступ `CurrentStaff`
— seller/admin/moderator); настройки магазина (`settings.py`), управление
командой (`moderators.py`), выдача инвайтов (`invites.py`) и контакты
(`contacts.py`) — строже, напрямую `CurrentSeller` (только seller/admin,
без moderator; нет отдельного алиаса `CurrentOwner` — это тот же
`CurrentSeller`, что и везде). Соответствует фронтенду, который помечает
`/seller/contacts` как `requiresOwner: true` (`router/index.ts`) — до
правки backend здесь использовал `CurrentStaff`, так что модератор не
видел пункт меню, но мог вызвать API контактов напрямую; исправлено,
заодно переписан тест `test_moderator_can_manage_contacts_but_not_settings`
→ `test_moderator_cannot_manage_contacts_or_settings` (`tests/
test_contacts.py`), который раньше намеренно проверял старое поведение.

- Пагинация — обобщённый `Paginated[T]` (`shared/pagination.py`):
  `{items, total, limit, offset}`, `limit` капается `le=100`.
- Валидация — pydantic DTO на каждый эндпоинт, отдельные Create/Update/
  Schema классы; в Update-схемах различают «поле не передано» и «поле
  явно сброшено в null» через `model_fields_set` (см.
  `ProductService.update_by_seller`).
- Ошибки — `HTTPException` с короткими машиночитаемыми `detail`
  (`product_not_found`, `insufficient_stock:{id}`, `contact_required`...).
  Сервисы кидают `ValueError(code)`, роутер превращает в 400 (см.
  `OrderService.checkout` + `except ValueError` в `catalog.py`).
- **Все `/api/*` ответы получают `Cache-Control: no-store`** (middleware
  в `asgi/app.py`) — защита от кеширования устаревшего JSON встроенным
  Telegram-webview. Не убирать без понимания причины (см. комментарий там
  же и `test_catalog_product_detail_includes_share_url`).
- Same-origin: фронтенд ходит на backend через nginx-проксирование
  (`baseURL: '/api/v1'`), `CORSMiddleware` на backend — только для
  локальной разработки (Vite на другом порту).

## 9. Frontend

- Сущность-слайс: `entities/<имя>/{api.ts, schema.ts, types.ts}` (+
  `store.ts` для Pinia, `ui/*.vue` для переиспользуемого компонента).
  `schema.ts` — zod; `api.ts` всегда парсит ответ через схему перед
  возвратом.
- State — Pinia setup-сторы (`defineStore('x', () => {...})`), не
  options-стиль.
- Сессия — только `sessionStorage` (переживает reload, не новую вкладку).
- Стили — Tailwind + токены `--sf-*` (`sf-bg/card/accent/ink/muted/line/
  danger/success/warning` + `-soft`-варианты), заданы в
  `app/styles/main.css`, подключены в `tailwind.config.js`. PrimeVue
  перекрашен один раз централизованно в `main.ts` (`definePreset(Aura,
  ...)`), а не поточечно на каждом компоненте. Тёмной темы нет
  (`darkModeSelector: false`).
- Telegram-интеграция — собственная обёртка
  (`shared/telegram/sdk.ts`) вокруг самостоятельно хостимого
  `public/js/telegram-web-app.js`, **не** npm-пакет `@telegram-apps/sdk`
  (сознательный отказ — см. заголовок файла про баг reload-loop в
  Telegram Web). Каждая функция безопасно no-op вне Telegram.
- Deep links (`startapp=...`): backend кодирует путь в base64url
  (`core/start_param.py`), фронтенд декодирует тем же алгоритмом в
  `router/index.ts` — менять синхронно на обеих сторонах.
- Автоимпорт: `ref`/`computed`/`watch`/роутер-композаблы и все
  PrimeVue-компоненты доступны в `.vue` без импорта
  (`unplugin-auto-import` + `unplugin-vue-components`). Файлы
  `src/auto-imports.d.ts`/`src/components.d.ts` сгенерированы и
  гитигнорены (`frontend/.gitignore`) — не редактировать руками.
  Новый composable из `@shared` — импортируется явно, автоимпорт на него
  не распространяется.
- `npm run build` = `vue-tsc --noEmit && vite build` — ошибка типов
  валит сборку, не только `lint`.

## 10. Backend: где писать новую логику

- Новая бизнес-логика — в сервис (`app/services/`), никогда в роутер или
  репозиторий. Роутер: проверка доступа → один вызов сервиса → маппинг
  результата/исключения в HTTP-ответ. Репозиторий: только SQL, без
  правил (объединение дублирующихся строк корзины и нормализация
  остатков живут в сервисах, даже если касаются персистентности).
- Сервисы получают зависимости через конструктор; Dishka резолвит их
  автоматически по типам — новый сервис/репозиторий достаточно
  зарегистрировать в `app/di/providers.py` в правильном Scope (APP —
  долгоживущее, REQUEST — на запрос).
- Сущности (`entities/`) не содержат поведения сверх простых производных
  полей — логика в сервисах, оформленная как именованный метод
  (`ProductService._normalize_stock`, `CategoryService.resolve_label`), а
  не разбросанные проверки по месту.

## 11. Внешние интеграции

- **Telegram Bot API** (aiogram, `clients/bot.py: BotClient`) — отправка
  сообщений/фото, сборка deep-link'ов Mini App. Специальной
  retry/backoff-обёртки нет: где сбой не должен ронять вызывающий код
  (уведомление о заказе) — он просто логируется и проглатывается; в
  остальных местах исключение всплывает как есть.
- **Telegram Mini App auth** — подпись `init_data` проверяется
  `aiogram.utils.web_app.safe_parse_webapp_init_data` относительно
  `BOT_TOKEN`, допустимый возраст — 24 часа (`INIT_DATA_MAX_AGE`).
- **OpenRouter** (OpenAI-совместимый Chat Completions через SDK `openai`
  с кастомным `base_url`) — экстракция данных товара, `temperature=0`,
  принудительный `response_format: json_object`, до
  `EXTRACTOR_MAX_RETRIES` повторов при ошибке вызова/невалидном JSON,
  до `EXTRACTOR_CONCURRENCY` параллельных вызовов (семафор). Если
  `OPENROUTER_API_KEY` не задан — экстрактор тихо ничего не делает
  (`is_configured()` возвращает False), это не жёсткая зависимость для
  работы остального приложения.
- **userbot ↔ backend** — внутренний HTTP API, авторизация общим
  секретом в заголовке `X-Internal-Token` (не JWT).

## 12. Локальный запуск и конфигурация

Проверено по README.md/Makefile:

```bash
cp .env.example .env
# заполнить STORE_*, TELEGRAM_CHANNEL_ID, BOT_TOKEN, USERBOT_*,
# OPENROUTER_API_KEY, POSTGRES_*, JWT_SECRET, INTERNAL_API_TOKEN

make up        # docker compose --profile dev up -d --build (+ dev Traefik)
make migrate   # опционально — миграции и так гоняются при старте backend
make logs
make shell-backend   # shell внутри контейнера backend
make test      # pytest backend'а локально через uv, без контейнеров
```

Mini App доступен на `http://localhost/` через dev-Traefik (не напрямую на
порт frontend-контейнера). Конфигурация — слоёные pydantic-settings группы
(`StoreSettings`, `TelegramSettings`, `UserbotSettings`,
`ExtractorSettings`, `DatabaseSettings`, `SecuritySettings`,
`AppSettings`), собранные в один фасад `Settings` (`core/config.py`),
кешируется на процесс через `@lru_cache get_settings()`. Dev vs prod
Traefik-конфиги — см. README.md «Dev vs prod».

Отдельный dev-сервер фронтенда: `cd frontend && npm install && npm run
dev` (Vite, порт 3000) — для same-origin `/api`-проксирования обычно всё
равно нужен backend, поднятый через compose/Traefik; не считать, что
голый `npm run dev` сам по себе видит backend.

## 13. Тестирование и контроль качества

- **Backend**: `cd backend && uv sync` один раз, затем `make test` (из
  корня) или `cd backend && uv run pytest` — на хосте, in-memory SQLite,
  без контейнеров. Линт — `uv run ruff check .`. `mypy` настроен
  (`pyproject.toml`), но в CI **не** запускается — не заявлять, что типы
  проверены, если явно не прогнали `uv run mypy` сами.
- **Frontend**: `npm run lint` (`eslint --fix`), `npm run build`
  (vue-tsc + vite build — это и есть типчек), `npm run format`
  (prettier). Модульных тестов фронтенда нет — проверка через браузер.
- **Userbot**: только линт в CI (`uvx ruff check .`, изолированное
  tool-окружение, зависимости проекта не ставятся — `tgcrypto` без
  прибилженного wheel требует C-тулчейн даже для линта).
- **CI** (`.github/workflows/ci.yml`): три независимых джоба на push/PR в
  main/master — `backend-tests` (ruff+pytest), `userbot-lint`,
  `frontend-checks` (eslint+build). Сквозного/интеграционного джоба между
  сервисами нет.
- Конвенция тестов backend: один `test_<область>.py` на домен в
  `backend/tests/`. `conftest.py` строит полный Dishka-контейнер на
  in-memory SQLite + реальное FastAPI-приложение, запросы идут через
  `httpx.AsyncClient`/`ASGITransport` (настоящий HTTP, не прямой вызов
  методов сервиса, кроме точечных низкоуровневых тестов через
  `db_session`/`container`). Фабрики `make_user`/`make_product`/
  `make_category`/`make_raw_post`; готовые `(User, auth_header)` —
  фикстуры `customer`/`seller`/`admin`/`moderator`. `Bot.get_me`
  замокан глобально (autouse), `Bot.send_message`/`send_photo` — только
  там, где тест явно запрашивает `mock_bot_send_message`.

## 14. Сборка, CI/CD и развёртывание

`docker-compose.yml` (база) + `docker-compose.prod.yml` + отдельный
`docker-compose.shared-traefik.yml` (оверлей для хоста, где уже крутится
общий Traefik для нескольких проектов) — перед правкой деплой-конфига
проверять, какие файлы реально накладываются друг на друга в конкретном
окружении, не предполагать единственный `docker-compose.yml`.

`backend`/`bot`/`extractor` — один образ (`backend/Dockerfile`,
многостадийный, на `uv`, non-root пользователь `app`), различаются только
`command:`. `frontend/Dockerfile` — сборка Vite-бандла + nginx
(`frontend/nginx.conf`, same-origin проксирование `/api`, `/media`,
`/robots.txt`, `/sitemap.xml`). `userbot/Dockerfile` — отдельный образ.

**В `.github/workflows/ci.yml` нет шага деплоя** — CI только
линт/тесты. В репозитории нет скрипта/описания процесса продакшен-
деплоя. Если задача требует деплоя — уточнить у пользователя способ и
хост, а не придумывать команду по аналогии; без прямой просьбы
пользователя в текущем диалоге деплой не выполнять.

## 15. Правила разработки и кодстайл

**Backend:**
- ruff: `select = ["E","F","I","UP","B","SIM"]`, `line-length=100`,
  `ignore=["E501","B008"]` (B008 отключён осознанно — `FromDishka[X]`/
  `Depends(...)` как значение по умолчанию — это и есть механизм DI, не
  баг). Таргет py312.
- Типы — везде (`check_untyped_defs=true` в mypy, хоть mypy и не в CI).
- Все enum'ы сущностей — `enum.StrEnum`, хранятся как `Enum(...,
  native_enum=False, length=N)`, т.е. обычная строковая колонка, не
  нативный Postgres enum.
- Комментарии в коде — содержательные, объясняют **почему**, а не что
  (вплоть до описания конкретного живого бага, который фикс устраняет, и
  ссылки на конкретный другой файл/символ, от которого зависит инвариант).
  Этот стиль пронизывает весь backend и frontend — придерживаться его в
  новых комментариях, а не писать содержательно-нейтральные «what»-
  комментарии.
- Бизнес-правило — один именованный метод, не разбросанные проверки (см.
  §10). Перед добавлением проверить, нет ли уже подходящего.

**Frontend:**
- Только `<script setup lang="ts">` + Composition API; Pinia — только
  setup-стиль.
- Не импортировать руками то, что покрыто автоимпортом (vue/vue-router/
  PrimeVue) — но новый `@shared`-composable импортировать явно.
- zod-схема в `schema.ts` — точка принудительной проверки формы ответа;
  новое поле backend'а, которое нужно фронтенду, добавляется и туда,
  иначе будет молча отфильтровано при парсинге.
- Tailwind + `--sf-*` токены — для всего, что видит покупатель; для
  форм кабинета продавца — штатные PrimeVue-контролы (перекрашены раз в
  `main.ts`), не изобретать свои поля ввода.
- Перед тем как считать фронтенд-правку готовой — прогнать `npm run
  lint` и `npm run build`.

**Везде:**
- UI/пользовательский текст — только на русском (ярлыки, тосты,
  сообщения бота). Не вносить английские пользовательские строки.
- Коммиты в истории проекта преимущественно в формате Conventional
  Commits — `feat: ...` / `fix: ...`, в повелительном наклонении,
  коротко (см. `git log`). Атрибуция авторства коммитов управляется
  текущими инструкциями сессии, а не фиксируется здесь.

## 16. Критически важные соглашения и ограничения

- **Single-shop, не multi-tenant.** Не добавлять `shop_id`/tenant без
  явной прямой просьбы — см. docs/architecture.md.
- **`edited_by_seller` — однонаправленный флаг.** Once true — экстрактор
  никогда больше не трогает этот товар (проверяется дважды: вызывающим
  кодом до LLM-запроса и внутри
  `ProductService.create_or_update_from_extraction`). Любой новый код
  рядом с экстрактором должен сохранять это свойство.
- **Инварианты остатка/наличия централизованы в
  `ProductService._normalize_stock`** (quantity==0 ⇒ `out_of_stock`;
  `on_order`/`out_of_stock` никогда не хранят отслеживаемое количество) и
  зеркалированы в `OrderRepository.try_decrement_stock` (списание при
  чекауте) и на фронтенде в `entities/product/stock.ts`. Все три места
  должны оставаться согласованными — правило несколько раз уточнялось по
  реальным багрепортам в истории проекта; перед правкой логики остатков
  перечитать докстринг `_normalize_stock`, а не восстанавливать правило
  по памяти.
- **Декремент остатка — условный `UPDATE ... WHERE quantity >= :n`**, не
  read-then-write — сохранять этот паттерн для похожей логики «списать
  ограниченный ресурс»; наивная read-check-write-версия возвращает гонку.
- **В ORM нигде нет `relationship()`.** Новой связи — отдельный метод
  репозитория (второй запрос/явный join), не ленивая загрузка.
- **`Cache-Control: no-store` на всех `/api/*` ответах не случаен** —
  фикс реального бага с кешированием устаревшего JSON встроенным
  Telegram-webview. Не сужать область действия без повторного чтения
  комментария в `asgi/app.py` и
  `test_catalog_product_detail_includes_share_url`.
- **Строки заказа снимаются снэпшотом при чекауте** (имя/sku/цена/
  валюта копируются, а не читаются вживую) — редактирование или удаление
  товара не должно переписывать историю заказов.
- **Deep link Mini App требует короткое имя Direct Link бота**
  (`MINI_APP_SHORT_NAME`) в пути — голый `t.me/<bot>?startapp=...`
  открывает просто чат, а не запускает Mini App. Любой новый код,
  формирующий такую ссылку, должен идти через `BotClient.mini_app_url`,
  не собирать URL вручную.
- **Пути к медиа хранятся относительно `MEDIA_ROOT`** везде (в колонках
  БД, у обоих писателей — bot и userbot) и превращаются в `/media/...`
  URL только на границе API (`shared/media.py: media_url`) — не хранить
  и не сравнивать уже-с-префиксом путь.
- **Кодирование/декодирование deep-link'ов должно остаться синхронным**
  между `core/start_param.py` (backend) и `router/index.ts:
  decodeStartPath` (frontend) — оба делают base64url от буквального
  app-relative пути.
- `bundle_check.js` в корне репозитория — незакоммиченный посторонний
  файл (не часть приложения) — не стейджить/коммитить его.

## 17. Перед внесением изменений

**До правки:**
1. Определить затронутый слой (сервис/репозиторий backend, слайс/
   фича/страница frontend) и прочитать его целиком, не только сигнатуру.
2. Если добавляется новый сервис/репозиторий — зарегистрировать в
   `app/di/providers.py` в правильном Scope.
3. Для правок, касающихся остатков/наличия, чекаута или auth — перечитать
   соответствующие инварианты в §16, не восстанавливать правило по
   памяти.
4. Для нового backend-эндпоинта — выбрать auth-зависимость
   (`CurrentUser`/`OptionalUser`/`CurrentSeller`/`CurrentStaff`/
   `RequireInternalToken`) по аналогии с соседними эндпоинтами того же
   роутера.
5. Для новых таблиц/колонок — новая линейная Alembic-миграция, не правка
   существующей.
6. Для нового фронтенд-функционала — проверить, нет ли уже подходящей
   сущности/компонента в `entities/`/`shared/`, прежде чем писать новый.
7. Не вводить новые зависимости, если задача решается существующими
   средствами стека; не переписывать архитектуру/не массово
   переименовывать файлы в рамках точечной задачи.

**После правки:**
1. Backend: `cd backend && uv run ruff check .` и `uv run pytest` (или
   `make test` из корня).
2. Frontend: `npm run lint` и `npm run build` (он же типчек).
3. Если меняется контракт API — обновить обе стороны синхронно: DTO/
   entity (backend) и `types.ts`/`schema.ts` (frontend).
4. В отчёте пользователю явно указывать, какие проверки реально
   выполнены — и какие не выполнены (например, не было ручной проверки в
   браузере, если её не делали). Не заявлять об успешном прохождении
   тестов/линта, которые фактически не запускались.
5. Не трогать `.env`/прод-конфигурацию/секреты и не выполнять деплой или
   прод-миграции без явной просьбы пользователя в текущем диалоге.
