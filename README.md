# 收银库存系统

基于 PyQt5 + [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 的收银库存管理系统。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能

- **收银台** — 扫码枪/手动输入条码，购物车管理，整单/单品折扣，忽略库存模式
- **结账** — 现金/支付宝/微信支付，自动扣减库存
- **仪表盘** — 今日/本月销售统计卡片，近7天营业额柱状图，分类销售饼图，支付方式分布，最近交易，热销商品排行，库存预警
- **商品管理** — 添加、编辑、搜索、删除商品，扫码快速添加/编辑
- **进货管理** — 扫码入库，自动更新库存和进价
- **销售记录** — 交易历史查询，双击查看详情，支持删除
- **用户管理** — 管理员/店员角色，启用/禁用/删除账号
- **支付设置** — 微信支付和支付宝接口配置
- **数据备份** — 每日自动备份，手动备份/恢复/导入/导出，退出前自动备份

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F4` | 整单折扣 |
| `F12` | 结账 |
| `Delete` | 删除选中商品/交易 |

## 快速开始

### 从发布包运行

前往 [Releases](https://github.com/zhiqing0205/pos-pyqt/releases) 下载对应平台的安装包：

| 平台 | 文件 |
|------|------|
| Windows (x64) | `pos-pyqt-windows-x64-版本号-setup.exe` 或 `-portable.zip` |
| macOS (ARM64) | `pos-pyqt-macos-arm64-版本号.dmg` |
| Linux (x64) | `pos-pyqt-linux-x64-版本号.tar.gz` |

### 从源码运行

```bash
git clone https://github.com/zhiqing0205/pos-pyqt.git
cd pos-pyqt
pip install -r requirements.txt
python main.py
```

## 默认账号

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| 张店员 | 123456 | 店员 |
| 李店员 | 123456 | 店员 |

> 首次启动自动创建数据库、默认账号和演示数据（交易、进货记录）。

## 权限说明

| 功能 | 管理员 | 店员 |
|------|:------:|:----:|
| 收银台 | ✓ | ✓ |
| 销售记录 | ✓ | ✓ |
| 仪表盘 | ✓ | — |
| 商品管理 | ✓ | — |
| 进货管理 | ✓ | — |
| 用户管理 | ✓ | — |
| 支付设置 | ✓ | — |
| 备份管理 | ✓ | — |

## 技术栈

- Python 3.8+
- PyQt5 5.15
- PyQt-Fluent-Widgets 1.11
- SQLite（WAL 模式）

## 项目结构

```
main.py                     # 入口
app/
  common/
    config.py               # 配置常量
    database.py             # 数据库初始化 + 演示数据
    signal_bus.py           # 全局信号
    auth.py                 # 认证
    backup.py               # 备份管理器
  models/
    user.py                 # 用户模型（级联删除）
    product.py              # 商品模型（级联删除）
    transaction.py          # 交易模型
    stock_in.py             # 进货模型
    settings.py             # 配置模型
    stats.py                # 统计查询
  views/
    login_window.py         # 登录窗口
    main_window.py          # 主窗口
    sales_interface.py      # 收银页面
    dashboard_interface.py  # 仪表盘
    product_interface.py    # 商品管理
    stock_in_interface.py   # 进货管理
    user_interface.py       # 用户管理
    transaction_interface.py# 销售记录
    settings_interface.py   # 支付设置
    backup_interface.py     # 备份管理
  dialogs/
    checkout_dialog.py      # 结账对话框
    discount_dialog.py      # 折扣对话框
    cart_item_dialog.py     # 购物车编辑
    product_edit_dialog.py  # 商品编辑
    user_edit_dialog.py     # 用户编辑
    stock_in_dialog.py      # 入库对话框
    transaction_detail_dialog.py  # 交易详情
docs/
  用户手册.md               # 详细使用说明
```

## 文档

详细使用说明请参阅 [用户手册](docs/用户手册.md)。

## License

MIT
