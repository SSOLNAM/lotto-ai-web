import pandas as pd
import random
import os
from collections import Counter

# ==========================================
# [설정] 파일 경로 (절대 경로)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# CSV 파일 경로 설정
CSV_PATH = os.path.join(BASE_DIR, 'number.csv')

class LottoEngine:
    def __init__(self):
        self.refresh_data()

    def refresh_data(self):
        """데이터 로드 (CSV 전용)"""
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {CSV_PATH}")

        # CSV 읽기
        self.df = pd.read_csv(CSV_PATH)
        
        # 전처리: 결측치 제거
        self.df = self.df.dropna()
        
        # '회차' 컬럼 처리 (쉼표 제거 및 정수 변환)
        # 데이터가 문자열일 경우에만 처리
        if self.df['회차'].dtype == 'object':
            self.df['회차'] = self.df['회차'].str.replace(',', '').astype(int)
        
        # 회차순 정렬
        self.df = self.df.sort_values('회차').reset_index(drop=True)
        
        # 번호 컬럼(1번~7번 컬럼: 당첨번호 6개 + 보너스) 정수 변환
        cols = self.df.columns[1:8]
        for col in cols:
            self.df[col] = self.df[col].astype(int)

        # Gap 가중치 학습 (안 나온 번호일수록 확률 높음)
        self.all_history_nums = self._get_all_history_nums(self.df)
        self.gap_weights = self._calculate_gap_weights(self.all_history_nums)
        
        print("✅ 유연한(Flexible) 엔진 학습 완료 (CSV 모드).")

    # --- [유틸리티] ---
    def _get_all_history_nums(self, df):
        nums = []
        for _, row in df.iterrows():
            try:
                # 당첨번호 6개만 추출 (보너스 제외, 인덱스 1~6)
                draw = [int(n) for n in row.iloc[1:7].tolist()]
                nums.extend(draw)
            except: pass
        return nums

    def _get_7_group_id(self, number):
        # 1~7, 8~14... 로 그룹핑
        return ((number - 1) // 7) + 1

    def _calculate_gap_weights(self, history_nums):
        freq = pd.Series(history_nums).value_counts()
        full_freq = pd.Series(0, index=range(1, 46))
        full_freq.update(freq)
        
        total_draws = len(history_nums) // 6
        expected = total_draws * (6 / 45)
        gap_weights = {}
        for num in range(1, 46):
            # 안 나온 횟수가 많을수록 가중치(확률) 증가
            gap_weights[num] = max(expected - full_freq[num], 0.1)
        return gap_weights

    # --- [필터] ---
    def _validate_combination(self, numbers):
        # 1. 합계 (90~190) - 유연하게 적용
        if not (90 <= sum(numbers) <= 190): return False
        
        # 2. 홀짝 (전체 홀수 혹은 전체 짝수만 아니면 통과)
        odd = len([n for n in numbers if n % 2 != 0])
        if odd == 0 or odd == 6: return False
        
        # 3. 7분할 쏠림 방지 (한 구역에 4개 이상 몰리면 탈락)
        group_counts = Counter([self._get_7_group_id(n) for n in numbers])
        for cnt in group_counts.values():
            if cnt >= 4: return False 
        
        return True

    # --- [번호 생성] ---
    def generate_numbers(self, count=5, fixed=[], exclude=[]):
        results = []
        
        for i in range(count):
            for _ in range(5000): # 필터 통과를 위해 충분히 반복
                final_set = list(fixed)
                
                # 사용 가능한 숫자 풀(Pool)과 가중치 준비
                pool = [n for n in range(1, 46) if n not in final_set and n not in exclude]
                weights = [self.gap_weights.get(n, 0.1) for n in pool]
                
                # 부족한 개수만큼 뽑기
                needed = 6 - len(final_set)
                if needed > 0:
                    picks = []
                    temp_pool = pool[:]
                    temp_weights = weights[:]
                    
                    # 비복원 추출 (중복 없이 뽑기)
                    while len(picks) < needed:
                        if not temp_pool: break
                        try:
                            pick = random.choices(temp_pool, weights=temp_weights, k=1)[0]
                        except ValueError: break
                        
                        if pick not in picks and pick not in final_set:
                            picks.append(pick)
                            # 뽑힌 숫자는 임시 풀에서 제거
                            idx = temp_pool.index(pick)
                            temp_pool.pop(idx)
                            temp_weights.pop(idx)
                    
                    final_set.extend(picks)

                final_set = list(set(final_set))
                if len(final_set) != 6: continue
                final_set.sort()
                
                # 필터 검증
                if self._validate_combination(final_set):
                    results.append({
                        "game_seq": i + 1,
                        "numbers": final_set,
                        "sum": sum(final_set),
                        "odd_even": f"{len([n for n in final_set if n%2!=0])}:{len([n for n in final_set if n%2==0])}"
                    })
                    break
                    
        return {
            "ai_pattern": "Flexible Weighted (유연한 가중치 모드)",
            "games": results
        }