# 启智自制仿真实验 Skill

[![跨平台检查](https://github.com/jiushinagechai/qizhi-custom-sim-skill/actions/workflows/check.yml/badge.svg)](https://github.com/jiushinagechai/qizhi-custom-sim-skill/actions/workflows/check.yml)

面向 qizhi 平台开发者的教材驱动仿真开发技能包，提供 **Codex** 和 **Claude Code** 两个可独立安装的版本。适用于新建实验、修改已有实验、接入已有 HTML，以及验收和审查。

两个版本由 `common/custom-sim/` 生成，共用流程、模板和检查逻辑，只在工具入口与代理配置上不同。无需作者的个人目录、账号、教材存放位置或历史台账。工作流脚本仅使用 Python 标准库，支持 Windows、macOS、Linux；不要求 Bash。

本包需要配合你有权访问的 **qizhi 平台代码仓库**。它不是整个启智平台，也不附带教材、学生数据、模型 API 密钥或平台美术资源。新实验依赖的本地布局与桥接示例从你自己的 qizhi checkout 读取。

## 1. 准备环境

| 必需项 | 用途 |
| --- | --- |
| Python 3.10+ | 安装、台账和验收工具；无需 pip 安装依赖 |
| Git | 仓库历史、修改基线和缓存版本比较 |
| Node.js 22+（建议当前 LTS）、npm | 运行平台的浏览器探针 |
| Chrome 或 Microsoft Edge | 本地无头浏览器检查 |
| 可访问的 qizhi checkout | `django_site/`、`phet-audit/` 和平台契约 |
| Codex 或 Claude Code | 安装对应版本，使用自己的正常登录与权限 |

PDF 阅读可用现有工具；命令行提取推荐 Poppler 的 `pdftotext` / `pdftoppm`。macOS 可使用 Homebrew 安装 `poppler`，Ubuntu 可安装 `poppler-utils`，Windows 可使用本机 PDF 工具或 WSL。缺少文本提取工具不应伪造教材内容。

在 qizhi 的 `phet-audit` 目录安装浏览器依赖：有锁文件用 `npm ci`，没有锁文件用 `npm install`。`puppeteer-core` 不下载浏览器；先安装 Chrome/Edge。自定义浏览器位置使用 `QIZHI_BROWSER`。

```bash
# macOS / Linux 示例，按本机实际位置填写
export QIZHI_BROWSER="/path/to/chrome"
```

```powershell
# Windows PowerShell 示例，按本机实际位置填写
$env:QIZHI_BROWSER = 'C:\Program Files\Google\Chrome\Application\chrome.exe'
```

独立 sim / audit / bridge 检查不需要 Django 服务或 AI API key。学生登录、真实任务卡、数据导出等端到端验收仍按 qizhi 自身 README 配置。不要为了运行 skill 创建学生账号、修改数据库或发布实验。

## 2. 安装

先把本仓库与 qizhi 仓库放在各自目录。以下命令中的 `python`，macOS/Linux 通常替换为 `python3`，Windows 可替换为 `py -3`。所有路径都可以包含空格，请加引号。

```bash
git clone https://github.com/jiushinagechai/qizhi-custom-sim-skill.git
cd qizhi-custom-sim-skill
python install.py --target codex --repo "/path/to/qizhi"
# 或：
python install.py --target claude-code --repo "/path/to/qizhi"
# 两个都装：
python install.py --target both --repo "/path/to/qizhi"
```

安装结果：

| 工具 | 技能位置（相对 qizhi） | 额外文件 | 显式调用 |
| --- | --- | --- | --- |
| Codex | `.agents/skills/custom-sim/` | 技能内 `agents/openai.yaml` | `$custom-sim` |
| Claude Code | `.claude/skills/custom-sim/` | `.claude/agents/sim-builder.md` | `/custom-sim` |

想对本机所有项目可用，使用 `--user` 替代 `--repo`。Codex 安装到 `~/.agents/skills/`，Claude Code 安装到 `~/.claude/skills/`。项目版与用户版选一种，避免同时维护不同版本。代理工具是可选能力，没有子代理时可由主会话完成开发，并如实标注独立审查待完成。

已有旧版本时，安装器默认拒绝覆盖。确认升级使用 `--replace`，原文件会移入对应的 `skill-backups/<时间>/`，不放在会自动发现技能的目录内。原来的个人台账也保留在备份中，不会被当作新版本已验收结果。新台账需初始化；历史文档按实际情况复用，旧测试结果不得直接复制为通过。

```bash
python install.py --target both --repo "/path/to/qizhi" --replace
```

也可以下载 GitHub Release 中对应 ZIP：把其中 `custom-sim/` 放到上表技能目录；Claude Code 的 `agents/sim-builder.md` 放到 `.claude/agents/`。已有内容请先移到技能扫描目录以外备份。ZIP 内是完整技能，无需回到本仓库读取公共文件。

## 3. 预设教材与第一次使用

**v1.1.0 的默认流程：预设教材 → 指定年级/单元 → 阅读实际课本 → 联网调研 → 设计与开发文档反复确认 → AI 开发 → 打开 Demo 反复打磨 → 你满意并同意接入 → 系统适配与实际平台预览。**

日常使用无需自己维护配置或运行脚本。第一次可以直接告诉 AI：

```text
使用 custom-sim。我的教材目录是……，课程标准 PDF 是……。
请先核对文件的版本、年级和上下册，保存本机教材映射，以后按年级和单元查找。
```

两个工具共用启智仓库根目录的 `.qizhi-sim.local.json`，不放在技能目录里，升级不会丢失。
工具自动加入本机 Git 排除规则，绝对路径和教材不上传。文件已被 Git 跟踪时会拒绝写入个人路径。
如果配置了多个版本或没指定上下册，会列出候选；一个单元有多个实验时，先定位目录和活动，再确认本次做哪一个。

也可手动配置（`/path/to/skill` 指已安装的 `custom-sim` 文件夹）：

```bash
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" textbooks configure --directory "/path/to/textbooks" --curriculum "课程标准.pdf"
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" textbooks list
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" textbooks add --id science-5a --grade 5 --semester 上 --publisher "已核对的出版社" --edition "已核对的版本" --file "五年级上册.pdf"
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" textbooks find --grade 5 --semester 上
```

`configure` 可以只设置目录或课标。相对 PDF 路径按教材目录解析；也可使用绝对路径。
`list` 列出目录内 PDF 和已有映射；`find` 返回匹配的册别，AI 继续读取对应 PDF 的目录、单元和课时页面。
脚本只验证文件存在和扩展名，**不会自动 OCR、理解教材或联网调研**，这些由调用 skill 的 AI 使用当前环境的阅读/搜索工具完成。
更换文件位置时使用 `add --replace` 更新映射，改变根目录不会自动修改已确认的书籍路径。


在 qizhi 项目打开新会话，执行：

```text
Codex：使用 $custom-sim，根据我提供的课本资料开发一个实验。先核对教材和范围，提出设计方案。
Claude Code：/custom-sim 根据我提供的课本资料开发一个实验，先完成设计。
```

可以直接说明现有实验和任务：

```text
使用 custom-sim 修复这个实验在平板上拖动无效的问题。保留当前教学设计，只做相关修复和验证。
使用 custom-sim 把这份已经确认的 HTML Demo 接入当前启智仓库。
```

首次检查环境（下例为 Codex；Claude Code 把 `.agents` 换成 `.claude`）：

```bash
python "/path/to/qizhi/.agents/skills/custom-sim/scripts/qizhi_sim.py" --repo "/path/to/qizhi" doctor
```

工具会报告缺少的 Git、Node、npm、平台文件、Puppeteer 依赖和浏览器，不自动安装或改系统配置。无网络、无浏览器或无教材时，代理应继续能独立完成的工作，并明确说明哪些验证尚未完成。

## 4. 开发流程

**新建：定位教材与实验范围 → 联网调研 → 设计方案和开发文档 → 你提意见、反复修改 → 确认后开发 → 打开 Demo 检查、反复打磨 → 你满意并允许接入 → 实际系统适配。**

设计认可只授权开发；页面认可针对你实际看过的那一版。AI 不能把“测试通过”当成你满意。
你可以一次说“满意，可以接入”，同时完成页面认可和接入授权，已有明确授权不会重复询问。
联网不可用时会标注调研未完成，并征求是否按现有资料继续，不会假装看过线上优秀案例。

- 小修复从当前代码和测试进入，不重新做整套课本调研。
- 涉及科学模型、学习目标、变量的修改，更新相关设计依据。
- 用户确认过的决定与授权持续有效，不重复询问固定口令。
- 用户亲自编辑期间不覆盖文件，交回后重新读取。
- 实现问题回开发；设计问题先更新设计；验收不靠降低阈值通过。

每个实验的共享资料放在 qizhi 的 `docs/custom-sims/<slug>/`：

```text
01-lesson-research.md   教材页码、图示核验、来源和调研结论
02-design.md           目标、变量、交互、模型边界和设计决定
03-acceptance.md       可判定标准、探针 ID、每轮页面反馈和验收证据
04-development.md      功能清单、控件布局、状态变化、模型规则、开发步骤和测试映射
manifest.json          相对路径、基线提交、当前机器和人工结果
```

初始化示例（在任意目录运行）：

```bash
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" init example-sim --owner "你的名字" --file "django_site/static/phet-sims/扩展-示例实验example-sim.html"
```

`/path/to/skill` 是已安装的 `custom-sim` 目录。初始化不会写 sim，也不会覆盖已有台账。默认把当时的 `HEAD` 固定成基线；如果修改已经提交，用 `--base <修改前提交>`。已有实验开启新一轮工作时，明确更新 `base_ref` 为改动前的完整提交 SHA，并在验收文档记录原因。不能把基线移到修改之后来规避缓存检查。

将 `assets/probe.cjs` 复制到台账所指的 `phet-audit/probe-<slug>.cjs`，实现真实交互断言。在验收清单写 `[probe:A1]`，探针用 `check('A1', 实际条件, 证据)`。模板故意保持未实现状态会失败，不能直接拿空模板宣称验收通过。

```bash
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" gate example-sim --phase demo
# 完成真实注册和桥接后：
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" gate example-sim --phase integration
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" status
```

每条验收子进程默认最多 420 秒，可用 `--timeout` 调整。Gate 始终写回结果，不需要容易漏掉的 `--write`。日志、探针 JSON 和截图写入 `phet-audit/out/skill/<slug>/`，沿用平台的输出忽略规则。

### 每轮 Demo 都交付可操作页面

AI 会先检查页面，再打开/给出预览链接、当前版本、本轮改动和建议检查的操作。
你提出意见后，它会修改页面、同步受影响文档、运行相关验证、刷新预览，直到你满意。
反馈记在同一份验收文档中，不会因为两轮普通修改就停止打磨。

```bash
# 查看可直接打开的 HTML 路径和文件 URL
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" preview example-sim
# 启动本机 HTTP 预览；终端保持运行，Ctrl+C 结束
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" preview example-sim --serve
```

预览默认选择空闲端口，仅绑定 `127.0.0.1`，只服务实验静态目录，禁用目录列表和缓存。
v1.1.1 移除了启动时不必要的反向 DNS 查询，避免离线或受限网络环境等待主机名解析。
在托管终端中运行时，AI 应保留会话供你检查，修改后刷新即可；截图只作辅助。
远程主机的 localhost 不是你电脑的 localhost，需要使用宿主支持的转发/预览功能或直接交付 HTML。

接入后还要打开**真实启智页面**检查 iframe 尺寸、触控/滚动、重置、问一问和学生模式任务规则。
没有本地 Django 或账号时，会明确标注“桥接通过，实际平台适配待验证”；不会把独立 HTML 测试当成系统适配完成。

如实登记人工证据或撤销过期结论：

```bash
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" mark example-sim tablet --result pass --by "测试人" --evidence "iPad 横屏，拖动/重置完成；证据见验收文档"
python "/path/to/skill/scripts/qizhi_sim.py" --repo "/path/to/qizhi" mark example-sim tablet --result pending --by "测试人" --evidence "修改拖动后需要复测"
```

人工项支持 `design/demo/integration/platform/review/tablet/taskcard/csv/playtest/commit`；结果支持 `pass/fail/pending/not_applicable`。修改源码、相关平台文件、验收文档或检查脚本后，旧结果显示 `STALE`，需要复验。`phase` 表示工作阶段，由开发者维护；机器结果里的 phase 表示实际运行过的验收模式。机器全绿不等于用户已确认、真机已通过或学生已试玩。设计与 Demo 认可会额外记录对应文件的哈希；已有认可保留为历史证据，机器或设备检查过期显示 STALE；已有设计、Demo、接入及提交决定保留原状态，相关内容改变时另提示复核范围。无关平台注册修改不会让你重新认可整个设计。

v1.0 台账仍可运行；新建实验自动增加开发文档，旧实验进行实质性重设计时补充 `04-development.md` 并在 manifest 中加入相对路径 `development`，无需覆盖原记录。

## 5. 修复了哪些旧问题

| 旧问题 | 当前处理 |
| --- | --- |
| Demo 未接平台却必须查平台契约 | Demo 与 integration 明确分开，平台项显示 N/A |
| 审计失败但输出没命中关键词就通过 | 同时检查退出码和目标实验明确成功结果 |
| `views.py` 随便改一行就算更新缓存 | 解析实际 per-sim 版本，与基线的内容和版本比较 |
| 注释里出现 slug 就算注册 | Python AST 读取真实字典；Node 检查元素字典和实际 Set |
| 脚本失败而台账仍是全绿 | 每次记录本次总体状态，输入变化标记 STALE |
| PASS 日志代替真实覆盖 | 本次 JSON 断言 ID 对照验收列表；审查者还需检查断言含义 |
| 审查只有日志、源码只能读 ±20 行 | 给予需求、模型依据、探针源码和截图，允许读完整调用链 |
| 使用个人目录、Shell 和历史台账 | 显式 repo 路径、Python CLI、相对资料路径，不携带个人记录 |

取消“最后 4 KB 出现 marker 就证明初始化成功”的伪验证，改为审查初始化顺序并结合真实 boot/snapshot/bridge 验证。临床传播、侵蚀速率等经验按适用模型引用，不再作为所有实验的强制规则。

## 6. 验证与维护

```bash
python -m unittest discover -s tests -v
python build.py
python build.py --check
```

维护时编辑 `common/` 和 `adapters/`，运行 build 同步 `editions/`，再提交。CI 在 Windows、macOS、Linux 上运行标准库回归测试和构建一致性检查。ZIP 输出到被忽略的 `dist/`，发布时附到 Release。

回归测试使用隔离的临时 Git 仓库和可控的探针/桥接脚本，覆盖误报通过、缓存、台账过期、教材配置与歧义、预览 HTTP 与刷新、阶段认可记录、安装备份和构建一致性。它们验证工具的判断，不替代真实实验的浏览器、教学和学生验收。目标 qizhi 分支改变配置结构时，适配器会明确失败；更新适配器与测试，不应放宽条件绕过。

本包支持检查的基准是 qizhi 当前的 `PHET_SIMS`、`PHET_SIM_PROMPTS`、`get_phet_sims()`、`QIZHI_PHET_ELEMENTS` 和 `CUSTOM_SIMS` 布局。所用示例路径可在本机自由选择，平台结构本身需要存在。本技能包采用 [MIT License](LICENSE)；第三方依赖和平台代码沿用各自许可，教材、原平台资源均未随包分发。

技能发现机制参考：[Codex Skills](https://developers.openai.com/codex/skills)、[Claude Code Skills](https://code.claude.com/docs/en/skills)。
