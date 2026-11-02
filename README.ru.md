# Interview Intel

**Исследование компаний, анализ вакансий и интерактивная подготовка к интервью для ИИ-агентов с опорой на источники.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![Тесты](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Релизы](https://github.com/gaochenyang666-droid/interview-intel/releases) · [Лицензия MIT](LICENSE)

Interview Intel это устанавливаемый Agent Skill. Он исследует работодателя и вакансию, собирает публичные отзывы и истории собеседований, создаёт десять вопросов с метками происхождения и запускает интерактивное собеседование с локальным состоянием. Итоговый отчёт на упрощённом китайском языке содержит ссылки, даты, уровни достоверности и пробелы в данных.

> Версия разработки: `0.2.0-beta.1`. Веб-поиск и открытие публичных страниц выполняет агент. Python-инструменты строят план, проверяют доказательства, создают вопросы, хранят состояние сессии и формируют отчёт. Сами по себе они не обходят сайты.

## Быстрый старт

```text
Страна: Китай
Компания: ByteDance
Должность: Product Operations
```

Для неизвестного поля используйте `0`. Нужно указать компанию или должность. Резюме, ссылка на вакансию и данные интервьюеров не требуются. Числовая оценка компании по умолчанию отключена.

```bash
python3 scripts/interview_intel.py quick "China/ByteDance/Product Operations" --output request.json
python3 scripts/interview_intel.py plan request.json --format json --output research-plan.json
```

## Возможности

- Изучает официальные сведения о компании, требования вакансии, зарплатные сигналы и актуальный контекст.
- При наличии компании проверяет минимум две независимые публичные площадки.
- Сохраняет положительные, отрицательные и смешанные отзывы со ссылками, датами и ограничениями.
- Ищет публичные истории собеседований на английском и основном языке страны.
- Сначала использует ту же компанию и должность, затем смежную роль, похожую компанию и прогноз по вакансии.
- Создаёт десять вопросов с разной структурой для инженерных, аналитических, продуктовых, операционных и управленческих ролей.
- Поддерживает HR-скрининг, профессиональный, технический, бизнес-кейс и финальный этап.
- Задаёт один вопрос за раз, использует контекстные уточнения и меняет сложность.

Конкретные интервьюеры не исследуются. Система не обходит авторизацию, CAPTCHA, платный доступ или ограничения платформ. Поисковый сниппет не считается проверенным доказательством.

## Уровни доказательств

| Уровень | Источник | Метка |
| --- | --- | --- |
| 1 | Та же компания и должность | `historical_exact` |
| 2 | Та же компания и смежная роль | `historical_similar_role` |
| 3 | Похожая компания и та же должность | `similar_company` |
| 4 | Прогноз по должности и описанию вакансии | `prediction` |

Историческая метка требует точного вопроса из связанной публичной истории. Для смежной роли и похожей компании нужно обоснование переноса. Подробнее: [руководство по практике](references/interview-practice.md).

## Генерация и собеседование

```bash
python3 scripts/interview_intel.py generate-questions research.json \
  --output research-labelled.json
python3 scripts/interview_intel.py validate research-labelled.json
python3 scripts/interview_intel.py render research-labelled.json --output report.md

python3 scripts/interview_simulator.py start research-labelled.json \
  --state .interview-intel/session.json
python3 scripts/interview_simulator.py answer --answer "Мой ответ"
python3 scripts/interview_simulator.py skip
python3 scripts/interview_simulator.py finish
```

В чате используйте `开始模拟面试` для начала, `结束面试` для обратной связи и `重新开始` для нового сеанса.

## Отчёт

Отчёт содержит краткое резюме и шесть разделов: компания, отзывы сотрудников, должность, публичные истории собеседований, прогноз и подготовка, источники и достоверность.

[Входные данные](references/input-schema.md) · [Доказательства](references/evidence-schema.md) · [Структура отчёта](references/report-spec.md)

## Установка

Требуются Git, Python 3.10 или новее и агент с доступом к публичному веб-поиску и локальным Python.

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

Для Claude Code:

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

Другие способы:

```bash
npx skills add gaochenyang666-droid/interview-intel --skill interview-intel
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
```

Устанавливайте весь каталог, включая `SKILL.md`, `scripts/` и `references/`. Дополнительные инструкции: [PUBLISHING.md](PUBLISHING.md).

## Пример вызова

```text
Используй Interview Intel для Microsoft, Software Engineer II, Redmond.
Найди свежие публичные отзывы и истории собеседований.
Создай десять вопросов со ссылками и предложи техническое собеседование.
```

## Ограничения и конфиденциальность

- Полнота данных зависит от поисковых возможностей агента.
- Закрытые страницы и CAPTCHA не обходятся.
- Анонимные отзывы остаются мнениями без подтверждённого статуса сотрудника.
- Копии одной публикации не считаются независимыми источниками.
- Отсутствие доказательств показывается как пробел.
- Резюме, личные контакты, адреса и посторонние чувствительные данные не собираются.
- Без веб-доступа выдаётся план без выдуманных выводов.

## Тесты

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate \
  examples/research-us-software-engineer.json
```

**Лицензия:** [MIT](LICENSE).
