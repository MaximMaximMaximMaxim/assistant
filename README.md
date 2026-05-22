# Analytics TAO Agent

FastAPI-ассистент для анализа запросов через OpenRouter и внешний Analytics API.

## Требования

- Docker
- Docker Compose

## Быстрый старт

1. Скопируйте пример переменных окружения:

```bash
cp .env.example .env
```

В PowerShell также можно выполнить:

```powershell
Copy-Item .env.example .env
```

2. Откройте `.env` и укажите реальные значения, как минимум:

```env
OPENROUTER_API_KEY=sk-...
```

3. Соберите и запустите контейнер:

```bash
docker compose up --build -d
```

После запуска API будет доступен на `http://localhost:8003`.

## Проверка

Откройте Swagger UI:

```text
http://localhost:8003/docs
```

Основной эндпоинт ассистента:

```text
POST /analyze
```

Пример запроса:

```bash
curl -X POST http://localhost:8003/analyze \
  -H "Content-Type: application/json" \
  -d '[{"role":"user","content":"Покажи аналитику по последним данным"}]'
```

## Полезные команды

Посмотреть логи:

```bash
docker compose logs -f agent
```

Проверить статус контейнера:

```bash
docker compose ps
```

Остановить ассистента:

```bash
docker compose down
```

