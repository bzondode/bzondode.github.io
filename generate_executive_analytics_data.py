import pandas as pd
import numpy as np

rng=np.random.default_rng(42)
dates=pd.date_range("2025-01-01","2026-08-23",freq="D")
regions=["North","Central","East","West"]
subs={r:[r[0]+str(i) for i in range(1,4)] for r in regions}
cats=["Property","Service","Safety","Quality","Other"]
rows=[]

for d in dates:
    for r in regions:
        for s in subs[r]:
            for c in cats:
                base={"Property":1.3,"Service":1.0,"Safety":.9,"Quality":.7,"Other":.5}[c]
                rf={"North":1.05,"Central":1.15,"East":.92,"West":.88}[r]
                trend=.94 if d.year==2026 else 1
                if d.year==2026 and r=="Central" and c=="Property": trend*=1.18
                if d.year==2026 and r=="West" and c=="Safety": trend*=.78
                season=1+.12*np.sin(2*np.pi*d.dayofyear/365.25)
                n=rng.poisson(max(.55*base*rf*trend*season,.05))
                if n: rows.append((d.date().isoformat(),r,s,c,int(n)))

pd.DataFrame(rows,columns=["Date","Region","Subregion","Category","EventCount"]).to_csv("executive_analytics_sample.csv",index=False)
