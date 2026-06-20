# Release Notes 生成规范

## 格式模板

```markdown
# api-tree vX.Y.Z

## New Features

- **Feature Name** — One sentence description of what it does and how to use it.

## Improvements

- Description of improvement.
- Description of improvement.

## Breaking Changes (如有)

- Description of breaking change and migration path.

## Supported Features Table (如有)

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| value | value | value |

## What's Changed

- type: short description by @author in #PR

**Full Changelog**: https://github.com/Abyss-PlayerEG/api-tree/compare/vOLD...vNEW
```

## 规则

### 标题

- 格式：`# api-tree vX.Y.Z`
- 版本号来自 git tag 或构建版本

### 分类

| 分类 | 何时使用 |
|------|----------|
| New Features | 全新功能，用户可感知 |
| Improvements | 已有功能的改进、性能优化、体验提升 |
| Breaking Changes | 不兼容的变更（尽量避免） |
| Bug Fixes | 修复已有问题（如有多个可单独列出） |

### 条目写法

- 每条以 `- ` 开头
- 功能名加粗：`**Feature Name**`
- 功能名后用 `—` 连接描述
- 描述说明：是什么、怎么用、有什么效果
- 用英文撰写，简洁明了

### What's Changed

- 从 `git log --oneline` 提取
- 格式：`- type: description by @author in #PR`
- type 使用：feat / fix / refactor / docs / security / build
- 按重要性排序，feat 在前

### Full Changelog

- 格式：`compare/vOLD...vNEW`
- OLD 为上一个 release tag，NEW 为当前

## 生成流程

1. 获取上一个 release tag：`git describe --tags --abbrev=0`
2. 获取当前版本号
3. 获取 commit 列表：`git log --oneline <old_tag>..HEAD`
4. 按 type 分类 commit
5. 提炼用户可感知的功能点和改进点
6. 按模板格式输出
