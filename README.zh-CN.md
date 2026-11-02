# Interview Intel

**全球面试情报 Skill：查公司、查岗位、看公开员工评价，带着证据准备面试。**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![自动测试](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Beta 版本](https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1) · [MIT 许可证](LICENSE)

Interview Intel 是一个可以安装到 AI Agent 的面试研究技能。只需输入**公司或岗位中的至少一项**，Agent 就能检索企业官方资料、招聘页面、员工评价、职业社区、薪酬线索与公开面经，最终生成**带原始链接和可信度说明的中文报告**。

> **当前版本：v0.1.0-beta.1（公开测试版）。** 联网搜索由宿主 Agent 的搜索或浏览器工具完成；仓库中的 Python 脚本负责生成检索计划、校验证据、去重与渲染报告，**脚本本身不会自动抓取网页**。

## 最简单的使用方法：只填三项

在已安装 Interview Intel 的 AI Agent 中直接输入：

```text
国家：中国
公司：字节跳动
岗位：产品运营
```

**不知道就填 `0`，自动跳过。** 国家为 `0` 时全球搜索；公司为 `0` 时研究岗位；岗位为 `0` 时研究公司。无需填写简历、JD、个人背景或联系人。**公司和岗位至少提供一项**，不能全部填写 `0`。

评分默认关闭，`0` 只表示未知或跳过该项资料。

命令行也支持三字段快捷输入：

```bash
python3 scripts/interview_intel.py quick "中国/字节跳动/产品运营" --output request.json
```

随后由 Agent 执行联网研究并生成报告。上述命令仅创建输入 JSON。

## 能帮你解决什么？

| 想了解的问题 | 可获得的研究结果 |
| --- | --- |
| 这家公司值得去吗？ | 公司背景、业务与招聘动态、员工反馈、不同来源之间的分歧。 |
| 岗位实际做什么？ | 官方 JD、主要职责、技能要求、薪酬观察、地区与职级差异。 |
| 工作环境怎么样？ | 公开员工评价和社交平台讨论，注明时间、样本限制及来源可信度。 |
| 应该怎么准备？ | 针对性准备清单、反问问题及 **10 道标注预测依据的模拟面试题**。 |

研究先使用**英文**查询，再使用目标国家的**本地语言**查询。候选来源包括 LinkedIn、Indeed、Glassdoor、Reddit、Blind、牛客、脉脉、OpenWork、JobPlanet、Naukri、SEEK 等。部分平台需要登录或有访问限制，列入目录不代表可以读取其全部内容。

## 支持哪些 AI？如何安装？

Interview Intel 使用通用的 **Agent Skills（`SKILL.md`）** 结构，可以在多种 AI Agent 中安装使用。具体由支持 Skill 的客户端负责发现、联网检索和调用 Python 脚本；仅切换 GPT、Claude 或 Gemini 模型，并不会自动安装技能。

**运行要求：** Git、Python 3.10 及以上，以及具有公开网页搜索或浏览器工具和本地 Python 执行权限的 Agent。本地脚本无第三方运行时依赖，不强制付费 API。

### 方案 A：一次安装，多款 AI 共用

对于 macOS / Linux，Codex、Gemini CLI、Cursor、GitHub Copilot、OpenCode 以及兼容版本的 Windsurf / Devin Desktop 均可通过通用目录 **`~/.agents/skills/`** 发现 Skill：

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

重新打开 Agent 会话或刷新技能列表。**Claude Code** 建议使用自己的目录：

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

也可以按照下表安装到各客户端的独立目录，或者安装到某个具体项目：

| AI 客户端 | 用户级目录（所有项目） | 项目级目录 |
| --- | --- | --- |
| **OpenAI Codex** | `~/.agents/skills/` | `.agents/skills/` |
| **Claude Code** | `~/.claude/skills/` | `.claude/skills/` |
| **Google Gemini CLI** | `~/.gemini/skills/` 或 `~/.agents/skills/` | `.gemini/skills/` 或 `.agents/skills/` |
| **Cursor** | `~/.cursor/skills/` 或 `~/.agents/skills/` | `.cursor/skills/` 或 `.agents/skills/` |
| **GitHub Copilot（CLI / VS Code Agent）** | `~/.copilot/skills/` 或 `~/.agents/skills/` | `.github/skills/` 或 `.agents/skills/` |
| **OpenCode** | `~/.config/opencode/skills/` 或 `~/.agents/skills/` | `.opencode/skills/` 或 `.agents/skills/` |
| **Windsurf / Devin Desktop** | `~/.codeium/windsurf/skills/` 或 `~/.agents/skills/` | `.windsurf/skills/` 或 `.agents/skills/` |

表中均为**父目录**，需要将整个 `interview-intel` 文件夹放入其中，形成 `<目录>/interview-intel/SKILL.md`。`scripts/` 和 `references/` 也要保留。Windows 用户使用相应的用户目录与复制命令。

### 方案 B：Gemini CLI 直接从 GitHub 安装

```bash
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
gemini skills list
```

进入 Gemini CLI 后，可以使用 `/skills list` 查看已加载技能，或用 `/skills reload` 刷新。触发技能时按照提示批准激活。

### 中国大陆 AI 开发工具

已核实以下六款中国大陆相关 AI Agent 支持 `SKILL.md`：**通义千问 Qwen Code、月之暗面 Kimi Code CLI、字节跳动 TRAE 中国版、Qoder、腾讯 CodeBuddy Code、智谱 ZCode**。先执行上文的 `git clone`，再将包含脚本及参考资料的完整目录安装到对应位置：

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

**Qoder：** 可以直接读取 `~/.agents/skills/interview-intel/`，或在 **Extensions → Skills → Add Skills → Upload Skill** 导入经过审核的 ZIP。

**如何调用：** Qwen Code 使用 `/interview-intel` 或 `/skills`；Kimi Code CLI 使用 `/skill:interview-intel`；腾讯 CodeBuddy Code 使用 `/skills` 检查；ZCode 在 **Settings → Skills → Refresh** 启用；TRAE 在 Agent 对话中指定 Interview Intel；Qoder 输入 `/` 选择技能。

**项目路径与通用目录：** Qwen Code 还支持 `~/.agents/skills/` 与项目 `.qwen/skills/`；Kimi Code CLI 支持 `~/.agents/skills/` 与项目 `.kimi-code/skills/`；TRAE 项目目录为 `.trae/skills/`，要使用项目 `.agents/skills/` 需在“设置 → 技能与命令”启用选项；CodeBuddy Code 项目目录为 `.codebuddy/skills/`。

**关于 DeepSeek、豆包 Doubao、GLM 和 MiniMax：** 它们可作为支持这些模型的 Agent 的底层模型。普通聊天 App 或仅有模型 API 并不保证能够安装 `SKILL.md`；完整研究还需要联网搜索和 Python 执行能力。

官方文档：[Qwen Code](https://qwenlm.github.io/qwen-code-docs/en/users/features/skills/) · [Kimi Code CLI](https://www.kimi.com/code/docs/en/kimi-code-cli/customization/skills.html) · [TRAE](https://docs.trae.cn/ide_skills?lang=zh) · [Qoder](https://docs.qoder.com/qoder/skills) · [CodeBuddy Code](https://www.codebuddy.cn/docs/cli/skills) · [ZCode](https://zcode.z.ai/en/docs/skill)

### ChatGPT 网页版与 Claude 网页版

- **ChatGPT Skills：** 符合资格的工作区可进入 **Plugins → Skills → Create → Upload from your computer**，上传已检查的 Skill 包。是否显示该入口取决于账户与工作区权限。此流程与 Codex 本地安装相互独立。参见 [ChatGPT 官方说明](https://help.openai.com/en/articles/20001066-skills-in-chatgpt)。
- **Claude.ai：** 在支持自定义 Skills 的账户中，可通过 Skills / 设置入口导入 Skill 包（通常为 ZIP）。网页版的联网搜索及代码执行能力取决于具体账户和环境。参见 [Anthropic 官方说明](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview)。

**注意：** Interview Intel 完整研究流程需要网页检索和 Python 证据校验。如果所用 AI 只能聊天、没有本地文件或代码执行权限，可以参考其研究方法，但不能宣称已经执行完整的自动校验流程。

### 各客户端如何调用？

| 客户端 | 调用示例 |
| --- | --- |
| Codex | `使用 Interview Intel Skill 研究……` |
| Claude Code | `/interview-intel`，或直接要求 Claude 使用 Interview Intel |
| Gemini CLI | 自然语言要求使用 Interview Intel；用 `/skills list` 检查 |
| Cursor / GitHub Copilot / OpenCode | 在 Agent 模式中输入 `使用 Interview Intel Skill 研究……` |
| Windsurf / Devin Desktop | 在 Cascade 中指定 Interview Intel；支持时可用 `@interview-intel` |
| ChatGPT / Claude 网页版 | 在支持的界面中选择或调用已导入的 Skill |

跨平台通用提示词：

```text
请使用 Interview Intel Skill，为我生成带有来源链接的面试情报报告。
公司：字节跳动
岗位：产品运营
地点：北京，中国
岗位链接：（可选）
个人背景：用户增长、数据分析经验
重点：团队文化、面试流程、加班情况、薪资和职业发展
```

**公司和岗位至少提供一项即可。** 其他字段可选。无论使用哪种语言输入，当前报告渲染器默认输出**简体中文**。

**各平台官方文档：** [Codex](https://learn.chatgpt.com/docs/build-skills) · [Claude Code](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview) · [Gemini CLI](https://geminicli.com/docs/cli/skills/) · [Cursor](https://cursor.com/docs/skills) · [Copilot](https://docs.github.com/en/copilot/concepts/customizations/agent-skills) · [OpenCode](https://opencode.ai/docs/skills) · [Windsurf / Devin Desktop](https://docs.devinai.cn/desktop/cascade/skills)

## 更多调用方式

**日本岗位研究：**

```text
使用 Interview Intel Skill 研究 Toyota 在日本东京的 Product Manager 岗位。
优先核实官方招聘信息，再用日语检索 OpenWork 等本地平台。
比较岗位职责和员工评价，提供中文报告及全部实际采用的来源。
```

**比较矛盾评价：**

```text
使用 Interview Intel Skill 调查 [公司] [城市] 的 [岗位]。
对比公司官方招聘信息与近期可访问的员工评价。
区分一手事实、匿名体验、推断与没有证据的部分。
```

## 最终会得到什么？

报告默认是**简体中文 Markdown**，开头提供一页式摘要，然后是五个栏目：

1. 公司概况与综合评价
2. 员工及社交媒体评价
3. 岗位评价、薪酬和风险
4. 面试预测与准备建议
5. 原始来源、可信度及信息缺口

报告区分事实、本人公开表述、第三方评价、分析推断、面试预测和信息缺口。重要结论应能追溯到实际打开过的公开页面，并保留原始链接、可获取的日期和证据限制。

**[查看完整的 Microsoft 软件工程师面试报告示例](examples/report-us-software-engineer.md)** · [输入字段说明](references/input-schema.md) · [证据规则](references/evidence-schema.md) · [报告格式](references/report-spec.md)

## 进阶：命令行用法

以下命令用于规划、校验和渲染。**CLI 不会自行联网搜集招聘评价**，Agent 需要先将实际核实的资料写入研究文件。

```bash
cd interview-intel

# 查看全部命令
python3 scripts/interview_intel.py --help

# 生成包含英文和本地语言查询的研究计划
python3 scripts/interview_intel.py plan examples/input-us-software-engineer.json --format markdown

# 创建待填写的证据文件
python3 scripts/interview_intel.py scaffold examples/input-us-software-engineer.json --output research.json

# 检查证据完整性和来源归因
python3 scripts/interview_intel.py validate research.json

# 渲染中文 Markdown 报告
python3 scripts/interview_intel.py render research.json --output report.md

# 查看日本的数据源候选
python3 scripts/interview_intel.py catalog --country JP
```

想直接测试校验器，可以使用仓库内已有的 [Microsoft 示例研究数据](examples/research-us-software-engineer.json)，不必先联网搜集数据。

## 重点功能：公开员工体验与社交平台口碑

输入国家、公司和岗位后，Agent 会**主动搜索职场社区与社交媒体的公开原帖**。只要提供了公司名称，就至少尝试两个独立平台，优先三个。例如中国大陆会重点尝试**知乎、脉脉、小红书、牛客和微博**，其他地区选择相应的职场社区。

报告会列出**实际检索过的平台及结果**。可以打开的员工分享会给出原帖链接、发布日期（如有）与局限，并归纳实际找到的正面、负面和不同观点；需要登录、仅有搜索摘要或无法打开时会明确说明。匿名作者的真实任职经历通常难以独立证明，不能仅凭一条帖子推导整个公司的文化。

**默认取消数字评分，重点呈现可追溯的信息与实际评价。** 只有明确要求“评分”时才启用 [可选评分规则](references/scoring-rubric.md)，三字段输入方式保持不变。

## Skill 商店与扩展安装

仓库现在提供 **Claude Code、Gemini CLI、Cursor** 兼容的插件/扩展清单，也保留原有 `SKILL.md` 跨平台安装方式。以下命令可从 GitHub 安装；**官方商店公开展示仍可能需要索引或人工审核**。

```bash
# skills.sh 生态及兼容 Agent
npx skills add gaochenyang666-droid/interview-intel --skill interview-intel

# Gemini CLI 扩展
gemini extensions install https://github.com/gaochenyang666-droid/interview-intel
```

Claude Code 中先执行 `/plugin marketplace add gaochenyang666-droid/interview-intel`，再执行 `/plugin install interview-intel@interview-intel-marketplace`。Cursor 官方商店需要单独提交审核。

各商店入口、上架材料与当前状态见 [PUBLISHING.md](PUBLISHING.md)。仓库可安装不代表已经获得官方精选商店认证。

## 全球覆盖与可信度

- **全球研究：** 根据国家、岗位和语言动态选择企业官网、招聘平台、职业社交媒体与本地职场社区。数据源可在 [source-catalog.json](references/source-catalog.json) 中扩展。
- **先核实，再下结论：** 搜索摘要只能帮助发现页面；验证码、登录限制及失效页面会单独记录。重复转载不会当成多份独立证据。
- **隐私边界：** 只研究与岗位有关的公开职业信息；不收集私人联系方式、家庭信息，也不绕过登录、付费墙或访问限制。
- **如实处理缺失：** 找不到可靠岗位、薪资或人员资料时，会明确标注。宿主没有搜索工具时，只能输出检索计划，不能冒充已经完成在线研究。

详见 [检索流程](references/research-playbook.md)、[数据源路由](references/source-routing.md) 和 [更新日志](CHANGELOG.md)。

## 测试与参与开发

```bash
python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate examples/research-us-software-engineer.json
```

欢迎通过 [Issues](https://github.com/gaochenyang666-droid/interview-intel/issues) 反馈错误公司匹配、过期岗位、失效来源与面试准备建议。提交问题时请删除个人简历、私人联系方式和受限页面内容。参与贡献参见 [CONTRIBUTING.md](CONTRIBUTING.md)。

**开源许可证：** [MIT](LICENSE)。
