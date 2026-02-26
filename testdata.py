from utils.data_loader import DataLoader
import pandas as pd

df = pd.read_excel('data/Backend_data.xlsx')
print("Column names found:")
print(df.columns.tolist())
print()
print("First 3 rows:")
print(df.head(3))
print()
print("Unique values in Industry column (if it exists):")
if 'Industry' in df.columns:
    print(df['Industry'].unique().tolist())
else:
    print("NO COLUMN NAMED 'Industry' FOUND")

industries = DataLoader.get_available_industries()
print('Industries found:', industries)
print()

industry = industries[0]
data = DataLoader.load_industry(industry)
print(f"Industry: {data['industry']}")
print(f"L1 Functions found: {len(data['functions'])}")
print()

for func in data['functions']:
    score = sum(sf['automation_score'] * sf['unit_cost_per_1000'] for sf in func['subfunctions'])
    cost = sum(sf['unit_cost_per_1000'] for sf in func['subfunctions'])
    avg_score = score/cost if cost > 0 else 0
    print(f"  L1: {func['name']}")
    print(f"      Subfunctions: {len(func['subfunctions'])}  |  Avg Score: {avg_score:.2f}  |  Total Cost: {cost:.2f}%")
    for sf in func['subfunctions']:
        print(f"        L2: {sf['name']}  |  Cost: {sf['unit_cost_per_1000']}%  |  Score: {sf['automation_score']}")
    print()