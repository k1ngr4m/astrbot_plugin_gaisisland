CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL, -- 聊天平台唯一 id (e.g. telegram user id)
    platform TEXT,
    group_id TEXT, -- 聊天群 id
    nickname TEXT,
    created_at INTEGER NOT NULL,
    updated_at INTEGER NOT NULL,
    UNIQUE(user_id, group_id)
);

-- 群/农场（群聊对应一个 farm）
CREATE TABLE IF NOT EXISTS farms (
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
CREATE TABLE IF NOT EXISTS farm_members (
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

-- 单块地（plot）
CREATE TABLE IF NOT EXISTS plots (
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
CREATE TABLE IF NOT EXISTS crop_templates (
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
CREATE TABLE IF NOT EXISTS crop_instances (
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

-- 玩家对某作物的等级（建议）
CREATE TABLE IF NOT EXISTS player_crop_levels (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_member_id INTEGER REFERENCES farm_members(id) ON DELETE CASCADE,
  crop_template_id INTEGER REFERENCES crop_templates(id),
  level INTEGER DEFAULT 1,
  exp INTEGER DEFAULT 0,
  UNIQUE(farm_member_id, crop_template_id)
);

-- 资源库存（通用）
CREATE TABLE IF NOT EXISTS inventories (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_member_id INTEGER REFERENCES farm_members(id),
  resource_key TEXT, -- 'vegetable', 'jam', 'milk'
  amount INTEGER DEFAULT 0,
  UNIQUE(farm_member_id, resource_key)
);

-- 建筑（例如 果酱站、乳品厂、洒水器）
CREATE TABLE IF NOT EXISTS buildings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id),
  type TEXT, -- 'jam_press','dairy','sprinkler'
  level INTEGER DEFAULT 1,
  position TEXT, -- 可选坐标/slot
  created_at INTEGER, updated_at INTEGER
);

-- 加工任务（加工队列）
CREATE TABLE IF NOT EXISTS processing_jobs (
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

-- 季节/天气事件
CREATE TABLE IF NOT EXISTS season_events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  farm_id INTEGER REFERENCES farms(id),
  season INTEGER, -- 0..3
  event_type TEXT, -- 'rain','frost','none'
  triggered_at INTEGER
);

-- 任务表
CREATE TABLE IF NOT EXISTS tasks (
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

CREATE TABLE IF NOT EXISTS player_task_progress (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  task_id INTEGER REFERENCES tasks(id),
  farm_member_id INTEGER REFERENCES farm_members(id),
  progress INTEGER DEFAULT 0,
  completed BOOLEAN DEFAULT 0,
  completed_at INTEGER
);

-- 扩地成本表（示例）
CREATE TABLE IF NOT EXISTS expansion_costs (
  level INTEGER PRIMARY KEY, -- 新增到 level (plots total)
  gems_cost INTEGER NOT NULL
);

-- 示例数据:
-- level 2 -> cost 5 gems; 3->10; 4->20; 5->40 ...
INSERT OR IGNORE INTO expansion_costs(level, gems_cost) VALUES
(2,5),(3,10),(4,20),(5,40),(6,80);
