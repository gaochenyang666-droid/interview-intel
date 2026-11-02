# Interview Intel

**Глобальная подготовка к собеседованию с помощью ИИ и проверяемых источников.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![Тесты](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Бета-релиз](https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1) · [Лицензия MIT](LICENSE)

**Interview Intel** — подключаемый навык (Agent Skill) для ИИ-агентов. Он помогает изучать компанию и вакансию, публичные отзывы сотрудников, сведения о зарплатах и этапах отбора. Результат — **отчёт на упрощённом китайском языке** с ссылками на источники, оценкой достоверности и обозначенными пробелами в данных.

> **Статус: публичная бета v0.1.0-beta.1.** Поиск и открытие сайтов выполняет ИИ-агент, в котором установлен навык. Скрипты Python формируют план, проверяют доказательства и создают отчёт; **сами сайты они не обходят**.

## Быстрый старт: всего три поля

Отправьте агенту с установленным Interview Intel:

```text
Страна: Китай
Компания: ByteDance
Должность: Product Operations
```

**Если данные неизвестны, укажите `0`.** Страна `0`: глобальный поиск; компания `0`: исследование вакансии; должность `0`: исследование работодателя. Нужно указать компанию или должность. Резюме и личные данные не требуются. Числовая оценка по умолчанию отключена.

```bash
python3 scripts/interview_intel.py quick "China/ByteDance/Product Operations" --output request.json
```

Команда только создаёт файл входных данных; веб-поиск выполняет агент.

## Возможности

| Задача | Что исследуется |
| --- | --- |
| Оценка работодателя | Официальные сведения о компании, бизнес-контекст, найм, отзывы и расхождения между источниками. |
| Анализ вакансии | Обязанности, требования, опубликованные данные о зарплатах, различия между городами и уровнями должности. |
| Изучение рабочей среды | Публичные отзывы сотрудников и обсуждения в соцсетях с учётом дат, ограничений выборки и происхождения сообщений. |
| Практическая подготовка | План подготовки, вопросы работодателю и **10 тренировочных вопросов с явной пометкой «прогноз»**. |

Поиск начинается **на английском**, затем добавляются запросы **на местном языке**. В каталоге возможных источников есть LinkedIn, Indeed, Glassdoor, Reddit, Blind, 牛客, 脉脉, OpenWork, JobPlanet, Naukri, SEEK и региональные площадки. Наличие площадки в каталоге не гарантирует доступ к её материалам.

## Установка для разных ИИ-агентов

Interview Intel использует открытый формат **Agent Skills (`SKILL.md`)** и может работать в нескольких совместимых ИИ-агентах. Сам по себе выбор модели GPT, Claude или Gemini навык не устанавливает.

**Требования:** Git, Python 3.10+ и агент с доступом к веб-поиску/браузеру и возможностью запускать локальный Python. Платные API и дополнительные пакеты Python для утилит не обязательны.

### Вариант A: общая установка

В macOS и Linux Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode и совместимые версии Windsurf / Devin Desktop распознают каталог **`~/.agents/skills/`**:

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

Откройте новую сессию агента или обновите список навыков. Для **Claude Code** используйте отдельный каталог:

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

При желании можно использовать собственные каталоги клиентов:

| Клиент | Личный каталог | Каталог проекта |
| --- | --- | --- |
| **OpenAI Codex** | `~/.agents/skills/` | `.agents/skills/` |
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` |
| **Google Gemini CLI** | `~/.gemini/skills/` или `~/.agents/skills/` | `.gemini/skills/` или `.agents/skills/` |
| **Cursor** | `~/.cursor/skills/` или `~/.agents/skills/` | `.cursor/skills/` или `.agents/skills/` |
| **GitHub Copilot (CLI / VS Code Agent)** | `~/.copilot/skills/` или `~/.agents/skills/` | `.github/skills/` или `.agents/skills/` |
| **OpenCode** | `~/.config/opencode/skills/` или `~/.agents/skills/` | `.opencode/skills/` или `.agents/skills/` |
| **Windsurf / Devin Desktop** | `~/.codeium/windsurf/skills/` или `~/.agents/skills/` | `.windsurf/skills/` или `.agents/skills/` |

В таблице указаны **родительские каталоги**. Устанавливайте всю папку `interview-intel`, включая `SKILL.md`, `scripts/` и `references/`, в `<каталог>/interview-intel/`. В Windows используйте эквивалентные пути и команды копирования.

### Вариант B: установщик Gemini CLI

```bash
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
gemini skills list
```

В Gemini CLI проверьте список через `/skills list`, обновите его командой `/skills reload` и подтвердите активацию при запросе.

### ИИ-агенты из Китая

Шесть клиентов официально поддерживают навыки с `SKILL.md`: **Qwen Code, Kimi Code CLI, TRAE China, Qoder, Tencent CodeBuddy Code и Zhipu ZCode**. После клонирования репозитория копируйте всю папку со скриптами и справочниками:

```bash
# Qwen Code
mkdir -p ~/.qwen/skills && cp -R interview-intel ~/.qwen/skills/interview-intel
# Kimi Code CLI
mkdir -p ~/.kimi-code/skills && cp -R interview-intel ~/.kimi-code/skills/interview-intel
# TRAE (China)
mkdir -p ~/.trae-cn/skills && cp -R interview-intel ~/.trae-cn/skills/interview-intel
# Tencent CodeBuddy Code
mkdir -p ~/.codebuddy/skills && cp -R interview-intel ~/.codebuddy/skills/interview-intel
# Zhipu ZCode
mkdir -p ~/.zcode/skills && cp -R interview-intel ~/.zcode/skills/interview-intel
```

**Qoder:** Работает с `~/.agents/skills/interview-intel/`; также можно импортировать проверенный ZIP через **Extensions → Skills → Add Skills → Upload Skill**.

**Вызов:** Qwen Code: `/interview-intel` или `/skills`; Kimi Code CLI: `/skill:interview-intel`; CodeBuddy Code: `/skills`; ZCode: **Settings → Skills → Refresh**; TRAE: запросите навык в агенте; Qoder: выберите его через `/`.

**Другие пути:** Qwen Code и Kimi Code CLI поддерживают `~/.agents/skills/` и проектные `.qwen/skills/`, `.kimi-code/skills/`. TRAE использует `.trae/skills/`, а папку `.agents/skills/` для проекта нужно включить в настройках. CodeBuddy Code использует `.codebuddy/skills/`.

**Модели и клиенты:** DeepSeek, Doubao, GLM и MiniMax можно использовать через совместимые агенты. Обычное чат-приложение или модель сами по себе не гарантируют поддержку `SKILL.md`. Для полноценной работы нужны веб-поиск и запуск Python.

Официальные документы: [Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) · [Kimi Code CLI](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html) · [TRAE](https://docs.trae.cn/ide_skills?lang=zh) · [Qoder](https://docs.qoder.com/qoder/skills) · [CodeBuddy Code](https://www.codebuddy.cn/docs/cli/skills) · [ZCode](https://zcode.z.ai/en/docs/skill)

### ChatGPT и Claude в браузере

- **ChatGPT Skills:** В поддерживаемых аккаунтах и рабочих пространствах откройте **Plugins → Skills → Create → Upload from your computer** и загрузите проверенный пакет. Эта установка не связана с локальной установкой Codex. [Документация OpenAI](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).
- **Claude.ai:** Поддерживаемые аккаунты могут импортировать собственные навыки через настройки Skills, обычно из ZIP-архива. Возможности веб-поиска и запуска кода зависят от среды. [Документация Anthropic](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

Для полноценной работы Interview Intel необходимы **живой веб-поиск и проверка доказательств через Python**. В интерфейсе без запуска файлов можно использовать методику исследования, но нельзя считать, что полный процесс проверки был выполнен.

### Вызов навыка

| Клиент | Пример |
| --- | --- |
| Codex | `Use $interview-intel to research ...` |
| Claude Code | `/interview-intel` или запрос на естественном языке |
| Gemini CLI | Попросите использовать Interview Intel; проверьте через `/skills list` |
| Cursor / GitHub Copilot / OpenCode | В режиме агента: `Используй навык Interview Intel для исследования ...` |
| Windsurf / Devin Desktop | Обратитесь к Cascade; `@interview-intel`, если поддерживается |
| ChatGPT / Claude web | Выберите установленный пользовательский навык, если он доступен |

Пример запроса для любого совместимого агента:

```text
Используй навык Interview Intel и подготовь отчёт со ссылками на источники.
Компания: Microsoft
Должность: Software Engineer II
Место: Редмонд, США
Ссылка на вакансию: [необязательно]
Мой опыт: C#, распределённые системы, Azure
Приоритеты: техническое интервью, культура команды, зарплата
```

**Достаточно указать компанию или должность.** Текущий формат итогового отчёта: **Markdown на упрощённом китайском языке**.

**Официальные инструкции:** [Codex](https://learn.chatgpt.com/docs/build-skills) · [Claude Code](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) · [Gemini CLI](https://geminicli.com/docs/cli/skills/) · [Cursor](https://cursor.com/docs/skills) · [Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) · [OpenCode](https://opencode.ai/docs/skills) · [Windsurf / Devin Desktop](https://docs.devinai.cn/desktop/cascade/skills)

## Примеры использования

**Исследование локального рынка:**

```text
Используй навык Interview Intel. Компания: Toyota.
Должность: Product Manager. Страна: Япония.
Проверь официальные вакансии и найди публичные отзывы на японском языке.
Подготовь отчёт с ссылками и обозначенными ограничениями.
```

**Сравнение противоречивых отзывов:**

```text
Используй навык Interview Intel для [компания] и вакансии [должность] в [город].
Сравни официальную информацию с доступными отзывами сотрудников.
Укажи, какие утверждения проверены, какие являются мнениями, а что неизвестно.
```

## Что входит в отчёт?

Текущий формат вывода — **Markdown на упрощённом китайском языке**. Сначала идёт краткое резюме, затем пять разделов:

1. Обзор и оценка компании.
2. Отзывы сотрудников и обсуждения в социальных сетях.
3. Анализ вакансии, зарплатных ориентиров и рисков.
4. Предполагаемые темы интервью и план подготовки.
5. Первоисточники, уровень достоверности и пробелы.

Факты, личные публичные заявления, мнения третьих лиц, аналитические выводы, прогнозы и отсутствие информации отмечаются отдельно. При необходимости приводятся даты и ссылки на просмотренные источники.

**[Пример отчёта: Microsoft Software Engineer II](examples/report-us-software-engineer.md)** · [Формат входных данных](references/input-schema.md) · [Схема доказательств](references/evidence-schema.md) · [Структура отчёта](references/report-spec.md)

## Командная строка

CLI предназначен для подготовки плана, проверки данных и создания отчёта. **Он не выполняет веб-поиск самостоятельно**.

```bash
cd interview-intel
python3 scripts/interview_intel.py --help

# Построить план исследования
python3 scripts/interview_intel.py plan examples/input-us-software-engineer.json --format markdown

# Создать шаблон файла с доказательствами
python3 scripts/interview_intel.py scaffold examples/input-us-software-engineer.json --output research.json

# Проверить заполненные доказательства
python3 scripts/interview_intel.py validate research.json

# Сформировать отчёт на китайском языке
python3 scripts/interview_intel.py render research.json --output report.md

# Посмотреть источники по Японии
python3 scripts/interview_intel.py catalog --country JP
```

Для проверки без поиска можно использовать [подготовленные примерные данные](examples/research-us-software-engineer.json).

## Публичные отзывы сотрудников и социальные сети

При наличии названия компании агент **обязательно пытается изучить минимум две независимые внешние площадки**, желательно три, открывая общедоступные оригинальные публикации. Для Китая приоритетны Zhihu, Maimai, Xiaohongshu, Nowcoder и Weibo, в других странах используются местные сообщества.

Отчёт показывает **фактически проверенные платформы**, ссылки на доступные первоисточники, даты и подтверждённые содержанием постов положительные и отрицательные мнения. Ограничения доступа и анонимность указываются открыто. Доступный пост ещё не доказывает, что автор действительно работал в компании.

**Числовая оценка по умолчанию выключена** и доступна только по явному запросу согласно [дополнительной методике](references/scoring-rubric.md).

## Источники, достоверность и конфиденциальность

- [Каталог источников](references/source-catalog.json) и [профили стран](references/country-profiles.json) позволяют искать данные в разных регионах. Фактическое покрытие зависит от доступности публичных страниц.
- Сниппеты поиска, закрытые страницы и копии одной публикации не считаются независимыми подтверждениями.
- Система не обходит авторизацию, CAPTCHA, платный доступ и другие ограничения; не собирает домашние адреса, личные контакты и сведения о частной жизни.
- При отсутствии инструментов поиска доступен план исследования, но выводы о компании  не выдумываются.

Подробнее: [методика исследования](references/research-playbook.md), [маршрутизация источников](references/source-routing.md), [история изменений](CHANGELOG.md).

## Тесты и участие

```bash
python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate examples/research-us-software-engineer.json
```

Ошибки, устаревшие вакансии и неверные сопоставления можно сообщать через [Issues](https://github.com/gaochenyang666-droid/interview-intel/issues). Не прикладывайте личные резюме, приватные данные. Правила участия: [CONTRIBUTING.md](CONTRIBUTING.md).

**Лицензия:** [MIT](LICENSE).
