# OneLiner

## 启动

### 后端

```bash
cd backend
./start-dev
```

### 数据库迁移

```bash
cd backend
.venv/bin/aerich upgrade       # 执行迁移
.venv/bin/aerich init-db       # 首次初始化
.venv/bin/aerich migrate       # 生成迁移文件
.venv/bin/aerich downgrade     # 回滚
.venv/bin/aerich history       # 查看历史
```

### 小程序

```bash
cd miniprogram
npm run build                  # 构建到 dist/
npm run dev                    # 开发模式（watch）
```

构建后用微信开发者工具导入 `miniprogram/dist/`。
