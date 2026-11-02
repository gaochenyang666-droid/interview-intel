# Interview Intel

**Investigación de empresas, inteligencia de entrevistas y práctica conversacional para agentes de IA, con fuentes verificables.**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![Pruebas](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Versiones](https://github.com/gaochenyang666-droid/interview-intel/releases) · [Licencia MIT](LICENSE)

Interview Intel es una Agent Skill instalable. Investiga empresas y puestos, recopila opiniones laborales públicas y experiencias de entrevista, genera diez preguntas con etiquetas de origen y ofrece una entrevista simulada con estado local. El informe final se escribe en chino simplificado e incluye enlaces originales, fechas, confianza y lagunas de información.

> Versión de desarrollo: `0.2.0-beta.1`. El agente anfitrión realiza las búsquedas y abre páginas públicas. Las herramientas Python planifican, validan, generan preguntas, conservan el estado y crean el informe. No rastrean la web por sí solas.

## Inicio rápido

```text
País: China
Empresa: ByteDance
Puesto: Product Operations
```

Usa `0` para un campo desconocido. Debes indicar al menos empresa o puesto. No se requiere CV, enlace de empleo ni datos de entrevistadores. La puntuación numérica de la empresa está desactivada por defecto.

```bash
python3 scripts/interview_intel.py quick "China/ByteDance/Product Operations" --output request.json
python3 scripts/interview_intel.py plan request.json --format json --output research-plan.json
```

## Capacidades

- Investiga información oficial de la empresa, requisitos del puesto, señales salariales y contexto reciente.
- Consulta al menos dos plataformas públicas e independientes cuando se indica una empresa.
- Conserva experiencias positivas, negativas y mixtas con fecha, enlace y limitaciones.
- Busca experiencias de entrevista en inglés y en el idioma principal del país.
- Prioriza misma empresa y puesto, puesto relacionado, empresa comparable y predicción basada en el puesto.
- Genera diez preguntas adaptadas al tipo de puesto y marca su procedencia.
- Ofrece entrevistas de selección, profesionales, técnicas, casos de negocio y rondas finales.
- Formula una pregunta cada vez, aplica seguimientos contextuales y ajusta la dificultad.

No investiga entrevistadores concretos ni evita controles de acceso. Los fragmentos de búsqueda no se consideran pruebas verificadas.

## Niveles de evidencia

| Nivel | Fuente | Etiqueta |
| --- | --- | --- |
| 1 | Misma empresa y puesto | `historical_exact` |
| 2 | Misma empresa y puesto relacionado | `historical_similar_role` |
| 3 | Empresa comparable y mismo puesto | `similar_company` |
| 4 | Predicción basada en puesto y JD | `prediction` |

Las etiquetas históricas requieren una pregunta textual incluida en la experiencia pública enlazada. Las preguntas de empresas comparables necesitan una justificación de transferencia. Consulta [la guía de práctica](references/interview-practice.md).

## Generación y práctica

```bash
python3 scripts/interview_intel.py generate-questions research.json \
  --output research-labelled.json
python3 scripts/interview_intel.py validate research-labelled.json
python3 scripts/interview_intel.py render research-labelled.json --output report.md

python3 scripts/interview_simulator.py start research-labelled.json \
  --state .interview-intel/session.json
python3 scripts/interview_simulator.py answer --answer "Mi respuesta"
python3 scripts/interview_simulator.py skip
python3 scripts/interview_simulator.py finish
```

En conversación, usa `开始模拟面试` para comenzar, `结束面试` para recibir comentarios y `重新开始` para reiniciar.

## Informe

El informe contiene un resumen y seis secciones: empresa, opiniones laborales, puesto, experiencias históricas de entrevista, predicción y preparación, y fuentes y confianza.

[Entrada](references/input-schema.md) · [Evidencia](references/evidence-schema.md) · [Formato del informe](references/report-spec.md)

## Instalación

Requisitos: Git, Python 3.10 o posterior y un agente con acceso web público y ejecución local de Python.

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

Claude Code:

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

También puede instalarse con:

```bash
npx skills add gaochenyang666-droid/interview-intel --skill interview-intel
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
```

Instala el directorio completo, incluidos `SKILL.md`, `scripts/` y `references/`. Consulta [PUBLISHING.md](PUBLISHING.md) para más clientes.

## Ejemplo

```text
Usa Interview Intel para Microsoft, Software Engineer II, Redmond.
Busca opiniones públicas recientes y experiencias de entrevista.
Genera diez preguntas con fuentes y ofrece una entrevista técnica simulada.
```

## Límites y privacidad

- La cobertura depende de las capacidades de búsqueda del agente.
- No se evitan inicios de sesión, CAPTCHA ni muros de pago.
- Las opiniones anónimas son opiniones y no pruebas de empleo.
- Las publicaciones duplicadas comparten una sola procedencia.
- La falta de pruebas se informa como laguna.
- No se recopilan CV, contactos privados, direcciones ni datos íntimos.
- Sin acceso web se entrega un plan, sin conclusiones inventadas.

## Pruebas

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate \
  examples/research-us-software-engineer.json
```

**Licencia:** [MIT](LICENSE).
