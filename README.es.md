# Interview Intel

**Investigación global para preparar entrevistas con IA y fuentes verificables.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![Pruebas](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Versión beta](https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1) · [Licencia MIT](LICENSE)

**Interview Intel** es una habilidad instalable para agentes de IA (Agent Skill) que investiga empresas, puestos de trabajo, señales salariales, opiniones laborales, procesos de selección y los antecedentes **profesionales públicos** de responsables de selección o entrevistadores. El resultado es un **informe en chino simplificado**, con enlaces a las fuentes, niveles de confianza y limitaciones explícitas.

> **Estado: beta pública v0.1.0-beta.1.** El agente anfitrión realiza las búsquedas y consulta las páginas públicas. Los scripts de Python generan planes, validan pruebas y redactan el informe; **no rastrean sitios web por sí solos**.

## Funcionalidades

| Necesidad | Qué analiza |
| --- | --- |
| Evaluar una empresa | Información oficial, actividad empresarial, contratación, experiencias laborales y discrepancias entre fuentes. |
| Entender una oferta | Descripción del puesto, responsabilidades, requisitos, señales salariales y diferencias por ubicación o nivel. |
| Investigar el ambiente laboral | Opiniones de empleados y comunidades públicas, con fechas, sesgos y procedencia. |
| Preparar una entrevista con una persona concreta | Trayectoria profesional verificada, publicaciones y criterios de contratación expresados públicamente, cuando existan. |
| Entrenar la entrevista | Estrategia personalizada, preguntas para el entrevistador y **10 preguntas de práctica identificadas como predicciones**. |

La búsqueda comienza en **inglés** y continúa en el **idioma local** del país de interés. El catálogo incluye fuentes potenciales como LinkedIn, Indeed, Glassdoor, Reddit, Blind, 牛客, 脉脉, OpenWork, JobPlanet, Naukri y SEEK. La inclusión de una plataforma no garantiza que sus contenidos sean accesibles.

## Instalación en distintos asistentes de IA

Interview Intel utiliza el formato abierto **Agent Skills (`SKILL.md`)**. Puede integrarse en varios agentes compatibles. Elegir un modelo GPT, Claude o Gemini por sí solo no instala la habilidad.

**Requisitos:** Git, Python 3.10 o posterior y un agente con acceso a búsqueda web o navegador y permiso para ejecutar Python localmente. Las utilidades no requieren paquetes Python externos ni una API de pago.

### Opción A: instalación compartida

En macOS y Linux, Codex, Gemini CLI, Cursor, GitHub Copilot, OpenCode y versiones compatibles de Windsurf / Devin Desktop reconocen **`~/.agents/skills/`**:

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

Abre una sesión nueva o actualiza las habilidades. **Claude Code** utiliza su propia carpeta:

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

También puedes instalarla en las rutas específicas de cada producto:

| Cliente | Carpeta personal | Carpeta de proyecto |
| --- | --- | --- |
| **OpenAI Codex** | `~/.agents/skills/` | `.agents/skills/` |
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` |
| **Google Gemini CLI** | `~/.gemini/skills/` o `~/.agents/skills/` | `.gemini/skills/` o `.agents/skills/` |
| **Cursor** | `~/.cursor/skills/` o `~/.agents/skills/` | `.cursor/skills/` o `.agents/skills/` |
| **GitHub Copilot (CLI / VS Code Agent)** | `~/.copilot/skills/` o `~/.agents/skills/` | `.github/skills/` o `.agents/skills/` |
| **OpenCode** | `~/.config/opencode/skills/` o `~/.agents/skills/` | `.opencode/skills/` o `.agents/skills/` |
| **Windsurf / Devin Desktop** | `~/.codeium/windsurf/skills/` o `~/.agents/skills/` | `.windsurf/skills/` o `.agents/skills/` |

Estas son carpetas **contenedoras**: copia el directorio completo en `<ruta>/interview-intel/`, incluyendo `SKILL.md`, `scripts/` y `references/`. En Windows, usa las rutas y comandos equivalentes.

### Opción B: instalador de Gemini CLI

```bash
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
gemini skills list
```

En Gemini CLI, `/skills list` muestra las habilidades y `/skills reload` vuelve a detectarlas. Acepta la activación cuando se te solicite.

### ChatGPT y Claude en el navegador

- **ChatGPT Skills:** Si tu cuenta o espacio de trabajo reúne los requisitos, ve a **Plugins → Skills → Create → Upload from your computer** y sube un paquete revisado. Esta opción es independiente de Codex. [Documentación oficial](https://help.openai.com/en/articles/20001066-skills-in-chatgpt).
- **Claude.ai:** Las cuentas compatibles permiten importar habilidades personalizadas desde la configuración de Skills, normalmente mediante un archivo ZIP. El acceso web y la ejecución de código dependen del entorno. [Documentación oficial](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview).

Para ejecutar todo el flujo de Interview Intel se necesitan **búsquedas reales y validación con Python**. En una interfaz sin ejecución de archivos, solo puede reutilizarse la metodología, sin afirmar que se ejecutaron las comprobaciones.

### Cómo invocar la habilidad

| Cliente | Ejemplo |
| --- | --- |
| Codex | `Use $interview-intel to research ...` |
| Claude Code | `/interview-intel` o una petición en lenguaje natural |
| Gemini CLI | Pide usar Interview Intel; compruébalo con `/skills list` |
| Cursor / GitHub Copilot / OpenCode | En modo agente: `Usa la habilidad Interview Intel para investigar ...` |
| Windsurf / Devin Desktop | Indícalo en Cascade; `@interview-intel` si está disponible |
| ChatGPT / Claude web | Selecciona la habilidad personalizada instalada, si está disponible |

Ejemplo independiente del cliente:

```text
Usa la habilidad Interview Intel para preparar un informe con fuentes.
Empresa: Microsoft
Puesto: Software Engineer II
Lugar: Redmond, Estados Unidos
Enlace a la oferta: [opcional]
Entrevistador: [nombre, cargo y perfil profesional público, opcional]
Experiencia: C#, sistemas distribuidos, Azure
Prioridades: entrevista técnica, equipo, salario
```

**Solo son obligatorios empresa y puesto.** Actualmente, el informe final se genera en **chino simplificado**.

**Documentación de plataformas:** [Codex](https://learn.chatgpt.com/docs/build-skills) · [Claude Code](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) · [Gemini CLI](https://geminicli.com/docs/cli/skills/) · [Cursor](https://cursor.com/docs/skills) · [Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) · [OpenCode](https://opencode.ai/docs/skills) · [Windsurf / Devin Desktop](https://docs.devinai.cn/desktop/cascade/skills)

## Ejemplos de uso

**Buscar información local en otro idioma:**

```text
Usa la habilidad Interview Intel para investigar Toyota y el puesto Product Manager en Japón.
Consulta primero las ofertas oficiales y después las comunidades japonesas.
Entrega un informe con fuentes, limitaciones y preguntas de práctica.
```

**Analizar a un entrevistador identificado:**

```text
Usa la habilidad Interview Intel. Empresa: [empresa]. Puesto: [puesto].
Entrevistador: [nombre, cargo y URL de perfil profesional público].
Confirma su identidad antes de atribuirle experiencia o publicaciones.
Extrae temas profesionales relevantes y distingue predicciones de hechos.
```

**Contrastar opiniones contradictorias:**

```text
Usa la habilidad Interview Intel para [empresa], [puesto] y [ciudad].
Compara la información oficial con opiniones laborales recientes y accesibles.
Separa hechos, experiencias anónimas, inferencias y lagunas de información.
```

## ¿Qué contiene el informe?

El informe se genera actualmente en **Markdown y chino simplificado**. Incluye un resumen ejecutivo y seis apartados:

1. Presentación y evaluación de la empresa.
2. Opiniones de empleados y redes sociales.
3. Análisis del puesto, remuneración y riesgos.
4. Información profesional pública sobre RR. HH. y entrevistadores.
5. Predicciones de entrevista y plan de preparación.
6. Fuentes originales, confianza y datos pendientes de verificar.

Los hallazgos distinguen hechos verificados, declaraciones de primera mano, opiniones de terceros, inferencias, predicciones y ausencia de pruebas. Se conservan los enlaces originales y las fechas disponibles. Si la identidad de una persona es ambigua, el sistema evita atribuirle datos.

**[Ver informe de ejemplo: Microsoft Software Engineer II](examples/report-us-software-engineer.md)** · [Esquema de entrada](references/input-schema.md) · [Reglas de evidencia](references/evidence-schema.md) · [Formato del informe](references/report-spec.md)

## Herramientas de línea de comandos

La CLI sirve para planificar, validar y generar el informe a partir de evidencias ya recopiladas. **No realiza búsquedas en Internet automáticamente**.

```bash
cd interview-intel
python3 scripts/interview_intel.py --help

# Generar un plan de investigación
python3 scripts/interview_intel.py plan examples/input-us-software-engineer.json --format markdown

# Crear el documento de evidencias para que el agente lo complete
python3 scripts/interview_intel.py scaffold examples/input-us-software-engineer.json --output research.json

# Validar las evidencias
python3 scripts/interview_intel.py validate research.json

# Generar el informe en chino simplificado
python3 scripts/interview_intel.py render research.json --output report.md

# Consultar fuentes candidatas para Japón
python3 scripts/interview_intel.py catalog --country JP
```

También puedes validar el [archivo de investigación de ejemplo](examples/research-us-software-engineer.json) sin efectuar búsquedas.

## Alcance, fiabilidad y privacidad

- El [catálogo de fuentes](references/source-catalog.json) y los [perfiles de país](references/country-profiles.json) orientan la investigación internacional. La cobertura real depende de los resultados accesibles.
- Los fragmentos de buscadores, las páginas bloqueadas y las publicaciones duplicadas no se convierten en pruebas independientes.
- El nombre de una persona no basta para identificarla; se requieren atributos profesionales compatibles y fuentes independientes.
- No se eluden inicios de sesión, CAPTCHAs, muros de pago ni controles de acceso. No se recopilan direcciones privadas, contactos personales ni datos íntimos.
- Si no hay herramientas de búsqueda, se entrega únicamente un plan y se explican las limitaciones; no se inventan hallazgos.

Consulta la [metodología](references/research-playbook.md), las [reglas de fuentes](references/source-routing.md) y el [historial de cambios](CHANGELOG.md).

## Pruebas y contribuciones

```bash
python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate examples/research-us-software-engineer.json
```

Puedes comunicar problemas o sugerencias en [Issues](https://github.com/gaochenyang666-droid/interview-intel/issues). Evita incluir currículos reales, datos privados o contenido de acceso restringido. Lee [CONTRIBUTING.md](CONTRIBUTING.md).

**Licencia:** [MIT](LICENSE).
