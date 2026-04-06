# Restaurant Seating Optimization (RSO) Engine 🍽️

[](https://www.google.com/search?q=https://opensource.org/licenses/MIT)
[](https://www.google.com/search?q=https://www.python.org/downloads/)
[](https://www.google.com/search?q=)

這是一個基於**整數線性規劃 (Integer Linear Programming, ILP)** 與**約束滿足問題 (Constraint Satisfaction Problem, CSP)** 的動態餐廳帶位排程系統。

本專案旨在解決高複雜度硬體限制下的「動態餐廳座位分配問題」。透過將實體座位抽象化為**帶有時間軸的二維裝箱問題 (2D Bin Packing Problem with Time Horizon)**，本系統能在毫秒級別內計算出最大化空間利用率、且完美符合「人之常情」商業邏輯的最佳帶位解。

-----

## 📖 目錄

  - [核心概念：動態裝箱問題](https://www.google.com/search?q=%23%E6%A0%B8%E5%BF%83%E6%A6%82%E5%BF%B5%E5%8B%95%E6%85%8B%E8%A3%9D%E7%AE%B1%E5%95%8F%E9%A1%8C)
  - [餐廳拓樸與硬體配置](https://www.google.com/search?q=%23%E9%A4%90%E5%BB%B3%E6%8B%93%E6%A8%B8%E8%88%87%E7%A1%AC%E9%AB%94%E9%85%8D%E7%BD%AE)
  - [商業邏輯與「人之常情」約束](https://www.google.com/search?q=%23%E5%95%86%E6%A5%AD%E9%82%8F%E8%BC%AF%E8%88%87%E4%BA%BA%E4%B9%8B%E5%B8%B8%E6%83%85%E7%B4%84%E6%9D%9F)
  - [數學模型 (Mathematical Formulation)](https://www.google.com/search?q=%23%E6%95%B8%E5%AD%B8%E6%A8%A1%E5%9E%8B-mathematical-formulation)
  - [演算法架構與狀態機](https://www.google.com/search?q=%23%E6%BC%94%E7%AE%97%E6%B3%95%E6%9E%B6%E6%A7%8B%E8%88%87%E7%8B%80%E6%85%8B%E6%A9%9F)
  - [Python 核心實作](https://www.google.com/search?q=%23python-%E6%A0%B8%E5%BF%83%E5%AF%A6%E4%BD%9C)

-----

## 🧠 核心概念：動態裝箱問題

傳統的**裝箱問題 (Bin Packing Problem)** 目標是用最少的箱子裝下所有物品。但在餐廳營運中，我們面臨的是其高階變體：

1.  **容器可變形 (Combinable Bins)**：箱子（桌子）可以根據策略合併或拆分。
2.  **多維度限制 (Multi-dimensional Constraints)**：除了「人數（體積）」，還有「兒童椅限制」、「沙發互斥性」等拓樸限制。
3.  **時間軸競爭 (Online Scheduling)**：物品（客人）是隨機抵達的，且有時間駐留限制。未來的預約客與當下的現場客會競爭同一個箱子（桌位）。

本專案採用**基於約束的貪婪計分演算法 (Constraint-Based Greedy Scoring)**，以確保系統具備線上即時決策能力。

-----

## 🗺️ 餐廳拓樸與硬體配置

餐廳以「王品集團原燒 台中西屯家樂福店」為原型進行研究。
系統將實體空間劃分為兩大區塊，並定義了嚴格的容量與硬體限制。

### 前區 (Front Area) - 舒適度優先

  * **四人沙發列**：`1-1` \~ `1-6`。
      * *硬體限制*：僅 `1-4`、`1-6` 最多可放置 1 張兒童椅；其餘為沙發區，**嚴禁**放置兒童椅。
  * **六人標準列**：`1-11` \~ `1-13`。兒童椅無限制。
  * **前區包廂 (極限 12 人)**：常態為 10 人配置，內部以隔板分為 `3-1` (6人) 與 `3-2` (4人)。

### 後區 (Back Area) - 彈性與動態併桌

全區皆無兒童椅限制。基本設計皆為 4 人桌。

  * **一般四人桌**：`2-1` \~ `2-3`、`3-3` \~ `3-6`。
  * **後區包廂**：`5-1` \~ `5-4`。
  * **動態連通桌 (Combinable Pairs)**：
    包含 `(2-4, 2-5)`、`(2-6, 2-7)`、`(5-1, 5-2)`、`(5-3, 5-4)`。
      * *變形規則*：預設為 4+4。可合併為 8 人桌 (極限 10 人)；或進行**不對稱拆分**成 2+6 (例如 2-4 坐 2 人，2-5 坐 6 人)，但**嚴禁** 6+2 拆分。

-----

## ⚖️ 商業邏輯與「人之常情」約束

本系統嚴格遵守以下營運邏輯（演算法中的權重與防呆機制）：

1.  **舒適度極大化 (Soft Constraint)**：前區沙發位優先級高於後區。無幼童的客群應優先享受沙發區。
2.  **預約霸王條款 (Hard Constraint)**：訂位客優先於現場客；系統會建立「陰影區間 (Shadow Zone)」保護預約桌位。
3.  **實體防呆機制 (Validation)**：兒童椅視同佔位（例：3大1小=4人容量）；不可全桌皆為兒童椅（須 $A \ge 1$）。
4.  **大組客群不跨排 (Topology Adjacency)**：5 人(含)以上需分桌時，僅可安排於同一列的相鄰座位，不可跨排。
5.  **12 人特殊體驗覆蓋 (Priority Override)**：為維持 12 人大組的用餐體驗，優先順序強制寫死為：`(2-4, 2-5, 3-4)` \> `(2-6, 2-7, 3-5)` \> `(3-1, 3-2)` 包廂。
6.  **狀態剛性鎖定 (Configuration Rigidity)**：`(2-4, 2-5)` 等連通桌，一旦其中一張入座，整個群組的變形配置 (Configuration) 即被鎖死，不可在客人用餐中途改變隔板或桌型。
7.  **時間邊界 (Time Bounds)**：最大用餐時間 120 分鐘，清桌緩衝時間 10 分鐘。

-----

## 🧮 數學模型 (Mathematical Formulation)

本系統的核心邏輯可抽象為以下的 ILP 模型：

### 決策變數

定義四維布林決策變數 $x_{p,g,c,\tau} \in \{0, 1\}$。若客人群組 $p$ 在時間 $\tau$ 被分配到桌位組合 $g$，且採用變形配置狀態 $c$，則值為 $1$，否則為 $0$。

### 目標函數 (最大化整體滿意度與效率)

$$\max \sum_{p \in P} \sum_{g \in G} \sum_{c \in C} x_{p,g,c,\tau_{start}} \cdot W(p, g)$$
其中權重 $W(p, g)$ 包含：前區加分、沙發保留加分、以及未填滿座位的空間浪費懲罰。

### 核心約束條件 (Hard Constraints)

**1. 容量與硬體防呆**
$$x_{p,g,c,\tau} \cdot N_p \le M_{g,c}$$
$$x_{p,g,c,\tau} \cdot K_p \le B_{g}$$
(人數 $N_p$ 不可超過極限容量 $M$；兒童椅需求 $K_p$ 不可超過硬體上限 $B$)

**2. 變形配置鎖定 (Configuration Rigidity)**
確保連通桌在佔用時間區間內，實體配置不發生衝突變更：
$$\sum_{c \in \mathcal{C}_g} x_{p_1, t_1, c, \tau_1} \cdot x_{p_2, t_2, c', \tau_2} = 0, \quad \forall c \neq c', \text{where } t_1, t_2 \subset g$$

-----

## ⚙️ 演算法架構與狀態機

系統處理每一次帶位請求的 Pipeline 如下：

1.  **例外攔截器 (Exception Handler)**：偵測 $N_p = 12$ 且不可分桌時，直接走訪寫死的優先級拓樸陣列。
2.  **CSP 剪枝引擎 (Pruning Engine)**：過濾掉容量不足、無兒童椅權限、或處於預約「陰影區間」的桌次。
3.  **啟發式評分 (Heuristic Scoring)**：對合法解打分。計算剩餘空位的機會成本、前區加分等。
4.  **狀態機同步 (State Machine Sync)**：一旦確定帶位，更新該桌的 `occupied_until` 屬性，並對可變形桌 (如 2-4, 2-5) 觸發互斥鎖 (Mutex)，鎖死其空間配置狀態。

-----

## 💻 Python 核心實作

以下為本專案核心演算邏輯的精簡架構展示：

```python
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class Party:
    total_people: int
    adults: int
    baby_chairs: int
    is_reservation: bool
    is_splittable: bool

class TableGroup:
    def __init__(self, group_id: str, base_cap: int, max_cap: int, baby_limit: int, is_front: bool, is_sofa: bool):
        self.group_id = group_id
        self.capacity = (base_cap, max_cap)
        self.baby_limit = baby_limit
        self.is_front = is_front
        self.is_sofa = is_sofa
        self.locked_configuration: Optional[str] = None
        self.occupied_until: int = 0  # Timestamp

class RSOEngine:
    def __init__(self):
        self.tables = self._initialize_topology()
        # 12人特例陣列
        self.special_12_pax = [['2-4', '2-5', '3-4'], ['2-6', '2-7', '3-5'], ['3-1', '3-2']]

    def allocate(self, party: Party, current_time: int) -> str:
        # Phase 1: 12-Pax Exception
        if party.total_people == 12 and not party.is_splittable:
            return self._handle_12_pax()

        valid_candidates = []

        # Phase 2: Hard Constraint Pruning
        for table in self.tables:
            if current_time < table.occupied_until:
                continue # 桌子有人或還在清理緩衝期
                
            if party.adults == 0 or party.baby_chairs >= party.total_people:
                continue # 防呆：無大人或全兒童椅
                
            if party.total_people > table.capacity[1]:
                continue # 極限容量不足
                
            if table.baby_limit != -1 and party.baby_chairs > table.baby_limit:
                continue # 兒童椅限制 (沙發區)
                
            valid_candidates.append(table)

        if not valid_candidates:
            return "NO_AVAILABLE_TABLES"

        # Phase 3: Heuristic Scoring
        best_table = max(valid_candidates, key=lambda t: self._calculate_score(t, party))

        # Phase 4: State Locking
        best_table.occupied_until = current_time + 120 + 10 # 120min 用餐 + 10min 清理
        self._lock_configuration(best_table, party)

        return f"ALLOCATED: {best_table.group_id}"

    def _calculate_score(self, table: TableGroup, party: Party) -> int:
        score = 0
        if table.is_front: score += 100
        if table.is_sofa and party.baby_chairs == 0: score += 50
        # 最佳適配：懲罰閒置座位
        score -= (table.capacity[0] - party.total_people) * 10 
        return score
```