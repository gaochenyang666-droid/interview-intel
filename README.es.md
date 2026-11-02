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

## Instalación rápida con Codex

**Requisitos:** Python 3.10 o posterior, Git y un agente con herramientas de búsqueda web o navegador. Los scripts locales no necesitan paquetes adicionales de Python ni API de pago.

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.codex/skills
cp -R interview-intel ~/.codex/skills/interview-intel
```

Abre una **nueva sesión de Codex** y utiliza `$interview-intel`:

```text
Usa $interview-intel para preparar mi entrevista.
Empresa: Microsoft
Puesto: Software Engineer II
Ubicación: Redmond, Estados Unidos
Enlace de la oferta: [opcional]
Entrevistador o RR. HH.: [nombre y perfil profesional público, opcional]
Mi experiencia: C#, sistemas distribuidos, Azure
Prioridades: cultura de equipo, entrevista técnica y salario
```

**Solo son obligatorios el nombre de la empresa y el puesto.** Puedes añadir ciudad, país, oferta, etapa del proceso, experiencia y datos profesionales públicos del entrevistador para mejorar la precisión. La instalación en otros agentes compatibles con Agent Skills depende de sus propias instrucciones; consulta [SKILL.md](SKILL.md).

## Ejemplos de uso

**Buscar información local en otro idioma:**

```text
Usa $interview-intel para investigar Toyota y el puesto Product Manager en Japón.
Consulta primero las ofertas oficiales y después las comunidades japonesas.
Entrega un informe con fuentes, limitaciones y preguntas de práctica.
```

**Analizar a un entrevistador identificado:**

```text
Usa $interview-intel. Empresa: [empresa]. Puesto: [puesto].
Entrevistador: [nombre, cargo y URL de perfil profesional público].
Confirma su identidad antes de atribuirle experiencia o publicaciones.
Extrae temas profesionales relevantes y distingue predicciones de hechos.
```

**Contrastar opiniones contradictorias:**

```text
Usa $interview-intel para [empresa], [puesto] y [ciudad].
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
