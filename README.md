# OneLiner

## 启动

### 后端

```bash
cd backend
./start-dev
```

### 数据库

```bash
cd backend

createdb -U postgres oneliner                    # 创建数据库
rm -rf migrations/models                         # 清除旧迁移（首次初始化需要）
.venv/bin/aerich init-db                         # 首次初始化（建表）

.venv/bin/aerich migrate --name describe_change  # 根据模型变更生成迁移文件
.venv/bin/aerich upgrade                         # 执行迁移
.venv/bin/aerich downgrade                       # 回滚上一次
.venv/bin/aerich history                         # 查看历史

dropdb -U postgres oneliner                      # 删除数据库（重来）
```

### 小程序

```bash
cd miniprogram
npm run build                  # 构建到 dist/
npm run dev                    # 开发模式（watch）
```

构建后用微信开发者工具导入 `miniprogram/dist/`。
