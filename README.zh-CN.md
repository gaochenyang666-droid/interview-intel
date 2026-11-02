# Interview Intel

**全球面试情报 Skill：查公司、查岗位、研究公开职业背景，带着证据准备面试。**

[English](README.md) · [简体中文](README.zh-CN.md) · [Español](README.es.md) · [Русский](README.ru.md)

[![自动测试](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml/badge.svg)](https://github.com/gaochenyang666-droid/interview-intel/actions/workflows/test.yml) · [Beta 版本](https://github.com/gaochenyang666-droid/interview-intel/releases/tag/v0.1.0-beta.1) · [MIT 许可证](LICENSE)

Interview Intel 是一个可以安装到 AI Agent 的面试研究技能。只需输入**公司名称和岗位**，Agent 就能检索企业官方资料、招聘页面、员工评价、职业社区、薪酬线索与公开面经，并根据可验证的职业资料研究指定 HR 或面试官，最终生成**带原始链接和可信度说明的中文报告**。

> **当前版本：v0.1.0-beta.1（公开测试版）。** 联网搜索由宿主 Agent 的搜索或浏览器工具完成；仓库中的 Python 脚本负责生成检索计划、校验证据、去重与渲染报告，**脚本本身不会自动抓取网页**。

## 能帮你解决什么？

| 想了解的问题 | 可获得的研究结果 |
| --- | --- |
| 这家公司值得去吗？ | 公司背景、业务与招聘动态、员工反馈、不同来源之间的分歧。 |
| 岗位实际做什么？ | 官方 JD、主要职责、技能要求、薪酬观察、地区与职级差异。 |
| 工作环境怎么样？ | 公开员工评价和社交平台讨论，注明时间、样本限制及来源可信度。 |
| 面试官可能关注什么？ | 已确认身份的公开职业履历、专业文章与明确表达的招聘标准。 |
| 应该怎么准备？ | 针对性准备清单、反问问题及 **10 道标注预测依据的模拟面试题**。 |

研究先使用**英文**查询，再使用目标国家的**本地语言**查询。候选来源包括 LinkedIn、Indeed、Glassdoor、Reddit、Blind、牛客、脉脉、OpenWork、JobPlanet、Naukri、SEEK 等。部分平台需要登录或有访问限制，列入目录不代表可以读取其全部内容。

## 两分钟安装：Codex

需要 Python 3.10 或更新版本、Git，以及具备联网搜索或浏览器能力的 Agent。核心脚本没有第三方 Python 运行时依赖，也不强制使用付费 API。

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.codex/skills
cp -R interview-intel ~/.codex/skills/interview-intel
```

重新打开 Codex 会话，然后直接输入：

```text
使用 $interview-intel，为我生成带来源的面试情报报告。
公司：字节跳动
岗位：产品运营
地点：北京，中国
岗位链接：（可选，粘贴公开 JD）
面试官：（可选，姓名、职位、公开主页）
个人背景：有用户增长和数据分析经验
重点：团队文化、加班情况、面试流程、薪资和岗位发展
```

**必填项只有公司和岗位。** 国家、城市、JD、面试轮次、面试官公开资料、个人技能背景都可以省略。提供的信息越明确，越容易避免同名企业与不同团队混淆。

其他兼容 Agent Skills 的客户端也可参考 [SKILL.md](SKILL.md) 使用，但安装路径和是否有可用搜索工具由具体客户端决定。

## 更多调用方式

**日本岗位研究：**

```text
使用 $interview-intel 研究 Toyota 在日本东京的 Product Manager 岗位。
优先核实官方招聘信息，再用日语检索 OpenWork 等本地平台。
比较岗位职责和员工评价，提供中文报告及全部实际采用的来源。
```

**指定面试官：**

```text
使用 $interview-intel 研究 [公司] 的 [岗位]。
面试官：[姓名、所在部门或职位、公开职业主页]。
先确认身份，再整理其公开职业经历、技术文章或招聘观点。
给出基于证据的准备建议，不要把预测写成面试官的确定偏好。
```

**比较矛盾评价：**

```text
使用 $interview-intel 调查 [公司] [城市] 的 [岗位]。
对比公司官方招聘信息与近期可访问的员工评价。
区分一手事实、匿名体验、推断与没有证据的部分。
```

## 最终会得到什么？

报告默认是**简体中文 Markdown**，开头提供一页式摘要，然后是六个栏目：

1. 公司概况与综合评价
2. 员工及社交媒体评价
3. 岗位评价、薪酬和风险
4. HR / 面试官公开职业情报
5. 面试预测与准备建议
6. 原始来源、可信度及信息缺口

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

## 全球覆盖与可信度

- **全球研究：** 根据国家、岗位和语言动态选择企业官网、招聘平台、职业社交媒体与本地职场社区。数据源可在 [source-catalog.json](references/source-catalog.json) 中扩展。
- **先核实，再下结论：** 搜索摘要只能帮助发现页面；验证码、登录限制及失效页面会单独记录。重复转载不会当成多份独立证据。
- **谨慎核实面试官：** 同名不等于同一人；需要多个兼容的公开属性和独立来源。职业背景不能证明对方会参加你的面试。
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
