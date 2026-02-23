# 超市收银库存系统

基于 PyQt5 + [PyQt-Fluent-Widgets](https://github.com/zhiyiYo/PyQt-Fluent-Widgets) 的超市收银库存管理系统。

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![PyQt5](https://img.shields.io/badge/PyQt5-5.15-green)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 功能

- **收银台** — 扫码枪/手动输入条码 → 购物车 → 结账（现金/支付宝/微信）
- **商品管理** — 添加、编辑、搜索、删除商品
- **进货管理** — 扫码入库，自动更新库存和进价
- **用户管理** — 管理员/店员角色，启用/禁用账号
- **数据备份** — 每日自动备份，手动备份/恢复/导入/导出

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| `F2` | 聚焦条码输入框 |
| `F4` | 整单折扣 |
| `F12` | 结账 |
| `Delete` | 删除选中商品 |

## 快速开始

### 从发布包运行

前往 [Releases](https://github.com/zhiqing0205/pos-pyqt/releases) 下载对应平台的压缩包，解压后运行：

- **Windows**: 双击 `超市收银系统.exe`
- **macOS (Apple Silicon)**: 运行 `超市收银系统`
- **Linux**: 运行 `./超市收银系统`

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

> 首次启动自动创建数据库和默认管理员账号。

## 权限说明

| 功能 | 管理员 | 店员 |
|------|--------|------|
| 收银台 | ✓ | ✓ |
| 商品管理 | ✓ | — |
| 进货管理 | ✓ | — |
| 用户管理 | ✓ | — |
| 备份管理 | ✓ | ✓ |

## 技术栈

- Python 3.8+
- PyQt5 5.15
- PyQt-Fluent-Widgets 1.11
- SQLite

## 项目结构

```
main.py                 # 入口
app/
  common/
    config.py           # 配置
    database.py         # 数据库初始化
    signal_bus.py       # 全局信号
    auth.py             # 认证
    backup.py           # 备份
  models/
    user.py             # 用户模型
    product.py          # 商品模型
    transaction.py      # 交易模型
    stock_in.py         # 进货模型
  views/
    login_window.py     # 登录窗口
    main_window.py      # 主窗口
    sales_interface.py  # 收银页面
    product_interface.py# 商品管理
    user_interface.py   # 用户管理
    stock_in_interface.py# 进货管理
  dialogs/
    checkout_dialog.py  # 结账对话框
    discount_dialog.py  # 折扣对话框
    product_edit_dialog.py
    user_edit_dialog.py
    backup_dialog.py    # 备份管理
```

## License

MIT
