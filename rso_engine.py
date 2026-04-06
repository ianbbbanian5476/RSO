import time
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional

# ==========================================
# 1. 資料模型 (Data Models)
# ==========================================

@dataclass
class Party:
    name: str
    adults: int
    baby_chairs: int
    is_reservation: bool
    is_splittable: bool

    @property
    def total(self) -> int:
        return self.adults + self.baby_chairs

class Table:
    def __init__(self, t_id: str, max_cap: int, baby_limit: int, is_front: bool, is_sofa: bool, row_id: str):
        self.t_id = t_id
        self.max_cap = max_cap
        self.baby_limit = baby_limit
        self.is_front = is_front
        self.is_sofa = is_sofa
        self.row_id = row_id
        
        # 狀態屬性
        self.occupied_until: int = 0
        self.current_party: Optional[Party] = None

    def is_empty(self, current_time: int) -> bool:
        return current_time >= self.occupied_until

class CombinablePair:
    """處理後區 (2-4, 2-5) 等特殊連通桌的狀態機"""
    def __init__(self, t1: Table, t2: Table):
        self.t1 = t1  # 例如 2-4
        self.t2 = t2  # 例如 2-5
        self.locked_config: Optional[str] = None # '4+4', '2+6', '8_merged'

    def is_fully_empty(self, current_time: int) -> bool:
        return self.t1.is_empty(current_time) and self.t2.is_empty(current_time)

    def set_config(self, config_name: str, current_time: int):
        # 只有在全空時才能改變變形狀態
        if self.is_fully_empty(current_time):
            self.locked_config = config_name

# ==========================================
# 2. 帶位引擎 (Restaurant Seating Optimization Engine)
# ==========================================

class RestaurantEngine:
    def __init__(self):
        self.tables: Dict[str, Table] = {}
        self.combinable_pairs: List[CombinablePair] = []
        self._initialize_topology()

    def _initialize_topology(self):
        # 前區 - 沙發排 (1-1~1-6)
        for i in range(1, 7):
            t_id = f"1-{i}"
            is_sofa = (i not in [4, 6])
            baby_limit = 1 if i in [4, 6] else 0
            self.tables[t_id] = Table(t_id, 4, baby_limit, True, is_sofa, "F_ROW_1")
            
        # 前區 - 6人標準排 (1-11~1-13)
        for i in range(11, 14):
            self.tables[f"1-{i}"] = Table(f"1-{i}", 6, -1, True, False, "F_ROW_2")
            
        # 前區 - 包廂
        self.tables["3-1"] = Table("3-1", 6, -1, True, False, "F_VIP")
        self.tables["3-2"] = Table("3-2", 4, -1, True, False, "F_VIP")

        # 後區 - 各排
        b_row_1 = ["2-1", "2-2", "2-3"]
        b_row_2 = ["2-4", "2-6"]
        b_row_3 = ["2-5", "2-7"]
        b_row_4 = ["3-3", "3-4", "3-5", "3-6"]
        b_vip = ["5-1", "5-2", "5-3", "5-4"]

        for row_id, t_list in enumerate([b_row_1, b_row_2, b_row_3, b_row_4, b_vip], start=1):
            for t_id in t_list:
                self.tables[t_id] = Table(t_id, 4, -1, False, False, f"B_ROW_{row_id}")

        # 註冊特殊連通組合 (Configuration Mutex)
        pairs = [("2-4", "2-5"), ("2-6", "2-7"), ("5-1", "5-2"), ("5-3", "5-4")]
        for p1, p2 in pairs:
            self.combinable_pairs.append(CombinablePair(self.tables[p1], self.tables[p2]))

    def allocate(self, party: Party, current_time: int) -> str:
        # 防呆檢查
        if party.adults == 0 or party.baby_chairs >= party.total:
            return f"❌ {party.name} 帶位失敗：無成人陪同或兒童椅數量不合規。"

        # 階段 1: 12 人專屬例外規則
        if party.total == 12 and not party.is_splittable:
            res = self._handle_12_pax_exception(party, current_time)
            if res: return res

        # 產生所有合法的候選方案 (單桌、併桌、分桌)
        candidates = self._generate_candidates(party, current_time)
        
        if not candidates:
            return f"⏳ {party.name} 目前無合適座位，需候位。"

        # 階段 2 & 3: 約束過濾與評分
        best_candidate = None
        highest_score = -float('inf')

        for candidate_tables, config_rule in candidates:
            score = self._calculate_score(candidate_tables, party)
            if score > highest_score:
                highest_score = score
                best_candidate = (candidate_tables, config_rule)

        # 階段 4: 狀態鎖定與帶位
        if best_candidate:
            tables_to_occupy, rule = best_candidate
            self._occupy_tables(tables_to_occupy, party, current_time, rule)
            t_names = ", ".join([t.t_id for t in tables_to_occupy])
            return f"✅ {party.name} 帶位成功：{t_names} (配置: {rule}, 分數: {highest_score})"

    def _generate_candidates(self, party: Party, current_time: int) -> List[Tuple[List[Table], str]]:
        candidates = []
        
        # 尋找單桌 (適合 1~6 人)
        for t in self.tables.values():
            if t.is_empty(current_time) and t.max_cap >= party.total:
                if t.baby_limit == -1  or party.baby_chairs <= t.baby_limit:
                    candidates.append(([t], "Single"))

        # 尋找特殊連通桌 (適合大組 7~10人 或 2+6配置)
        for pair in self.combinable_pairs:
            if pair.is_fully_empty(current_time):
                # 合併 8~10 人
                if 7 <= party.total <= 10:
                    candidates.append(([pair.t1, pair.t2], "Merged_8_10"))
                # 處理 2+6 拆分配置
                if party.total <= 6:
                    candidates.append(([pair.t2], "Split_2_6 (坐後者)"))
                if party.total <= 2:
                    candidates.append(([pair.t1], "Split_2_6 (坐前者)"))

        # 尋找同排分桌 (適合 >=5 人且可分桌)
        if party.total >= 5 and party.is_splittable:
            # 將空桌按 row_id 分組
            rows = {}
            for t in self.tables.values():
                if t.is_empty(current_time) and (t.baby_limit == -1 or party.baby_chairs <= t.baby_limit):
                    rows.setdefault(t.row_id, []).append(t)
            
            # 在同一排尋找容量足夠的組合
            for row_id, t_list in rows.items():
                if sum(t.max_cap for t in t_list) >= party.total:
                    # 簡化：直接全拿該排空桌來分
                    candidates.append((t_list, "Adjacency_Split"))
                    
        return candidates

    def _calculate_score(self, candidate_tables: List[Table], party: Party) -> int:
        score = 0
        total_cap = 0
        
        for t in candidate_tables:
            total_cap += t.max_cap
            # 軟約束 1：前區加分
            if t.is_front: score += 100
            # 軟約束 2：沒帶小孩享受沙發加分
            if t.is_sofa and party.baby_chairs == 0: score += 50
            
        # 軟約束 3：最佳適配 (減少空位浪費)
        wasted_seats = total_cap - party.total
        score -= (wasted_seats * 15)
        
        # 軟約束 4：預約客保護 (給予預約客更高權重尋找最優解)
        if party.is_reservation: score += 200
        
        return score

    def _occupy_tables(self, tables: List[Table], party: Party, current_time: int, config_rule: str):
        # 120 分鐘用餐 + 10 分鐘清理
        lock_time = current_time + 130 
        for t in tables:
            t.occupied_until = lock_time
            t.current_party = party
            
        # 處理配置狀態鎖定 (Configuration Mutex)
        for pair in self.combinable_pairs:
            if pair.t1 in tables or pair.t2 in tables:
                pair.set_config(config_rule, current_time)

    def _handle_12_pax_exception(self, party: Party, current_time: int) -> Optional[str]:
        priorities = [
            ["2-4", "2-5", "3-4"],
            ["2-6", "2-7", "3-5"],
            ["3-1", "3-2"]
        ]
        for priority_group in priorities:
            tables = [self.tables[t_id] for t_id in priority_group]
            if all(t.is_empty(current_time) for t in tables):
                self._occupy_tables(tables, party, current_time, "12_PAX_OVERRIDE")
                return f"🌟 {party.name} 觸發 12 人特例規則：{', '.join(priority_group)}"
        return None

# ==========================================
# 3. 執行與模擬 (Simulation)
# ==========================================
if __name__ == "__main__":
    engine = RestaurantEngine()
    current_time = 0 # 假設現在是 0 分鐘 (開館)

    print("--- 模擬開始：餐廳帶位系統 ---")
    
    # 預先塞入幾組客人佔用前區
    print(engine.allocate(Party("前區佔位客A", 4, 0, False, False), current_time)) # 佔 1-1
    print(engine.allocate(Party("前區佔位客B", 4, 0, False, False), current_time)) # 佔 1-2
    print(engine.allocate(Party("前區佔位客C", 6, 0, False, False), current_time)) # 佔 1-11
    
    print("\n--- 尖峰時刻：大量預約與現場客湧入 ---")
    # 模擬佇列
    queue = [
        Party("預約 R3 (帶嬰兒)", adults=2, baby_chairs=1, is_reservation=True, is_splittable=False),
        Party("預約 R4 (7人大組)", adults=7, baby_chairs=0, is_reservation=True, is_splittable=False),
        Party("預約 R1 (4人桌)", adults=4, baby_chairs=0, is_reservation=True, is_splittable=False),
        Party("現場 Walk-in (9人)", adults=9, baby_chairs=0, is_reservation=False, is_splittable=True),
        Party("現場 測試防呆 (皆嬰兒)", adults=0, baby_chairs=2, is_reservation=False, is_splittable=False)
    ]

    # 系統會優先處理預約客 (在實務中，會先跑一遍 reservation filter)
    reservations = [p for p in queue if p.is_reservation]
    walk_ins = [p for p in queue if not p.is_reservation]

    for p in reservations:
        print(engine.allocate(p, current_time))
        
    for p in walk_ins:
        print(engine.allocate(p, current_time))