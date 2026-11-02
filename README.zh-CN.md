# Interview Intel

**面向 AI Agent 的可溯源公司调查、面试情报与模拟面试技能。**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![自动测试](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [版本记录](https://github.com/gaochenyang666-droid/interview-intel/releases) · [MIT 许可证](LICENSE)

Interview Intel 可以调查公司、岗位、公开员工讨论和历史面经，生成带原始链接、日期、可信度和信息缺口的中文报告，并提供可连续追问的模拟面试。

> 当前开发版本：`0.2.0-beta.1`。联网检索由宿主 Agent 的公开搜索或浏览器工具完成。Python 工具负责规划、校验、题目生成、会话状态和报告渲染，不会自行抓取网页。

## 三字段开始

```text
国家：中国
公司：字节跳动
岗位：产品运营
```

未知字段填写 `0`，公司或岗位至少提供一项。简历、岗位链接和面试官信息都不是必需项。公司数字评分默认关闭。

```bash
python3 scripts/interview_intel.py quick "中国/字节跳动/产品运营" --output request.json
python3 scripts/interview_intel.py plan request.json --format json --output research-plan.json
```

之后由 Agent 检索公开资料，并将实际打开的来源写入研究 JSON。

## 核心能力

- 调查公司背景、岗位要求、薪酬线索和近期经营状态。
- 提供公司名称时，至少尝试两个独立职场社区或社交平台，优先三个。
- 保留正面、负面和混合体验，记录原帖链接、日期和样本限制。
- 使用英文优先、目标国家主要语言补充的方式检索公开面经。
- 按本公司同岗位、本公司相近岗位、相似公司同岗位、岗位预测四级降级。
- 生成 10 道岗位相关题目，并明确标记历史原题、相近岗位题、相似公司题或 AI 预测题。
- 支持 HR 初筛、专业、技术、业务案例和综合终面模拟。
- 每次只问一道题，根据回答补充追问并调整难度。
- 回答阶段不展示参考答案，结束后生成具体反馈。

本项目不研究具体面试官，不绕过登录、验证码、付费墙或平台权限。搜索摘要只用于发现页面，不能作为已核实证据。

## 面经分级

| 级别 | 来源 | 题目标签 |
| --- | --- | --- |
| 1 | 本公司同岗位 | `historical_exact` |
| 2 | 本公司相近岗位 | `historical_similar_role` |
| 3 | 相似公司同岗位 | `similar_company` |
| 4 | 根据岗位和 JD 预测 | `prediction` |

历史原题必须能在关联的公开面经中找到原文。相近岗位和相似公司题必须提供迁移理由。AI 预测题不得冒充公司历史题。

完整规则见 [面经与模拟面试参考](references/interview-practice.md)。

## 生成题目与模拟面试

```bash
# 为研究文件生成 10 道带来源标签的题目
python3 scripts/interview_intel.py generate-questions research.json \
  --output research-labelled.json

# 校验并渲染中文报告
python3 scripts/interview_intel.py validate research-labelled.json
python3 scripts/interview_intel.py render research-labelled.json --output report.md

# 启动本地有状态模拟面试
python3 scripts/interview_simulator.py start research-labelled.json \
  --state .interview-intel/session.json
python3 scripts/interview_simulator.py answer --answer "我的回答"
python3 scripts/interview_simulator.py skip
python3 scripts/interview_simulator.py finish
```

在对话中输入 `开始模拟面试` 开始，输入 `结束面试` 获取反馈，输入 `重新开始` 清空当前会话。会话文件保存在本地，并已加入 `.gitignore`。

## 报告结构

报告默认使用简体中文，包含一页式摘要和六个栏目：

1. 公司概况与综合评价
2. 员工及社交媒体评价
3. 岗位评价
4. 公开历史面经与匹配
5. 面试预测与准备
6. 来源与可信度

[输入格式](references/input-schema.md) · [证据结构](references/evidence-schema.md) · [报告规范](references/report-spec.md) · [示例报告](examples/report-us-software-engineer.md)

## 安装

运行要求：Git、Python 3.10 及以上，以及能访问公开网页和执行本地 Python 的 Agent。

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.agents/skills
cp -R interview-intel ~/.agents/skills/interview-intel
```

Codex、Gemini CLI、Cursor、GitHub Copilot、OpenCode 及兼容版 Windsurf / Devin Desktop 可使用通用目录。Claude Code 使用：

```bash
mkdir -p ~/.claude/skills
cp -R interview-intel ~/.claude/skills/interview-intel
```

必须安装完整目录，包括 `SKILL.md`、`scripts/` 和 `references/`。各客户端目录如下：

| 客户端 | 用户级目录 | 项目级目录 |
| --- | --- | --- |
| OpenAI Codex | `~/.agents/skills/` | `.agents/skills/` |
| Claude Code | `~/.claude/skills/` | `.claude/skills/` |
| Gemini CLI | `~/.gemini/skills/` 或 `~/.agents/skills/` | `.gemini/skills/` 或 `.agents/skills/` |
| Cursor | `~/.cursor/skills/` 或 `~/.agents/skills/` | `.cursor/skills/` 或 `.agents/skills/` |
| GitHub Copilot | `~/.copilot/skills/` 或 `~/.agents/skills/` | `.github/skills/` 或 `.agents/skills/` |

商店和扩展安装：

```bash
npx skills add gaochenyang666-droid/interview-intel --skill interview-intel
gemini skills install https://github.com/gaochenyang666-droid/interview-intel.git
```

更多分发方式见 [PUBLISHING.md](PUBLISHING.md)。

## 调用示例

```text
使用 Interview Intel Skill 调查 Microsoft 的 Software Engineer II，
地点为 Redmond。查找近期公开员工讨论和面经，生成 10 道带来源标签的题，
然后进入技术模拟面试。
```

```text
使用 Interview Intel Skill。
国家：日本
公司：Toyota
岗位：Product Manager
```

## 可信度与隐私

- 官方页面可以支持公司或岗位事实，不能证明真实员工体验。
- 匿名帖子属于公开观点，作者任职状态通常无法核实。
- 转载和同源内容只算一个来源谱系。
- 信息缺失标记为缺口，不能解释为没有负面评价。
- 不收集简历、私人联系方式、家庭信息、住址和无关敏感资料。
- 无网络或搜索工具时只输出计划和限制，不生成研究结论。

## 测试

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
python3 scripts/interview_intel.py validate \
  examples/research-us-software-engineer.json
```

测试覆盖证据校验、来源去重、国家路由、社区检索记录、面经分级、题源防伪、角色差异化题库、上下文追问、难度调整、结束流程、打包和分发。

## 已知局限

- 实际信息覆盖取决于宿主 Agent 的搜索和浏览器能力。
- 登录墙、验证码和反自动化页面不在支持范围。
- 只有公开面经明确记录时，系统才会展示历史原题。
- 相似公司必须有可核验的行业、业务或岗位匹配依据。
- 本地模拟器使用确定性启发式进行追问和反馈。上层 Agent 可以提供更丰富的对话判断，同时保持相同证据与隐私规则。

贡献前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)、[CHANGELOG.md](CHANGELOG.md) 和 [研究手册](references/research-playbook.md)。

**许可证：** [MIT](LICENSE)。
