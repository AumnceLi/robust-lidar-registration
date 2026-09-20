import time,numpy as np
from scipy.optimize import minimize
import m_common as M
obj=M.Objective(); P=M.load_scan(0)['aligned'].astype(float)
hh=np.array([M.FD_T]*3+[M.FD_R]*3); k=1
def fg(x):
    f0=obj.values(P,x)[k]; g=np.zeros(6)
    for a in range(6):
        e=np.zeros(6);e[a]=hh[a]; g[a]=(obj.values(P,x+e)[k]-obj.values(P,x-e)[k])/(2*hh[a])
    return f0,g
bnds=[(-.3,.3)]*3+[(-np.deg2rad(15),np.deg2rad(15))]*3
for opt in [dict(ftol=1e-11,gtol=1e-7,maxls=8),dict(ftol=1e-10,gtol=1e-6,maxls=5),dict(ftol=1e-9,gtol=1e-5,maxls=4)]:
    t=time.perf_counter(); r=minimize(fg,np.zeros(6),jac=True,method='L-BFGS-B',bounds=bnds,options=opt|dict(maxiter=200))
    print(opt,'-> %.1fs nfev=%d t*=%.1fmm g*=%.1e'%(time.perf_counter()-t,r.nfev,np.linalg.norm(r.x[:3])*1000,np.linalg.norm(fg(r.x)[1])))
