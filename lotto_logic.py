import pandas as pd
import random
import os
from collections import Counter
from itertools import combinations

# ==========================================
# [설정] 파일 경로 (절대 경로)
# ==========================================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'number.csv')

class LottoEngine:
    def __init__(self):
        self.refresh_data()

    def refresh_data(self):
        """데이터 로드 및 노출 순위 패턴 분석"""
        if not os.path.exists(CSV_PATH):
            raise FileNotFoundError(f"데이터 파일을 찾을 수 없습니다: {CSV_PATH}")

        # 헤더 없는 CSV 읽기
        self.df = pd.read_csv(CSV_PATH, header=None, names=['회차', '1', '2', '3', '4', '5', '6', '보너스'])
        self.df = self.df.dropna()
        
        # '회차' 컬럼 처리 (쉼표 제거 및 정수 변환)
        if self.df['회차'].dtype == 'object':
            self.df['회차'] = self.df['회차'].str.replace('"', '').str.replace(',', '').astype(int)
        
        self.df = self.df.sort_values('회차').reset_index(drop=True)
        
        # 번호 컬럼 정수 변환
        for col in ['1', '2', '3', '4', '5', '6', '보너스']:
            self.df[col] = self.df[col].astype(int)

        # 1. 역대 전 회차의 당첨 번호 순위 패턴(Rank Pattern) 사전 계산
        self.all_round_winning_ranks = []
        self._precalculate_rank_history()
        
        # 2. 현재 시점(가장 최근)의 번호별 순위 맵 생성
        self.current_ranks_map = self._get_ranks_at_round(len(self.df))
        self.rank_to_num = {r: n for n, r in self.current_ranks_map.items()}
        
        # 3. 최근 100회차에서 가장 많이 등장한 순위 패턴 추출 (Top Patterns)
        history_patterns = self.all_round_winning_ranks[-100:]
        self.frequent_patterns = [p for p, count in Counter(history_patterns).most_common(200)]
        
        print(f"✅ 노출 순위 패턴 엔진 학습 완료 ({len(self.df)}회차 데이터 기반)")

    def _precalculate_rank_history(self):
        """과거 모든 회차의 당첨 번호가 당시 노출 순위로 몇 위였는지 기록"""
        counts = Counter()
        for i in range(len(self.df)):
            # 해당 회차 직전까지의 누적 횟수로 순위 매기기
            full_counts = {n: counts.get(n, 0) for n in range(1, 46)}
            # 빈도순(DESC), 같으면 번호순(ASC)으로 정렬하여 순위 부여
            sorted_nums = sorted(full_counts.items(), key=lambda x: (-x[1], x[0]))
            round_ranks_map = {num: r + 1 for r, (num, cnt) in enumerate(sorted_nums)}
            
            # 해당 회차의 당첨 번호 6개를 당시 순위(1~45위)로 변환
            winning_nums = self.df.iloc[i, 1:7].tolist()
            winning_ranks = tuple(sorted([round_ranks_map[n] for n in winning_nums]))
            self.all_round_winning_ranks.append(winning_ranks)
            
            # 다음 회차 계산을 위해 카운트 업데이트
            counts.update(winning_nums)

    def _get_ranks_at_round(self, n_rounds):
        """특정 시점까지의 누적 데이터로 현재의 1~45위 순위표 생성"""
        all_nums = []
        for i in range(n_rounds):
            all_nums.extend(self.df.iloc[i, 1:7].tolist())
        counts = Counter(all_nums)
        full_counts = {n: counts.get(n, 0) for n in range(1, 46)}
        sorted_nums = sorted(full_counts.items(), key=lambda x: (-x[1], x[0]))
        return {num: r + 1 for r, (num, cnt) in enumerate(sorted_nums)}

    def _validate(self, numbers):
        """백테스팅 수익률을 높여준 5단계 통계 필터"""
        # 1. 합계 필터 (90~190)
        s = sum(numbers)
        if not (90 <= s <= 190): return False
        
        # 2. 홀짝 필터 (모두 홀수이거나 모두 짝수인 경우 제외)
        odd = len([n for n in numbers if n % 2 != 0])
        if odd == 0 or odd == 6: return False
        
        # 3. AC값 필터 (번호 간의 불규칙성 지수 7 이상)
        diffs = set()
        for a, b in combinations(numbers, 2):
            diffs.add(b - a)
        if (len(diffs) - 5) < 7: return False
        
        # 4. 연번 필터 (3연번 이상 제외)
        sn = sorted(numbers)
        for i in range(len(sn)-2):
            if sn[i] + 1 == sn[i+1] and sn[i+1] + 1 == sn[i+2]:
                return False
                
        # 5. 끝수 필터 (동일 끝수 3개 이상 제외)
        ld = Counter([n % 10 for n in numbers])
        if any(v >= 3 for v in ld.values()): return False
        
        return True

    def generate_numbers(self, count=5, fixed=[], exclude=[]):
        """역대 빈출 순위 패턴을 현재 순위에 대입하여 번호 생성"""
        results = []
        
        # 패턴에 다양성을 주기 위해 상위 50개 패턴 내에서 셔플
        pattern_pool = self.frequent_patterns[:]
        top_n = pattern_pool[:50]
        random.shuffle(top_n)
        search_pool = top_n + pattern_pool[50:]

        for pat in search_pool:
            if len(results) >= count:
                break
                
            # 순위(Rank)를 현재 시점의 번호(Number)로 변환
            try:
                game = sorted([self.rank_to_num[r] for r in pat])
            except KeyError:
                continue # 순위 매핑 오류 시 스킵
            
            # 사용자 제약 조건 확인 (고정수/제외수)
            if fixed:
                if not all(f in game for f in fixed): continue
            if exclude:
                if any(e in game for e in exclude): continue
                
            # 최종 통계 필터 검증
            if self._validate(game):
                results.append({
                    "game_seq": len(results) + 1,
                    "numbers": game,
                    "sum": sum(game),
                    "odd_even": f"{len([n for n in game if n%2!=0])}:{len([n for n in game if n%2==0])}"
                })

        # 만약 패턴 매칭만으로 부족할 경우 (고정수가 너무 많을 때 등) 랜덤 보충
        while len(results) < count:
            game = sorted(random.sample(range(1, 46), 6))
            if self._validate(game) and all(f in game for f in fixed) and not any(e in game for e in exclude):
                results.append({
                    "game_seq": len(results) + 1,
                    "numbers": game,
                    "sum": sum(game),
                    "odd_even": f"{len([n for n in game if n%2!=0])}:{len([n for n in game if n%2==0])}"
                })

        return {
            "ai_pattern": "Historical Exposure Rank Pattern",
            "games": results
        }