# Interview Intel v0.1.0-beta.1

[English](README.md)

Interview Intel 是一个可安装的 Agent Skill，用于跨语言检索公开的公司、岗位、员工评价、面试流程和面试官职业资料，并生成带原始链接和可信度分级的中文面试情报报告。

它优先复用 Agent 已具备的搜索和浏览器能力，不依赖付费 API，也不要求搭建爬虫。本地 Python 工具负责输入规范化、国家数据源路由、英文优先的多语言查询生成、来源去重、证据校验和中文报告渲染。

## 能做什么

- 根据公司名称、岗位、国家和城市选择候选招聘平台、评价社区和职业社交来源。
- 自动生成英文优先的查询，再补充国家或地区的主要语言查询。
- 核验公司实体，并明确记录同名企业风险。
- 聚合岗位 JD、技术面试流程、薪酬观察、员工评价和近期人员调整。
- 研究用户提供的 HR 或面试官公开主页，并用多个兼容属性确认身份。
- 将事实、本人公开表述、第三方评价、分析推断、面试预测和信息缺口分开标注。
- 对重复 URL、来源转载和同一来源血缘进行合并，避免夸大证据独立性。
- 在无网络、验证码或登录限制时保留失败记录，不生成虚构结果。
- 输出固定六段结构中中文报告，并提供十个带预测依据的模拟问题。

## 目录

```text
interview-intel/
├── SKILL.md
├── README.md
├── README.zh-CN.md
├── LICENSE
├── CHANGELOG.md
├── CONTRIBUTING.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── country-profiles.json
│   ├── source-catalog.json
│   ├── input-schema.md
│   ├── evidence-schema.md
│   ├── report-spec.md
│   ├── research-playbook.md
│   └── source-routing.md
├── scripts/
│   ├── intel_core.py
│   └── interview_intel.py
├── tests/
│   └── test_interview_intel.py
├── .github/
│   └── workflows/
│       └── test.yml
└── examples/
    ├── input-us-software-engineer.json
    ├── input-jp-product-manager.json
    ├── input-cn-product-operations.json
    ├── input-ambiguous-company.json
    ├── research-us-software-engineer.json
    └── report-us-software-engineer.md
```

## 安装

要求 Python 3.10 或更高版本。运行时没有第三方 Python 依赖。

```bash
git clone https://github.com/gaochenyang666-droid/interview-intel.git
mkdir -p ~/.codex/skills
cp -R interview-intel ~/.codex/skills/interview-intel
```

重新打开一个 Agent 会话后，Skill 应出现在可用技能列表中。也可以显式调用：

```text
使用 $interview-intel，研究 Microsoft 的 Software Engineer II 岗位。
公司：Microsoft
国家：美国
城市：Redmond
岗位链接：https://apply.careers.microsoft.com/careers?query=Software+Engineer+II&start=0&location=Redmond%2C+Washington%2C+United+States&pid=1970393556999242&sort_by=timestamp
背景：有分布式系统、C#、Azure 和测试经验。
重点：技术面试、系统设计、团队文化。
```

Skill 会自动调用当前 Agent 的搜索或浏览器工具。安装 Skill 本身不会打开网络访问。

## 四步使用流程

### 1. 准备输入

最小输入只有公司和岗位：

```json
{
  "company": {"name": "Example Corp"},
  "role": {"title": "Product Manager"}
}
```

完整字段见 [references/input-schema.md](references/input-schema.md)。

### 2. 生成检索计划

```bash
cd interview-intel
python3 scripts/interview_intel.py plan \
  examples/input-us-software-engineer.json \
  --format json \
  --network-status available \
  --output /tmp/interview-intel-plan.json
```

查看可读计划和数据源路由：

```bash
python3 scripts/interview_intel.py plan \
  examples/input-jp-product-manager.json \
  --format markdown
```

### 3. 执行公开来源研究

Agent 按计划打开官方页面、招聘页面、员工评价、薪酬页面和公开职业主页。搜索摘要只用于发现候选页面，不能直接作为已核实证据。

创建研究文件骨架：

```bash
python3 scripts/interview_intel.py scaffold \
  examples/input-us-software-engineer.json \
  --network-status available \
  --output /tmp/research.json
```

Agent 将实际打开并核对过的证据写入 `evidence`，将分类结论文写入 `findings`。字段规则见 [references/evidence-schema.md](references/evidence-schema.md)。

### 4. 校验并渲染

```bash
python3 scripts/interview_intel.py validate examples/research-us-software-engineer.json
python3 scripts/interview_intel.py render \
  examples/research-us-software-engineer.json \
  --output examples/report-us-software-engineer.md
```

渲染器会拒绝没有来源支持的事实类结论，并阻止在身份未确认时归因面试官履历。

## 命令

```bash
python3 scripts/interview_intel.py --help
python3 scripts/interview_intel.py plan REQUEST.json --format json|markdown
python3 scripts/interview_intel.py scaffold REQUEST.json --output research.json
python3 scripts/interview_intel.py validate research.json
python3 scripts/interview_intel.py render research.json --output report.md
python3 scripts/interview_intel.py catalog --country JP
python3 scripts/interview_intel.py catalog --raw
```

`plan` 和 `catalog` 只读取本地配置，不访问网站。

## 输入与输出约定

输入至少包含：

```json
{
  "company": {"name": "Company"},
  "role": {"title": "Role"}
}
```

输出报告固定包含：

1. 一页式摘要
2. 公司概况与综合评价
3. 员工及社交媒体评价
4. 岗位评价
5. HR / 面试官公开情报
6. 面试预测与准备
7. 来源与可信度

模拟问题始终带有“面试预测”标签和公开依据。报告不生成没有依据的 0 至 100 分评分。

## 证据与隐私规则

- 只使用公开搜索索引、公开页面、官方接口或用户主动提供的资料。
- 不绕过登录、验证码、付费墙、robots 限制或其他访问控制。
- 匿名员工评价与单条社交媒体爆料按低可信度处理。
- 同文转载共享 `independence_group`，只计为一个独立来源。
- 搜索摘要和不完整页面只能作为发现线索。
- 已确认的面试官身份需要两个独立公开来源和至少两个相互兼容的公开属性。同名无法区分时停止个人归因。
- 不在日志中写入候选人简历原文、私人联系方式、家庭地址或其他与求职无关的敏感信息。
- 默认不保存中间浏览内容。示例中的候选人背景是虚构测试数据。
- 检索内容会被视为不可信数据。疑似网页提示词注入会阻止报告生成，无关电子邮箱、私人电话和住址会自动脱敏。

## 数据源扩展

平台目录位于 `references/source-catalog.json`。每个条目包含真实主页、覆盖地区、用途、访问方式、是否可能要求登录和搜索域名。

国家与语言配置位于 `references/country-profiles.json`。新增平台或国家时只修改这两个 JSON 文件，无需改动主流程。扩展字段说明见 [references/source-routing.md](references/source-routing.md)。域名被出售、改版或不再代表原平台时，将来源标记为 `status: "retired"`，保留审计记录并停止路由。

## 测试

运行全部测试：

```bash
python3 -m unittest discover -s tests -v
```

测试覆盖：

- 美国大型科技企业软件工程师岗位的数据源路由；
- 日本产品经理岗位的日英双语计划；
- 中国企业产品运营岗位的本地平台路由；
- 同名或未知公司实体；
- 未提供面试官；
- 面试官同名且身份未确认；
- 多平台匿名评价冲突；
- 小型企业式信息稀疏场景；
- 无网络或检索失败；
- 无证据事实、虚假 URL、重复 URL 和可信度过高；
- 少于十个模拟问题与薪酬数值完整性。

QA 修复后还增加了以下回归覆盖：

- `ambiguous` 或 `not_found` 公司不得输出事实、评价、推断和预测；
- 网页提示词注入会被拒绝；
- 无关电子邮箱、私人电话和住址会被脱敏；
- 已确认面试官需要两个独立来源和两个兼容匹配属性；
- 低查询预算也会保留本地语言查询；
- 十个模拟问题必须标记为预测。

真实网页摘录和 QA 调查原始材料不进入公开 Git 历史。公开发布只包含 Skill、已审查示例、测试、文档和自动化配置。

## 真实端到端样例

[examples/report-us-software-engineer.md](examples/report-us-software-engineer.md) 是基于 2026 年 11 月 2 日实际公开页面生成的研究样例。采用的关键来源包括：

- Microsoft 2026 财年 SEC 10-K；
- Microsoft 官方公司与职业页面；
- Microsoft 官方技术面试说明；
- 2026 年 10 月 31 日发布的当前 Software Engineer II JD；
- Microsoft 官方自愿离职公告；
- CNBC 的交叉报道；
- Blind 的可公开访问薪酬和员工评价汇总；
- 一条明确标注为个例的 Reddit 面经。

Glassdoor、Levels.fyi 和 H1BGrader 在测试时触发验证码或访问控制，因此没有采用其搜索摘要，访问失败记录保留在报告中。

## 已知局限

- v0.1 依赖当前 Agent 的搜索能力。本地脚本不包含搜索引擎或爬虫，因此没有搜索工具时只能生成计划、校验数据或渲染已有证据。
- 平台覆盖、地区可用性和页面结构会变化。目录中的平台是候选发现源，不保证每个页面都公开可读。
- 聚合薪酬和匿名评价通常不披露完整样本，无法稳定支持团队级或精确百分位结论。
- 当前身份匹配辅助以结构化校验为主，复杂同名仍需人工结合多个公开属性判断。
- 报告中的预测问题不是泄题，不能替代真实岗位沟通。

## 下一版本建议

- 增加研究任务缓存，只保存 URL、哈希和证据元数据，支持过期提醒与增量复检。
- 加入可插拔搜索适配器，支持 Agent 自带搜索、企业搜索和合法公开 API。
- 增加评价时间序列、地区与部门筛选，并在样本量不足时自动抑制统计图。
- 增加面试官身份证据图，明确同名候选、属性冲突和确认路径。
- 增加 HTML、DOCX 与 PDF 输出，以及更细的中文来源附录。
- 增加社区反馈机制，让用户标记过时岗位、失效 URL 和误匹配。
