import pandas as pd
import random
import os
from collections import Counter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'number.csv')

class LottoEngine:
    def __init__(self):
        self.refresh_data()

    def refresh_data(self):
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {CSV_PATH}")

        # [수정] 헤더가 없는 CSV이므로 이름을 직접 지정해서 읽어옵니다.
        self.df = pd.read_csv(CSV_PATH, header=None, names=['회차', '1', '2', '3', '4', '5', '6', '보너스'])
        
        self.df = self.df.dropna()
        
        # '회차' 컬럼 처리 (쉼표 제거 및 정수 변환)
        if self.df['회차'].dtype == 'object':
            self.df['회차'] = self.df['회차'].str.replace('"', '').str.replace(',', '').astype(int)
        
        self.df = self.df.sort_values('회차').reset_index(drop=True)
        
        cols = ['1', '2', '3', '4', '5', '6', '보너스']
        for col in cols:
            self.df[col] = self.df[col].astype(int)

        self.all_history_nums = self._get_all_history_nums(self.df)
        self.gap_weights = self._calculate_gap_weights(self.all_history_nums)
        print("✅ 엔진 학습 완료 (CSV 모드).")

    def _get_all_history_nums(self, df):
        nums = []
        for _, row in df.iterrows():
            try:
                # iloc[1:7]은 1,2,3,4,5,6번 당첨번호를 가져옵니다.
                draw = [int(n) for n in row.iloc[1:7].tolist()]
                nums.extend(draw)
            except: pass
        return nums

    def _get_7_group_id(self, number):
        return ((number - 1) // 7) + 1

    def _calculate_gap_weights(self, history_nums):
        freq = pd.Series(history_nums).value_counts()
        full_freq = pd.Series(0, index=range(1, 46))
        full_freq.update(freq)
        total_draws = len(history_nums) // 6
        expected = total_draws * (6 / 45)
        gap_weights = {}
        for num in range(1, 46):
            gap_weights[num] = max(expected - full_freq[num], 0.1)
        return gap_weights

    def _validate_combination(self, numbers):
        if not (90 <= sum(numbers) <= 190): return False
        odd = len([n for n in numbers if n % 2 != 0])
        if odd == 0 or odd == 6: return False
        group_counts = Counter([self._get_7_group_id(n) for n in numbers])
        for cnt in group_counts.values():
            if cnt >= 4: return False 
        return True

    def generate_numbers(self, count=5, fixed=[], exclude=[]):
        results = []
        for i in range(count):
            for _ in range(5000):
                final_set = list(fixed)
                pool = [n for n in range(1, 46) if n not in final_set and n not in exclude]
                weights = [self.gap_weights.get(n, 0.1) for n in pool]
                needed = 6 - len(final_set)
                if needed > 0:
                    picks = []
                    temp_pool = pool[:]
                    temp_weights = weights[:]
                    while len(picks) < needed:
                        if not temp_pool: break
                        try:
                            pick = random.choices(temp_pool, weights=temp_weights, k=1)[0]
                        except ValueError: break
                        if pick not in picks and pick not in final_set:
                            picks.append(pick)
                            idx = temp_pool.index(pick)
                            temp_pool.pop(idx)
                            temp_weights.pop(idx)
                    final_set.extend(picks)
                final_set = list(set(final_set))
                if len(final_set) != 6: continue
                final_set.sort()
                if self._validate_combination(final_set):
                    results.append({
                        "game_seq": i + 1,
                        "numbers": final_set,
                        "sum": sum(final_set),
                        "odd_even": f"{len([n for n in final_set if n%2!=0])}:{len([n for n in final_set if n%2==0])}"
                    })
                    break
        return {"ai_pattern": "Flexible Weighted", "games": results}