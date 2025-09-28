多人基于对话的休闲农场游戏 PRD + 数据库设计 + 接口与行为设计。下面给出：产品需求文档（PRD）、数据模型（DDL）、关键 DB 接口/事务示例、群聊命令/后端行为、核心算法（作物成长、经验/等级、季节轮换、扩地），以及并发/伸缩/持久化注意点与示例数据。
1 — 概要（Product Brief）
目标：在群聊中通过命令与消息互动来协作/竞争式经营农场，核心玩法：种植 → 等待生长（异步）→ 收获 → 加工/出售 → 升级农场/扩地/解锁作物/建筑。支持多人共享同一农场（群为单位）。节奏偏休闲（成长以分钟为单位），支持季节与天气（每 17 分钟切换季节），任务+成就+每日奖励。
关键货币与数值：
● 奖牌 (Medals)
● 钻石 (Gems) —— 稀缺，扩地/加速/特殊物品
● 金币 (Coins) —— 日常货币
● 资源（蔬菜/水果/奶/蜂蜜 等）
● 作物等级（1–250），作物等级决定每株收益（可用公式计算）
● 农场等级（Farm level）：解锁作物/建筑/扩地
群聊交互形式：以 slash 命令或关键字触发（/种植、/收获、/浇水、/扩张、/商店、/任务、/农场），并通过 Bot 回复简短文本/表情与进度。
2 — 核心玩法细节（规则要点）
● 作物示例：生菜、胡萝卜（你给出的参数已内置）
    ○ 生菜：成本 15 coin，生长 10m（可缩短到 5m），收获 30 coin + 1 蔬菜资源 + 1 exp
    ○ 胡萝卜：成本 35 coin，生长 20m（可缩短到 10m），收获 60 coin + 2 蔬菜资源 + 2 exp
● 作物等级 1–250：等级影响单株售卖价格与/或资源产量（后面给公式）
● 浇水 / 洒水器：缩短生长时间（部分或全部浇透）
● 每次收获：给予作物经验（用于作物本身升级）并给玩家经验（或给农场经验）——你可以把“玩家经验”与“作物经验”两条独立管理
● 季节：每 17 分钟切换（Spring, Summer, Autumn, Winter）。季节限制某些作物种植。季节切换时有小概率天气事件（例如：暴雨：浇透范围扩大 1 次；霜冻：某些作物产量暂降）
● 扩地：初始 1 块地，扩地消耗钻石。扩地成本按层级表（见下）
● 任务：无时限任务（完成得奖牌/钻石/经验），例如“收获 10 次番茄”
● 异步成长：作物在后台计时，达到收获时间后玩家（群任何成员）可触发 /harvest 来收割
● 成品加工：如牛奶→奶酪、果汁→果酱。加工需要建筑与时间，出售成品可以换奖牌
3 — PRD（功能清单）
短期 MVP（可在 2–4 周实现）：
● 群农场基础：群中第一个玩家输入注册指令时，自动创建农场。
● 种植/收获/浇水：/plant、/harvest、/water、/status
● 作物与资源：生菜、胡萝卜；资源库存与出售 /sell
● 季节系统（每 17 分钟）并在群内广播季节变更事件
● 扩地 /expand（使用钻石），基础 5 层扩地表
● 任务系统：简单任务（收获 N 次）
● 后台作物定时器（持久化触发）
后续（v2+）：
● 更多作物、建筑（果酱摊位、乳品厂、灌溉塔）
● 生产链（加工/合成）与配方
● PVP/市集/拍卖/群间互访
● 成就/排行榜/皮肤/事件（节日活动）
● 可视化小地图（网页/卡片）
4 — 数据库设计（SQL DDL，SQLite / PostgreSQL 都适用）
下面给出核心表与字段（我用 SQLite 风格，但适配 Postgres 非常容易）。
4.1 基础表
-- 玩家（全局唯一）
CREATE TABLE players (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id TEXT NOT NULL, -- 聊天平台唯一 id (e.g. telegram user id)
  username TEXT,
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL,
  UNIQUE(user_id)
);

-- 群/农场（群聊对应一个 farm）
CREATE TABLE farms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  group_id TEXT NOT NULL, -- 聊天群 id
  name TEXT,
  farm_level INTEGER DEFAULT 1,
  medals INTEGER DEFAULT 0,
  gems INTEGER DEFAULT 0,  -- 钻石
  coins INTEGER DEFAULT 0, -- 公用金币池（也可用 player 持有金币）
  season INTEGER DEFAULT 0, -- 0:spring 1:summer 2:autumn 3:winter
  last_season_change_at INTEGER DEFAULT 0,
  plots_count INTEGER DEFAULT 1, -- 总地块数（可扩展）
  created_at INTEGER,
  updated_at INTEGER,
  UNIQUE(group_id)
);

-- 玩家在某个 farm 的数据（角色与财富）
CREATE TABLE farm_members (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
  player_id INTEGER REFERENCES players(id) ON DELETE CASCADE,
  coins INTEGER DEFAULT 0,
  gems INTEGER DEFAULT 0,
  medals INTEGER DEFAULT 0,
  exp INTEGER DEFAULT 0,      -- 玩家经验
  level INTEGER DEFAULT 1,
  nickname TEXT,
  last_active_at INTEGER,
  UNIQUE(farm_id, player_id)
);

4.2 地块与作物实例
-- 单块地（plot）
CREATE TABLE plots (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id) ON DELETE CASCADE,
  slot_index INTEGER NOT NULL, -- 0..N-1
  terrain TEXT DEFAULT 'standard', -- default, watery, slope, flat
  is_owned BOOLEAN DEFAULT TRUE,
  created_at INTEGER,
  updated_at INTEGER,
  UNIQUE(farm_id, slot_index)
);

-- 作物模板（静态配置）
CREATE TABLE crop_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  key TEXT UNIQUE, -- 'lettuce', 'carrot'
  name TEXT,
  type TEXT, -- vegetable/fruit/dairy/...
  base_cost INTEGER,
  base_grow_seconds INTEGER,
  seasons_allowed TEXT, -- json array or bitmask e.g. "0,1,2,3"
  base_sell INTEGER, -- 等级1时的售卖金币
  base_resource_yield INTEGER, -- 如 1,2
  base_exp INTEGER, -- 给玩家的 exp
  unlock_farm_level INTEGER DEFAULT 1,
  description TEXT
);

-- 作物实例（某地块正在生长或成熟的实例）
CREATE TABLE crop_instances (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  plot_id INTEGER REFERENCES plots(id) ON DELETE CASCADE,
  planted_by INTEGER REFERENCES farm_members(id),
  crop_template_id INTEGER REFERENCES crop_templates(id),
  planted_at INTEGER, -- unix sec
  grow_seconds INTEGER, -- 实际所需秒（受浇水/加速/作物等级影响）
  water_level INTEGER DEFAULT 0, -- 0..100
  crop_level INTEGER DEFAULT 1, -- 1..250 (每株独立等级或全局同模板等级，选择其一)
  last_watered_at INTEGER,
  status TEXT DEFAULT 'growing', -- growing|mature|harvested
  ready_at INTEGER, -- unix sec when mature
  created_at INTEGER,
  updated_at INTEGER
);

关于**作物等级（1-250）**的实现建议：
● 可以选择两种方案，选第一种方案（全局模板等级）：
    a. 全局模板等级：同一玩家/群的某作物有统一等级（例如玩家对“生菜”的熟练度）。好处：节省空间，便于平衡；缺点：不支持每株独立成长经验。
    b. 每株等级：每个 crop_instance 有自己的 crop_level（如你描述）。比较复杂且数据量大，但更精细。MVP 建议使用“玩家对作物的熟练度表”（见 below: player_crop_levels）。
-- 玩家对某作物的等级（建议）
CREATE TABLE player_crop_levels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_member_id INTEGER REFERENCES farm_members(id) ON DELETE CASCADE,
  crop_template_id INTEGER REFERENCES crop_templates(id),
  level INTEGER DEFAULT 1,
  exp INTEGER DEFAULT 0,
  UNIQUE(farm_member_id, crop_template_id)
);

4.3 资源/背包/加工
-- 资源库存（通用）
CREATE TABLE inventories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_member_id INTEGER REFERENCES farm_members(id),
  resource_key TEXT, -- 'vegetable', 'jam', 'milk'
  amount INTEGER DEFAULT 0,
  UNIQUE(farm_member_id, resource_key)
);

-- 建筑（例如 果酱站、乳品厂、洒水器）
CREATE TABLE buildings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id),
  type TEXT, -- 'jam_press','dairy','sprinkler'
  level INTEGER DEFAULT 1,
  position TEXT, -- 可选坐标/slot
  created_at INTEGER, updated_at INTEGER
);

-- 加工任务（加工队列）
CREATE TABLE processing_jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id),
  started_by INTEGER REFERENCES farm_members(id),
  input_resource TEXT,
  input_amount INTEGER,
  output_resource TEXT,
  output_amount INTEGER,
  started_at INTEGER,
  finish_at INTEGER,
  status TEXT DEFAULT 'running' -- running|done|cancelled
);

4.4 季节/天气与任务
CREATE TABLE season_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id),
  season INTEGER, -- 0..3
  event_type TEXT, -- 'rain','frost','none'
  triggered_at INTEGER
);

-- 任务表
CREATE TABLE tasks (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id),
  title TEXT,
  description TEXT,
  reward_medals INTEGER DEFAULT 0,
  reward_gems INTEGER DEFAULT 0,
  reward_exp INTEGER DEFAULT 0,
  condition_json TEXT, -- e.g. {"type":"harvest_count","crop":"tomato","count":10}
  created_at INTEGER,
  expires_at INTEGER NULL
);

CREATE TABLE player_task_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER REFERENCES tasks(id),
  farm_member_id INTEGER REFERENCES farm_members(id),
  progress INTEGER DEFAULT 0,
  completed BOOLEAN DEFAULT 0,
  completed_at INTEGER
);

4.5 扩地成本表（示例）
CREATE TABLE expansion_costs (
  level INTEGER PRIMARY KEY, -- 新增到 level (plots total)
  gems_cost INTEGER NOT NULL
);

-- 示例数据:
-- level 2 -> cost 5 gems; 3->10; 4->20; 5->40 ...
INSERT INTO expansion_costs(level, gems_cost) VALUES
(2,5),(3,10),(4,20),(5,40),(6,80);

5 — 关键 API / DB 接口（伪代码 / SQL + 事务）
下面给出常用群聊命令对应的后端流程（以伪代码/事务为主），便于你直接实现。
注意：所有修改用户/作物/金币的操作建议在 DB 事务中完成，并对目标行加悲观锁（Postgres: SELECT ... FOR UPDATE）或使用乐观锁 version 字段，防止并发丢失。
5.1 /plant 指令 — 种植
输入： player_user_id, farm_group_id, plot_index, crop_key流程：
1. 查 farm_member、farm、plot、crop_template。
2. 检查季节允许、plot 空闲、玩家/农场是否有足够金币/解锁条件。
3. 扣金币，创建 crop_instance 行，计算 grow_seconds：
    ○ base = crop_template.base_grow_seconds
    ○ apply watering/建筑/作物等级影响
    ○ final = max( (base * seasonal_modifier * terrain_modifier) - water_bonus - building_bonus, min_seconds)
4. set ready_at = now + final事务 SQL 示例（伪）：
BEGIN;
SELECT coins FROM farm_members WHERE id=? FOR UPDATE;
-- if coins < cost -> rollback
UPDATE farm_members SET coins = coins - cost WHERE id = ?;
INSERT INTO crop_instances( plot_id, planted_by, crop_template_id, planted_at, grow_seconds, ready_at, crop_level, status)
 VALUES (..., ?, ?, now, ?, now + ?, 1, 'growing');
COMMIT;

回复群：@user 在地块 #3 种下了 生菜 ，到时可用 /harvest 收获（约 10 分钟）
5.2 /harvest 指令 — 收获
输入： player_user_id, farm_group_id, plot_index流程：
1. SELECT crop_instance WHERE plot_id & status = 'growing' OR 'mature'
2. 如果 ready_at > now：告诉用户还未成熟（显示剩余）
3. 否则：在事务中
    ○ 标记该 instance 为 harvested 或删除实例并释放地块
    ○ 计算卖价： base_sell * crop_level_multiplier(level)
    ○ 将 coins 加到触发者或 farm/owner（按你规则）
    ○ 加玩家 exp，更新 player_crop_levels exp （如果使用）
    ○ 产出资源，写入 inventories
    ○ 更新 farm/plot updated_at示例事务要点：
● use FOR UPDATE on crop_instance or plot
● 给 player_task_progress 增量，检测是否完成任务并发放奖励
5.3 /water 指令 — 浇水
行为：
● 影响 crop_instance.water_level、grow_seconds（可直接缩短 ready_at）
● 若在洒水器覆盖范围内则自动水（建筑影响）
5.4 /expand 指令 — 扩地
输入： desired_new_plot_count事务：
● SELECT expansion_costs for desired level
● 检查 farm.gems >= cost
● 扣 gems 并在 plots 表中插入新的 slot_index（或设置 plots_count 更新）
● 返回成功消息与新的总地块数
5.5 /status /farm 指令 — 查看状态
● 返回 farm 概览（coins, gems, medals, plots free/used, next season 在多少分钟）
● 简短文本 + 若支持卡片可带图片/进度条
6 — 核心算法与数值设计
6.1 作物收益与作物等级公式（示例）
让 1–250 等级对收益有“渐进式但受限”的提升：
● sell_price(level) = base_sell * (1 + 0.02 * (level - 1)^(0.6))
    ○ level 1 => base_sell
    ○ level 10 => 大约 + ~30%（示例）
● 每次收获给作物/玩家经验（可选）
● 作物升级经验表：
    ○ exp_to_next(level) = floor(50 * (1.08)^(level-1)) （逐级递增）
你可以根据偏慢/偏快节奏调整 0.02 与 1.08 的系数。
6.2 浇水 / 洒水器对生长时间影响
● 单次浇水：减少剩余时间 30%（或直接减去固定秒数）
● 完全浇透（100%）：生菜示例可将 10 分钟 → 5 分钟
● 洒水器（建筑）覆盖：自动视为完全浇透（但有冷却/容量）
6.3 季节切换与天气（每 17 分钟）
● 定时任务（服务端 cron）每 17 分钟遍历 farms：
    ○ farm.season = (farm.season + 1) % 4
    ○ 随机概率触发天气事件（例：10% rain, 5% frost, else none）
    ○ 将 event 写入 season_events 并在群内广播一句话
● 季节影响：
    ○ 限制作物是否可种（使用 crop_templates.seasons_allowed）
    ○ 在季节开始时，tree-type 静态资源刷新
7 — 并发、持久化与扩展建议
● 所有写操作（转账、种植、收获）使用 DB 事务，重要行使用 SELECT ... FOR UPDATE（Postgres）或乐观锁版本字段。
● 后台任务（season tick、处理队列、processing_jobs 完成）建议使用单独工作进程/队列（如 Celery / RQ / Sidekiq），避免 Bot 进程阻塞。
● 作物到时触发有两种实现：
    a. 延迟队列/任务：种植时创建一个延迟任务（e.g., Redis delayed job / rdb），到时自动标记 mature 并通知群；优点：及时；缺点：需要任务系统。
    b. 惰性检查：当有人查询/收获时检查 ready_at（更简单，消费计算量少），并在 season tick 时做一次批量扫描用于广播天气/季节影响。
● 数据量预估：每个群最多几百地块，crop_instances 行可能很多，建议对 crop_instances.ready_at、plots(farm_id,slot_index) 建索引。
● 备份：定期备份 DB（尤其是 production）
8 — 群聊命令速查（示例）
● /register — 注册玩家
● /farm — 显示农场总览（coins/gems/medals/plots）
● /status plot_id — 查看具体地块状态
● /plant <plot#> <crop_key> — 在地块种植
● /harvest <plot#> — 收获（或 /harvest all）
● /water <plot#> — 浇水（或 /water all）
● /expand — 扩地（显示可扩展等级与成本）
● /shop — 查看种子/建筑/加速道具
● /tasks — 列出任务
● /process start <recipe> <amount> — 发起加工
● /inventory — 查看个人资源
● /leaderboard — 农场/玩家排行
Bot 输出示例（短）：
[FarmBot] @alice 在 #3 种下了 生菜 🌱 到期：14:33 (+10m)。/harvest 收获

9 — 示例 SQL：插入 crop_template 与示例作物
INSERT INTO crop_templates (key,name,type,base_cost,base_grow_seconds,seasons_allowed,base_sell,base_resource_yield,base_exp,unlock_farm_level,description)
VALUES
('lettuce','生菜','vegetable',15,600,'0,1,2,3',30,1,1,1,'全年可种'),
('carrot','胡萝卜','vegetable',35,1200,'0,2,3',60,2,2,1,'三季作物：春秋冬');

10 — 任务示例（示例 JSON 条件）
任务条件 JSON 例子：
● {"type":"harvest_count","crop":"carrot","count":10} — 收获 10 次胡萝卜
● {"type":"sell_amount","resource":"jam","amount":5} — 卖出 5 份果酱
实现任务匹配时在收获/卖出操作的事务中更新 player_task_progress 表并检查完成。
11 — UX 与提示设计（群内简短、可读）
● 每次重要事件（扩地成功、季节变更、任务完成）在群里广播一句短消息，并可以 @ 谁 做了什么
● 避免写大量表格输出，优先用“卡片 + 文字摘要”。如果聊天平台支持图片/富文本，可生成小图示（例如进度条）
12 — 示例：种植->收获完整流程（伪代码）
def cmd_plant(user_id, group_id, plot_index, crop_key):
    with db.transaction():
        member = ensure_member(user_id, group_id)
        plot = select_plot_for_update(group_id, plot_index)
        if plot has crop -> return "该地已被占用"
        template = get_crop_template(crop_key)
        if not season_allowed(template, farm.season): return "当前季节不可种植"
        if member.coins < template.base_cost: return "金币不足"
        member.coins -= template.base_cost
        grow_seconds = compute_grow_seconds(template.base_grow_seconds, member, plot, farm)
        ready_at = now + grow_seconds
        insert crop_instances(...)
    return "种植成功，预计到期：..."

13 — 扩展与平衡建议（设计原则）
● 让钻石用于“便利/扩容/微付费路径”，不把所有强力收益绑定钻石
● 奖牌用于活动/兑换限定摊位（如只用奖牌购买的装饰）
● 作物等级成长速度不宜过快；可以让玩家专注少量作物升级（例如加速同类作物收益）以促进玩法选择性
● 季节与天气带来短期变动，增加群聊讨论点（例如“这次暴雨大家都可以受益”）
14 — 示例种子数据（快速启动）
● crop_templates: lettuce, carrot, tomato, grape, milk (以你提供为模板)
● expansion_costs: see table above
● 初始 farm coins/gems 分配：farm.gems=5, farm.coins=500; 每新玩家 farm_member.coins += 200
15 — 安全性、滥用防护
● 防止刷分/脚本：给大量自动操作施加冷却（每个 player 每分钟 N 次命令）
● 操作限制：同一 plot 同时只能有一个活跃 crop_instance
● 日志审计：记录所有资源变更（谁、何时、什么动了多少）

