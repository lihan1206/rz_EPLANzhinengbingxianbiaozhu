# EPLAN智能并线标注系统

## 🛠 技术栈
- Frontend: React + TypeScript + Vite + Ant Design + ECharts
- Backend: FastAPI + SQLAlchemy + JWT
- Database: MySQL 8.0

## 🚀 启动指南 (How to Run)
1. 确保 Docker Desktop 已启动。
2. 在根目录执行：`docker compose up --build`
3. 等待容器启动完成。

## 🔗 服务地址 (Services)
- Frontend: http://localhost:13217
- Backend Swagger: http://localhost:18217/docs
- Database: localhost:13317 (user: eplan / pass: eplan123456)

## 🧪 测试账号
- 管理员: admin / admin123
- 工程师: engineer / engineer123

## ✨ 功能清单
- EPLAN 导出文件导入（CSV/XML）
- 并线智能识别（拓扑归并、规则阈值）
- 自动标注生成（支持模板）
- 并线可视化统计（分布图、占比图）
- 项目版本化导入记录
- 用户登录与角色权限
- 操作日志追踪
- 数据导出（CSV）
