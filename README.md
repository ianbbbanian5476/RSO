<p align="center">
  <strong>RSO (Restaurant Seating Optimization) 引擎</strong><br>
  <em>具時間軸之約束裝箱問題 · 線上/線下混合排程 · 多代理人強化學習</em>
</p>

---

## 目錄

1. [問題描述](#1️⃣-問題描述)
2. [學術基礎](#2️⃣-學術基礎)
3. [原型餐廳](#3️⃣-原型餐廳--原燒-台中西屯家樂福店)
4. [座位拓樸與約束](#4️⃣-座位拓樸與約束)
5. [數學模型](#5️⃣-數學模型-ilp--csp)
6. [系統架構](#6️⃣-系統架構)
7. [研究路線圖](#7️⃣-研究路線圖)
8. [快速開始](#8️⃣-快速開始)
9. [參考文獻](#9️⃣-參考文獻)

---

## 1️⃣ 問題描述

### 領域定位

全服務餐廳在**物理空間、時間軸、人力資源**三重約束下的座位分配問題，屬於高維度 NP-Hard 組合最佳化問題。

### 為什麼困難

傳統餐廳管理將帶位視為**先到先服務（FCFS）**的排隊問題。實際上，這是三個軸向的並行最佳化：

| 軸向 | 問題本質 | 計算複雜度類別 |
|---|---|---|
| **空間** | 桌子可合併、拆分或固定；容量不可簡單加總 | 約束裝箱問題（CBPP） |
| **時間** | 每組客人占用 120 分鐘；未來預約與當前現場客競爭同一桌位 | 線上/線下混合排程 |
| **人力** | 服務生有最大管理桌數上限，跨區服務有移動成本 | 車輛路線問題（VRP）變體 |

三個軸向彼此**耦合**：t=0 時的空間決策（例如將連通桌對 2-4/2-5 拆分給一組 2 人現場客），會鎖死配置並對 t=30 分鐘的 8 人預約客（需要合併使用該桌對）產生**機會成本**。

### 核心研究問題

> 面對隨機抵達的現場客人與已知的未來預約，如何在即時帶位決策中**最大化 RevPASH**（每可用座位小時營收），同時滿足實體拓樸、服務生容量與顧客體驗約束？

---

## 2️⃣ 學術基礎

### 2.1 Kimes（1999）— 餐廳營收管理（RRM）

Sheryl E. Kimes（康乃爾大學）於 Cornell Hospitality Quarterly 發表了 RRM 的開創性理論框架 [1]。核心貢獻：

- **RevPASH** 作為核心 KPI：
  \[
  \text{RevPASH} = \frac{\text{總營收}}{\text{可用座位數} \times \text{小時數}}
  \]

- **RRM 五步驟框架**：
  1. 建立基準線（量測當前 RevPASH）
  2. 理解驅動因子（客群規模分佈、用餐時長、到店模式）
  3. 制定策略（時長控制、需求轉移）
  4. 執行策略（員工訓練、系統部署）
  5. 監控成果（RevPASH 變異分析）

- **時長控制（Duration Control）**：核心槓桿——管理用餐時長之於餐廳，如同航空公司收益管理中停留天數控制之於機票。

### 2.2 Thompson（2002, 2003）— 桌位組合性與配置

Gary M. Thompson（康乃爾大學）分析了**專用桌 vs. 可合併桌**的權衡 [2, 3]：

- **專用桌（Dedicated）**：固定容量（如固定 4 人桌），簡單、無閒置時間，但對大型客群缺乏彈性。
- **可合併桌（Combinable）**：相鄰桌可合併（如兩張 4 人桌 → 一張 8 人桌），具彈性，但存在**閒置機會成本**：一張空桌為等待相鄰桌釋放而閒置，期間產生零營收。
- **關鍵發現**：最佳配置取決於**客群規模分佈**。客群規模變異大的餐廳，從可合併桌中獲益更多——但前提是帶位策略能考量閒置時間的權衡。

### 2.3 Bertsimas & Shioda（2003）— 打破先到先服務

Dimitris Bertsimas 與 Romy Shioda（MIT）在 Operations Research 中提出了**基於閾值的訂位政策** [4]：

- 當大型客群（較高預期營收）晚於小型客群抵達時，傳統 FCFS 是**營收次優**的。
- **預期邊際收益模型**：若未來大型客群佔用該桌位空間的**期望價值**超過當前小型客群的確定營收，系統應拒絕小型現場客。
- 引入**價值函數** V(s,t)，表示在系統狀態 s 與時間 t 下的預期未來營收——為 Task B 的 ADP 公式化奠定了基礎。

### 2.4 Coffman, Garey & Johnson（1997）— 裝箱問題理論

演算法基礎 [5]：

- **降序首次適配（FFD）**：將物品降序排列，依序放入第一個有足夠容量的箱子。近似比：11/9 OPT + 6/9。
- **約束裝箱問題**：箱子有**物品類型限制**（在本案中對應：沙發桌不可接受兒童椅）。
- 本研究的擴展：箱子可**變形**（合併/拆分），使之成為**具物品相依容量限制之可變尺寸裝箱問題**——遠比標準 BPP 困難。

### 2.5 近期研究方向

- **資源分配的 MARL**：多代理人強化學習已應用於叫車派送與倉儲機器人，但餐廳帶位（具獨特的空間-時間耦合約束）在 RL 文獻中仍幾乎未被探索。Task C 旨在填補此缺口。
- **近似動態規劃（ADP）**：Powell（2011）提供了處理序列決策中指數級狀態空間的框架——直接適用於 Task B。

---

## 3️⃣ 原型餐廳 — 原燒 台中西屯家樂福店

### 基本資訊

| 欄位 | 內容 |
|---|---|
| 品牌 | 原燒（Oh My! Yaki-Yan）— 王品集團 |
| 分店 | 台中西屯家樂福店 |
| 地址 | 台中市西屯區台灣大道四段1086號1樓（家樂福1樓） |
| 定位 | 日式燒肉，中高價位休閒餐飲 |
| 訂位系統 | inline.app（無公開 API） |

### 營業參數

| 參數 | 數值 |
|---|---|
| 營業時間 | 11:00 – 23:00 |
| 最後帶位 | 21:00（開店後 t = 600 分鐘） |
| 電話接聽 | 至 22:00 |
| 每組用餐時間 | 120 分鐘 |
| 翻桌緩衝 | 10 分鐘（清潔消毒） |
| 總桌數 | 約 27 桌（見拓樸） |
| 總座位數 | 約 106 位（因連通桌合併而浮動） |
| 價位區間 | NT$648 – NT$1,498+/人 |

---

## 4️⃣ 座位拓樸與約束

### 前區 — 舒適度優先

| 桌號 | 容量 | 類型 | 兒童椅 | 備註 |
|---|---|---|---|---|
| 1-1 ~ 1-3, 1-5 | 4 | 沙發 | **0（嚴禁）** | 高舒適度，禁兒童 |
| 1-4, 1-6 | 4 | 沙發（混合） | 最多 1 | 例外：容許 1 張兒童椅 |
| 1-11 ~ 1-13 | 6 | 標準 | 無限制 | 大組彈性區 |
| 3-1, 3-2 | 6+4 | VIP 包廂 | 無限制 | 合併 10 人；12 人溢位 |

### 後區 — 彈性優先

| 桌號 | 容量 | 兒童椅 |
|---|---|---|
| 2-1, 2-2, 2-3 | 4 | 無限制 |
| 3-3, 3-4, 3-5, 3-6 | 4 | 無限制 |
| 5-1 ~ 5-4 | 4 | 無限制 |

### 連通桌對 — 配置互斥鎖

| 桌對 | 預設配置 | 合併 | 不對稱拆分 | 禁止 |
|---|---|---|---|---|
| (2-4, 2-5) | 4+4 | 8（極限 10） | 2+6 | 6+2 |
| (2-6, 2-7) | 4+4 | 8（極限 10） | 2+6 | 6+2 |
| (5-1, 5-2) | 4+4 | 8（極限 10） | 2+6 | 6+2 |
| (5-3, 5-4) | 4+4 | 8（極限 10） | 2+6 | 6+2 |

**狀態剛性鎖定（Configuration Rigidity）**：一旦桌對中任一桌被佔用，該桌對的配置即被**鎖死**，直到兩桌完全釋放。這是空間層面的互斥鎖——也是 Thompson 可合併桌模型的核心挑戰。

### 12 人特例路由

當不可分桌的 12 人客群抵達時，系統跳過常規評分，依循寫死的優先級路徑：

1. **第一優先**：(2-4, 2-5, 3-4) — 後區，2 連通 + 1 標準
2. **第二優先**：(2-6, 2-7, 3-5) — 備援連通三桌組
3. **第三優先**：(3-1, 3-2) — 前區 VIP 包廂（10 席，2 站位）

### 營運約束（人之常情）

| # | 約束 | 類型 | 實作方式 |
|---|---|---|---|
| C1 | 沙發區嚴禁兒童椅 | 硬約束 | `baby_limit > 0` 檢查 |
| C2 | 每桌至少 1 位成人 | 硬約束 | `adults >= 1` 驗證 |
| C3 | 大組客群（≥5 人）不可跨排 | 硬約束 | `Adjacency_Split` 規則 |
| C4 | 連通桌配置鎖死 | 硬約束 | `CombinablePair.locked_config` |
| C5 | 陰影區間（預約時間保護） | 硬約束 | 時間軸重疊檢查 |
| C6 | 前區舒適度最大化 | 軟約束 | 每桌前區 +100 分 |
| C7 | 無幼童客群優先享沙發 | 軟約束 | 沙發 + 無嬰兒 +50 分 |
| C8 | 最佳適配（最小化空位浪費） | 軟約束 | −15 × 浪費座位數 |
| C9 | 預約客優先 | 軟約束 | 預約客 +200 分 |

---

## 5️⃣ 數學模型（ILP + CSP）

### 決策變數

\[
x_{p,g,c,\tau} \in \{0,1\}
\]

客群 \(p\) 在時間 \(\tau\) 被分配至桌位組合 \(g\)、採用配置狀態 \(c\)。

### 目標函數：最大化 RevPASH

\[
\max \sum_{p \in P} \sum_{g \in G} \sum_{c \in C} x_{p,g,c,\tau_{\text{start}}} \cdot W(p,g)
\]

\[
W(p,g) = \underbrace{\frac{\text{Rev}_p}{\tau_p} \cdot \text{seats}_{g,c}}_{\text{RevPASH 貢獻}}
+ \underbrace{\alpha \cdot \mathbf{1}_{\text{front}}(g)}_{\text{前區加分}}
- \underbrace{\beta \cdot (\text{seats}_{g,c} - N_p)}_{\text{空位浪費懲罰}}
+ \underbrace{\gamma \cdot \mathbf{1}_{\text{reservation}}(p)}_{\text{預約客優先權重}}
\]

### 硬約束

**容量與屬性防呆**：

\[
x_{p,g,c,\tau} \cdot N_p \leq M_{g,c} \quad \text{（人數 ≤ 極限容量）}
\]
\[
x_{p,g,c,\tau} \cdot K_p \leq B_{g} \quad \text{（兒童椅需求 ≤ 家具限制）}
\]

**配置互斥鎖**：

\[
\sum_{c \in \mathcal{C}_g} x_{p_1,t_1,c,\tau_1} \cdot \sum_{c' \neq c} x_{p_2,t_2,c',\tau_2} = 0
\]

若桌位 \(t_1, t_2 \subset g\)（連通桌對）且 \(t_1\) 在時間 \(\tau_1\) 被佔用，則 \(t_2\) 在鎖定期間內不可被以衝突配置佔用。

**時間陰影區間（預約保護）**：

\[
x_{p_{\text{現場}},g,c,\tau} \cdot x_{p_{\text{預約}},g,c,\tau'} = 0
\quad \text{若 } |\tau - \tau'| < \tau_p + \tau_{\text{緩衝}}
\]

現場客不可佔用與未來預約時間窗重疊的桌位。

### 服務生負載與動線（Task A 擴充）

引入服務生集合 \(S\) 與決策變數 \(y_{t,s} \in \{0,1\}\)（桌位 \(t\) 由服務生 \(s\) 負責）：

\[
\sum_{s \in S} y_{t,s} = \sum_{p \in P} \sum_{c \in C} x_{p,t,c,\tau} \quad \forall t \in T
\]
\[
\sum_{t \in T} y_{t,s} \leq M_s \quad \forall s \in S \quad \text{（每位服務生最大桌數）}
\]

擴充懲罰項：

\[
P_{\text{空間}} = \alpha_s \cdot \sum_{s \in S} \max\left(0,\ \sum_{z \neq Z_s} a_{s,z}\right)
\]

完整公式化請參閱**研究路線圖 → Task A**。

---

## 6️⃣ 系統架構

```
                   ┌─────────────────────────┐
                   │       客群抵達           │
                   │   （預約 / 現場客）       │
                   └───────────┬─────────────┘
                               │
                               ▼
                   ┌─────────────────────────┐
                   │   階段 1：例外攔截       │
                   │   12 人特例覆寫          │
                   │   防呆驗證               │
                   └───────────┬─────────────┘
                               │
                               ▼
                   ┌─────────────────────────┐
                   │   階段 2：CSP 剪枝       │
                   │   - 容量檢查             │
                   │   - 兒童椅限制           │
                   │   - 時間陰影區間         │
                   │   - 配置互斥鎖           │
                   └───────────┬─────────────┘
                               │
                               ▼
                   ┌─────────────────────────┐
                   │   階段 3：啟發式評分     │
                   │   - RevPASH 估算         │
                   │   - 前區加分             │
                   │   - 最佳適配懲罰         │
                   │   - [服務生負載懲罰]     │ ← Task A
                   │   - [ADP 價值函數]       │ ← Task B
                   └───────────┬─────────────┘
                               │
                               ▼
                   ┌─────────────────────────┐
                   │   階段 4：狀態機同步     │
                   │   - occupied_until 鎖定  │
                   │   - 連通桌互斥鎖         │
                   │   - 陰影區間更新         │
                   └─────────────────────────┘
```

### 核心資料結構

```python
@dataclass
class Party:
    name: str                # 客群名稱
    adults: int              # 成人數
    baby_chairs: int         # 兒童椅數
    is_reservation: bool     # 是否預約
    is_splittable: bool      # 是否可分桌
    time_arriving: int       # 抵達時間（開店後分鐘數）

class Table:
    t_id: str                # 桌號，如 "2-4"
    max_cap: int             # 最大容納人數
    baby_limit: int          # -1 = 無限制, 0 = 禁止
    is_front: bool           # 是否前區
    is_sofa: bool            # 是否沙發
    row_id: str              # 排位分組
    occupied_until: int      # 釋放時間戳
    current_party: Optional[Party]

class CombinablePair:
    t1: Table
    t2: Table
    locked_config: Optional[str]  # '4+4', '2+6', '8_merged', None
```

---

## 7️⃣ 研究路線圖

### Phase 0 — 基礎建設（當前進度）

- [x] 原型拓樸建模（27 桌、4 組連通桌對）
- [x] 基礎 CSP 剪枝（容量、兒童椅、沙發限制）
- [x] 啟發式評分（前區、沙發、最佳適配、預約優先）
- [x] 12 人特例路由
- [x] 配置互斥鎖（連通桌對鎖定）

**待修復缺口**：

- [ ] **陰影區間實作**——系統目前未保護未來預約桌位不被現場客搶佔
- [ ] **12 人 `is_splittable` 邏輯**——硬編碼路由使用 3 桌，但 `is_splittable=False`；應允許強制分桌
- [ ] **Adjacency_Split 過度分配**——當前取整排空桌全部分配；需最佳子集選擇
- [ ] KPI 評估框架（RevPASH 追蹤、拒絕率、利用率）

### Task A — 服務生負載與空間路由

將服務生容量與空間約束納入 ILP 目標函數：

\[
\boxed{
\begin{aligned}
\max \quad & \sum_{p,g,c} W(p,g) \cdot x_{p,g,c,\tau}
\\
&- \alpha \cdot \sum_{s \in S} \max\left(0, \sum_{z \neq Z_s} a_{s,z}\right) \quad \text{（跨區移動懲罰）}
\\
&- \beta \cdot \sum_{s \in S} \max\left(0, L_s - M_s\right) \quad \text{（服務生超載懲罰）}
\\
&- \gamma \cdot \sum_{z \in Z} \zeta_z \cdot (1 - \zeta_z^{\text{prior}}) \quad \text{（區域冷啟動懲罰）}
\end{aligned}
}
\]

**核心機制**：區域冷啟動懲罰（\(\gamma\)）是迫使系統將 12 人客群帶往前區 1-11/1-12（已活躍區域）而非開通後區（產生新區域啟動成本）的關鍵槓桿。

> Task A 程式碼待實作 — 見 `rso_engine.py` v2。

### Task B — 近似動態規劃（ADP）

設計狀態價值函數 \(V(s, t)\)，評估在時間 \(t\) 從狀態 \(s\) 出發的預期未來營收：

\[
V(s, t) = \max_{a \in \mathcal{A}(s)} \left[ R(s, a) + \gamma \cdot \mathbb{E}[V(s', t+\Delta t)] \right]
\]

其中：
- \(s\)：當前桌位佔用狀態 + 未來預約向量（120 分鐘前瞻）
- \(a\)：帶位決策（分配至何桌、何配置）
- \(R(s,a)\)：即時 RevPASH 貢獻
- **閾值政策**：僅在 \(R(p, a^*) \geq \mathbb{E}[\text{未來損失}]\) 時接受現場客 \(p\)

此為 Bertsimas & Shioda（2003）模型在本餐廳拓樸上的正式化。

> Task B 設計文件待撰寫。

### Task C — OpenAI Gymnasium RL 環境

將 RSO 封裝為標準 RL 環境：

| 組件 | 規格 |
|---|---|
| **觀察空間** | 桌位佔用向量（27 × 二元）、未來預約（120 分鐘前瞻）、各區服務生負載 |
| **動作空間** | 離散：分配至桌位組 g 配置 c（或拒絕並給出候位時間估計） |
| **獎勵** | RevPASH 貢獻 − 服務生超載懲罰 − 區域冷啟動懲罰 |
| **代理人** | PPO（近端策略最佳化） |
| **評估** | 在 3 個餐期場景中與啟發式基準線對比 |

> Task C `gymnasium` 環境待實作。

### 未來展望 — MARL 編排器

單代理人環境驗證完成後，擴展至多代理人：
- **代理人 1**：桌位分配員（帶位員）
- **代理人 2**：服務生調度員（樓面主管）
- **代理人 3**：訂位政策控制器（營收經理）
- **協作獎勵**：全域 RevPASH

---

## 8️⃣ 快速開始

### 環境需求

- Python 3.9+
- 無外部依賴（純標準庫）

### 執行模擬

```bash
git clone https://github.com/ianbbbanian5476/RSO.git
cd RSO
python3 rso_engine.py
```

### 使用範例

```python
from rso_engine import RestaurantEngine, Party

engine = RestaurantEngine()

# 帶位一組 2 大 1 嬰兒的現場客
result = engine.allocate(
    Party("現場客 A", adults=2, baby_chairs=1,
          is_reservation=False, is_splittable=False),
    current_time=30  # 11:30
)
print(result)
# ✅ 現場客 A 帶位成功：1-4 (配置: Single, 分數: 285)
```

---

## 9️⃣ 參考文獻

[1] **Kimes, S. E.**（1999）. Implementing Restaurant Revenue Management. *Cornell Hotel and Restaurant Administration Quarterly*, 40(3), 16–21.
> 提出 RevPASH 作為核心 KPI 與 RRM 五步驟框架，為現代餐廳收益管理奠定基礎。

[2] **Thompson, G. M.**（2002）. Optimizing a Restaurant's Seating Capacity: Use Dedicated or Combinable Tables? *Cornell Hotel and Restaurant Administration Quarterly*, 43(3), 48–57.
> 首篇對專用桌 vs. 可合併桌權衡進行量化分析，證明閒置保留成本使可合併桌對特定客群分佈並非明顯最佳解。

[3] **Thompson, G. M.**（2003）. Optimizing Restaurant-Table Configurations: Specifying Combinable Tables. *Cornell Hotel and Restaurant Administration Quarterly*, 44(1), 53–60.
> 延伸 2002 年模型，回答「具體哪些桌應該設為可合併」。關鍵發現：策略性配置連通桌對，可在近乎零資本成本下獲得營收增益。

[4] **Bertsimas, D., & Shioda, R.**（2003）. Restaurant Revenue Management. *Operations Research*, 51(3), 472–486.
> 將打破 FCFS 問題正式化為預期營收最佳化問題，引入即時帶位決策的閾值政策。為 Task B 的 ADP 公式化之直接前導研究。

[5] **Coffman, E. G., Garey, M. R., & Johnson, D. S.**（1997）. Approximation Algorithms for Bin Packing: A Survey. 收錄於 *Approximation Algorithms for NP-Hard Problems*（pp. 46–93）. PWS Publishing.
> FFD 及其變體的經典參考文獻。本案的 CBPP 在此基礎上擴展了可變形箱子與物品類型約束。

[6] **Kimes, S. E., & Thompson, G. M.**（2004）. Restaurant Revenue Management at Chevys: Determining the Best Table Mix. *Cornell Hotel and Restaurant Administration Quarterly*, 45(1), 52–67.
> Thompson 桌位組合模型在 Chevys 餐廳的實務應用，證實透過最佳桌位配置可產生可量測的 RevPASH 改善。

[7] **Powell, W. B.**（2011）. *Approximate Dynamic Programming: Solving the Curses of Dimensionality*（第二版）. Wiley.
> ADP 基礎教材，為 Task B 在高維度餐廳狀態空間中的價值函數近似提供理論基礎。

[8] **Sutton, R. S., & Barto, A. G.**（2018）. *Reinforcement Learning: An Introduction*（第二版）. MIT Press.
> Task C Gymnasium 環境與 PPO 代理人架構的 RL 基礎理論。
