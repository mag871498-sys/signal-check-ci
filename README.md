# Signal Check

Python-сервіс повертає стан через `/health` і SHA випуску через `/version`. Для роботи контейнера достатньо стандартної бібліотеки Python.

## Запуск і перевірка

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
cp .env.example .env
docker build --build-arg APP_VERSION=local -t signal-check:local .
docker compose up -d --wait --wait-timeout 20
python -m pytest -q tests
python -m pytest -q infra --hosts="docker://$(docker compose ps -q api)"
python ops/probe.py 8216 local
docker compose down
```

У PR до `main` запускаються pytest і складання Docker-образу. Після push у `main` зібраний образ перевіряється на окремому Linux runner із Compose, Testinfra і контрольними HTTP-запитами. GitHub Actions зберігає результати й журнали в артефактах. Після успішного розгортання образ із тегом SHA зберігається як `approved-image` на 30 днів.

## Експерименти

- Push гілки `codex/qa-negative` із завідомо неправильним очікуванням у тесті дає помилку на етапі збірки й блокує розгортання.
- Push гілки `codex/health-negative` зі значенням `IMAGE_HEALTH_CODE=503` у Dockerfile створює несправний образ. Розгортання завантажує останній чинний `approved-image` з успішного запуску `main`. Після HTTP 503 скрипт відновлює цей образ і повторює перевірки, а сам запуск зберігає статус Failure.

Для другого експерименту потрібен успішний запуск `main` із доступним артефактом. Обидві гілки використовуються окремо від `main`.

## Ручне повернення образу

Знайдіть останній успішний запуск гілки `main` у вкладці Actions. Підставте його ідентифікатор замість `RUN_ID`, а повний SHA — замість `PREVIOUS_SHA`. Виконайте команди в корені локальної копії після активації `.venv`.

```bash
gh run download RUN_ID -n approved-image -D baseline
docker load -i baseline/image.tar.gz
IMAGE_REF=signal-check:PREVIOUS_SHA docker compose up -d --force-recreate --wait --wait-timeout 20
python -m pytest -q infra --hosts="docker://$(docker compose ps -q api)"
python ops/probe.py 8216 PREVIOUS_SHA
docker compose down
```

## Навчальне середовище

На час перевірки сервіс працює на Linux VM GitHub Actions. Для IaaS можна перенести Compose на постійну VM і зберігати образи за SHA в реєстрі. У цьому випадку команда відповідає за оновлення ОС, Docker та застосунку. У PaaS провайдер підтримує платформу, а команда оновлює образ і параметри сервісу. Витрати залежать від часу роботи VM або сервісу, обсягу реєстру та вихідного трафіку.