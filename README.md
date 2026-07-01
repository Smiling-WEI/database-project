# 航空订票管理系统

本项目是一个基于 Vue + Flask + MySQL 的航空订票管理系统，包含乘客客户端和航空公司管理端两部分。系统支持航班查询、购票、订单管理、值机选座、退票、改签、航班异常处理、舱位票价管理、管理员权限管理等功能。

## 一、项目简介

本系统面向航空订票业务场景，主要实现乘客端购票流程与管理端航司后台管理流程。

乘客端主要用于完成航班查询、购票、订单查看、值机选座、退票申请、改签申请、个人信息维护等操作。

管理端主要用于航空公司管理员维护航班、舱位票价、退改签规则、订单处理、航班异常发布、用户管理和管理员管理等操作。

## 二、技术栈

### 前端

- Vue 3
- Vite
- Element Plus
- Axios
- Vue Router

### 后端

- Python
- Flask
- Flask-CORS
- PyMySQL
- PyJWT
- python-dotenv
- cryptography

### 数据库

- MySQL 8.0

## 三、项目结构

```text
database-project-main
├── backend
│   ├── app.py
│   ├── db.py
│   ├── routes
│   │   ├── auth.py
│   │   ├── flight.py
│   │   ├── passenger.py
│   │   ├── order.py
│   │   ├── change.py
│   │   ├── admin_flight.py
│   │   ├── admin_order.py
│   │   ├── admin_pricing.py
│   │   ├── admin_rule.py
│   │   └── flight_notice.py
│   ├── services
│   ├── utils
│   └── requirements.txt
│
├── src
│   ├── api
│   ├── components
│   ├── router
│   ├── utils
│   └── views
│       ├── client
│       └── admin
│
├── airline_db.sql
├── airline_db_improved.sql
├── 测试数据.sql
├── package.json
└── README.md
```

## 四、数据库初始化

推荐优先使用：

```text
airline_db_improved.sql
测试数据.sql
```

其中：

- `airline_db_improved.sql`：最终数据库结构脚本
- `测试数据.sql`：系统测试所需的基础数据
- `airline_db.sql`：早期基础版本，可作为备用参考

### 初始化步骤

1. 打开 MySQL。
2. 创建数据库：

```sql
CREATE DATABASE airline_database_improved DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
```

3. 进入数据库：

```sql
USE airline_database_improved;
```

4. 导入数据库结构：

```sql
SOURCE airline_db_improved.sql;
```

5. 导入测试数据：

```sql
SOURCE 测试数据.sql;
```

## 五、后端运行说明

进入后端目录：

```bash
cd backend
```

创建虚拟环境：

```bash
python -m venv venv
```

激活虚拟环境：

```bash
venv\Scripts\activate
```

安装依赖：

```bash
pip install -r requirements.txt
```

如果没有 requirements.txt，可以手动安装：

```bash
pip install Flask Flask-CORS PyMySQL PyJWT python-dotenv cryptography
```

在 `backend` 目录下创建 `.env` 文件：

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的MySQL密码
DB_NAME=airline_database_improved
JWT_SECRET_KEY=airline-ticket-system-secret
```

启动后端服务：

```bash
python app.py
```

后端默认运行地址：

```text
http://127.0.0.1:5000
```

## 六、前端运行说明

在项目根目录安装依赖：

```bash
npm install
```

启动前端开发服务：

```bash
npm run dev
```

前端默认访问地址：

```text
http://localhost:5173/
```

打包检查：

```bash
npm run build
```

## 七、测试账号

### 乘客账号

```text
用户名：passenger_zhang
密码：123456
```

### 系统总管理员

```text
用户名：system_admin
密码：123456
```

### 航司主管理员

```text
用户名：air_ca_admin
密码：123456
```

```text
用户名：air_mu_admin
密码：123456
```

不同管理员账号对应不同权限范围，可用于测试管理端权限控制。

## 八、主要功能

## 1. 乘客客户端功能

### 1.1 用户注册与登录

乘客可以注册账号并登录系统。登录后可以进入客户端首页进行航班查询、购票和订单管理。

### 1.2 航班查询

乘客可以根据：

- 出发城市
- 到达城市
- 出发日期

查询符合条件的航班。

查询结果会展示：

- 航班号
- 航空公司
- 出发机场
- 到达机场
- 起飞时间
- 到达时间
- 舱位信息
- 各舱位票价

### 1.3 多舱位购票

同一航班支持展示不同舱位价格，例如：

- 经济舱
- 头等舱

乘客可以选择对应舱位进行购票。

### 1.4 订单管理

乘客可以在“我的订单”中查看自己的订单，包括：

- 订单号
- 航班信息
- 乘机人信息
- 舱位信息
- 票价
- 订单状态

### 1.5 值机选座

乘客可以在满足值机时间要求后进行值机操作。

系统支持座位图式选座，乘客可以选择可用座位完成值机。

### 1.6 退票申请

乘客可以对符合条件的订单发起退票申请。

系统会根据当前退票规则计算：

- 退票手续费
- 实际退款金额

### 1.7 改签申请

乘客可以对符合条件的订单发起改签申请。

系统会根据当前改签规则计算：

- 原票价
- 新票价
- 票价差额
- 改签手续费
- 应补金额
- 应退金额

### 1.8 退改记录查看

乘客可以查看自己的退票记录和改签记录，方便追踪历史处理情况。

### 1.9 个人中心

乘客可以维护个人信息，包括：

- 手机号
- 邮箱
- 登录密码

### 1.10 常用乘机人管理

乘客可以新增、修改、删除常用乘机人信息，购票时可直接选择乘机人。

## 2. 管理端功能

### 2.1 管理员登录

管理端面向航空公司管理员和系统管理员开放，不同管理员根据岗位拥有不同操作权限。

### 2.2 控制台

管理端首页展示系统概况，方便管理员快速进入各业务模块。

### 2.3 航班管理

管理员可以查看航班列表，并进行航班维护。

支持：

- 新增航班
- 编辑航班
- 查看航班详情
- 配置航班日期
- 配置起飞时间和到达时间
- 配置执飞机型
- 配置头等舱和经济舱座位数量
- 配置初始票价

### 2.4 舱位票价管理

管理员可以维护航班对应舱位票价。

支持：

- 查看各航班舱位价格
- 新增舱位价格
- 修改舱位价格
- 查看剩余座位数量

### 2.5 退改签规则管理

管理员可以维护本航司的退票和改签规则。

规则可包括：

- 起飞前时间范围
- 手续费比例
- 是否收取正差价
- 是否退还负差价
- 规则启用状态

### 2.6 订单管理

管理员可以查看订单列表，并支持按照条件筛选订单。

支持：

- 按订单号查询
- 按航班号查询
- 按手机号查询
- 查看订单详情
- 查看订单状态

### 2.7 后台代办退票

订单管理员或主管理员可以帮助乘客处理退票。

系统会自动计算：

- 原票价
- 退票手续费
- 应退金额

### 2.8 后台代办改签

订单管理员或主管理员可以帮助乘客处理改签。

系统会自动计算：

- 原票价
- 新票价
- 票价差额
- 改签手续费
- 应补金额
- 应退金额

### 2.9 退票记录管理

管理员可以查看本航司相关退票记录。

### 2.10 改签记录管理

管理员可以查看本航司相关改签记录。

### 2.11 航班异常管理

管理员可以对航班发布异常信息，例如：

- 航班取消
- 航班调整
- 航班延误

异常发布后，系统会影响乘客端购票、退票和改签逻辑。

### 2.12 用户管理

航司主管理员和系统总管理员可以查看和维护用户信息。

### 2.13 管理员管理

航司主管理员和系统总管理员可以管理后台管理员账号。

### 2.14 管理员个人信息

管理员可以查看和修改自己的联系方式、密码等信息。

## 九、管理员权限说明

系统根据管理员岗位区分权限。

### 1. 系统总管理员

系统总管理员拥有最高权限，可以跨航司管理全部数据。

可操作：

- 所有航司航班
- 所有航司订单
- 所有舱位票价
- 所有退改签规则
- 所有用户
- 所有管理员
- 跨航司协调相关功能

### 2. 航司主管理员

航司主管理员拥有本航司全部管理权限。

可操作：

- 本航司航班管理
- 本航司舱位票价管理
- 本航司订单处理
- 本航司退改签规则管理
- 本航司用户管理
- 本航司管理员管理
- 本航司航班异常处理

### 3. 航班管理员

航班管理员主要负责航班相关操作。

可操作：

- 新增航班
- 编辑航班
- 修改舱位票价
- 发布航班异常
- 解除航班异常

不可操作：

- 后台代办退票
- 后台代办改签
- 用户管理
- 管理员管理
- 退改签规则管理

### 4. 订单管理员

订单管理员主要负责订单相关操作。

可操作：

- 查看订单
- 按手机号查询订单
- 后台代办退票
- 后台代办改签
- 查看退票记录
- 查看改签记录

不可操作：

- 新增航班
- 编辑航班
- 修改舱位票价
- 发布航班异常
- 用户管理
- 管理员管理
- 退改签规则管理

## 十、核心业务流程

### 1. 乘客购票流程

```text
乘客登录
→ 查询航班
→ 选择航班和舱位
→ 选择乘机人
→ 确认订单
→ 生成购票记录
```

### 2. 乘客值机流程

```text
进入我的订单
→ 选择可值机订单
→ 打开座位图
→ 选择座位
→ 确认值机
```

### 3. 乘客退票流程

```text
进入我的订单
→ 选择订单
→ 申请退票
→ 系统计算手续费和退款金额
→ 确认退票
→ 生成退票记录
```

### 4. 乘客改签流程

```text
进入我的订单
→ 选择订单
→ 申请改签
→ 选择目标航班和目标舱位
→ 系统计算差价和手续费
→ 确认改签
→ 原订单归档
→ 生成新订单
→ 生成改签记录
```

### 5. 管理端新增航班流程

```text
管理员登录
→ 航班管理
→ 新增航班
→ 填写航班号、日期、航线、时间、机型、座位数和票价
→ 保存
→ 生成航班实例和舱位票价
```

### 6. 管理端代办退票流程

```text
管理员登录
→ 订单管理
→ 查找订单
→ 后台退票
→ 系统计算退款金额
→ 确认处理
→ 原订单归档
→ 生成退票记录
```

### 7. 管理端代办改签流程

```text
管理员登录
→ 订单管理
→ 查找订单
→ 后台改签
→ 选择目标航班和目标舱位
→ 系统计算应补或应退金额
→ 确认处理
→ 原订单归档
→ 生成新订单
→ 生成改签记录
```

## 十一、常用接口概览

### 乘客端接口

```text
POST /api/register
POST /api/login
GET  /api/user/profile
PUT  /api/user/profile
GET  /api/flights/search
GET  /api/flights/:instance_id/cabins
POST /api/orders
GET  /api/orders
GET  /api/orders/:order_id
POST /api/orders/:order_id/refund-preview
POST /api/orders/:order_id/refund
POST /api/orders/:order_id/change-preview
POST /api/orders/:order_id/change
```

### 管理端接口

```text
POST /api/admin/login
GET  /api/admin/flights
POST /api/admin/flights
GET  /api/admin/flights/:instance_id
PUT  /api/admin/flights/:instance_id
GET  /api/admin/routes
GET  /api/admin/orders
GET  /api/admin/refund-records
GET  /api/admin/change-records
POST /api/admin/orders/:order_id/refund-preview
POST /api/admin/orders/:order_id/refund
POST /api/admin/orders/:order_id/change-preview
POST /api/admin/orders/:order_id/change
GET  /api/admin/pricing
POST /api/admin/pricing
PUT  /api/admin/pricing/:pricing_id
GET  /api/admin/rules
POST /api/admin/rules
PUT  /api/admin/rules/:rule_id
```

## 十二、运行检查

### 前端构建检查

```bash
npm run build
```

如果只出现 chunk 体积较大或第三方依赖注释提示，一般不影响运行。

### 后端语法检查

```bash
backend\venv\Scripts\python.exe -m compileall -q backend
```

无输出表示后端 Python 文件语法检查通过。

## 十三、注意事项

1. 启动前端开发环境应使用：

```bash
npm run dev
```

2. `npm run build` 只用于打包检查，不会自动更新当前浏览器开发页面。

3. 修改后端代码后需要重启后端服务。

4. 修改前端代码后建议重启前端开发服务，并在浏览器中使用 `Ctrl + F5` 强制刷新。

5. 数据库连接信息需要写在 `backend/.env` 文件中。

6. 推荐使用 `airline_db_improved.sql` 作为最终数据库结构脚本。

## 十四、项目说明

本项目为数据库课程设计项目，重点围绕航空订票业务进行数据库建模、前后端接口设计、业务流程实现和管理端权限控制。

系统覆盖了从乘客查询购票到航司后台管理的完整业务链路，并对退票、改签、航班异常、舱位票价和管理员岗位权限进行了较完整的实现。
