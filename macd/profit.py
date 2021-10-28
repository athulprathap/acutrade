
import numpy as np
import pandas as pd

df = pd.read_csv('/content/trades.csv',header=None)

gk = df.groupby(df[0])

b = gk.get_group('BUY')

s = gk.get_group('SELL')

totalB = b[1].sum()

totalS = s[1].sum()

print(totalS-totalB)

