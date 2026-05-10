# smscode-rules

`smscode-rules` 是一个独立维护的验证码识别规则仓库，面向 `XposedSmsCode`、`xinyi-relay` 及其共享运行时。

目标：
- 将易变的验证码识别规则从应用版本中解耦
- 允许按机构/产品持续补规则，而不必等待整包发版
- 为社区贡献规则提供统一格式、样例和校验入口

## 仓库结构

- `rules/`：规则文件
- `schemas/`：规则 Schema
- `tools/`：校验与索引生成脚本
- `_meta/rules-index.json`：生成后的规则索引

## 规则文件格式

每个规则文件描述一个供应商/产品的规则集，推荐一家公司或一个产品一份文件。

当前规则模型兼顾：
- **现有应用兼容字段**：`company`、`codeKeyword`、`codeRegex`
- **未来扩展字段**：`senderRegex`、`packageNameHint`、`priority`、`examples`

示例：

```json
{
  "specVersion": 1,
  "id": "cn.carrier.china-mobile-cloud-drive",
  "name": "中国移动云盘",
  "locale": "zh-CN",
  "updatedAt": "2026-05-01T00:00:00+08:00",
  "rules": [
    {
      "id": "reward-code",
      "company": "中国移动云盘",
      "codeKeyword": "领奖验证码",
      "codeRegex": "(?<=领奖验证码[:：])\\d{4,8}",
      "priority": 100,
      "examples": [
        {
          "body": "【验证密码】领奖验证码:1234，5分钟有效……【中国移动云盘】",
          "expectedCode": "1234"
        }
      ]
    }
  ]
}
```

## 设计约束

- 规则文件使用 `UTF-8` 编码，统一为 `JSON`
- 每条规则至少带 1 个可复现样例
- `codeRegex` 必须是可编译正则
- 样例短信必须能命中 `expectedCode`
- 若配置了 `company` / `codeKeyword`，样例正文必须包含对应文本

## 当前兼容策略

现阶段客户端可以直接读取下列字段映射到现有 `SmsCodeRuleSpec`：

- `company`
- `codeKeyword`
- `codeRegex`

其余字段可供后续版本扩展：

- `senderRegex`
- `packageNameHint`
- `priority`
- `notes`
- `examples`

## 工具

校验全部规则：

```bash
python3 tools/validate_rules.py
```

生成索引：

```bash
python3 tools/build_index.py
```

## 初版规则

当前已包含：
- 中国移动云盘活动领奖验证码
- 汇丰银行中国验证码

后续建议继续补充：
- 银行
- 运营商
- 电商
- 出行 / 生活服务
- 海外短信模板

