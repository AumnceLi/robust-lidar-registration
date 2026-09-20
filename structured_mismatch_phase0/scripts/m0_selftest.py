# -*- coding: utf-8 -*-
"""Numerical-core self-test: model-self stationarity + known-offset recovery + timing."""
import time, numpy as np
import m_common as M

rng=np.random.default_rng(0)
obj=M.Objective()
print("model N=",len(obj.M))

# ---- (1) model-self: subset of the model is a perfect scan
sub=rng.choice(len(obj.M),9000,replace=False)
Pself=obj.M[sub].copy()
z=obj.probe(Pself,np.zeros(6))
print(f"\n[SELF] J0 p2p={z['Jp2p']*1e6:.3f} mm^2  p2l={z['Jp2l']*1e6:.3f} mm^2")
t0=time.perf_counter(); gh=M.grad_hess(obj,Pself); dt=time.perf_counter()-t0
print(f"[SELF] |g_p2p|={np.linalg.norm(gh['gp']):.4e}  |g_p2l|={np.linalg.norm(gh['gl']):.4e}  ({dt*1000:.0f}ms)")
print("       eig(Hp2p)=",np.linalg.eigvalsh(gh['Hp']).round(2))
lp=M.local_min_p2p(obj,Pself); ll=M.local_min_p2l(obj,Pself)
print(f"[SELF] localopt xi* p2p trans={np.linalg.norm(lp['xi'][:3])*1000:.3f}mm rot={np.degrees(np.linalg.norm(lp['xi'][3:])):.4f}deg it={lp['iters']}")
print(f"[SELF] localopt xi* p2l trans={np.linalg.norm(ll['xi'][:3])*1000:.3f}mm rot={np.degrees(np.linalg.norm(ll['xi'][3:])):.4f}deg it={ll['iters']}")

# ---- (2) known offset: P = T_true Msub ; optimizer (from xi=0) must undo it
xi_true=np.array([0.012,-0.008,0.004, *np.deg2rad([0.0,-0.35,0.20])])
Poff=M.apply_xi(Pself,xi_true)
Rt=M.rodrigues(xi_true[3:]); tt=xi_true[:3]
# expected recovery transform T_acc = T_true^{-1}: R=Rt^T, t=-Rt^T tt
exp_xi=np.concatenate([-Rt.T@tt, M.rodrigues_log(Rt.T)])
lp2=M.local_min_p2p(obj,Poff); ll2=M.local_min_p2l(obj,Poff)
print("\n[KNOWN OFFSET] expected recovery xi*=",exp_xi[:3].round(5),np.degrees(exp_xi[3:]).round(4))
print("[KNOWN OFFSET] p2p xi*=",lp2['xi'][:3].round(5),np.degrees(lp2['xi'][3:]).round(4),f"Jfinal={lp2['J']*1e6:.2f}mm^2 it={lp2['iters']}")
print("[KNOWN OFFSET] p2l xi*=",ll2['xi'][:3].round(5),np.degrees(ll2['xi'][3:]).round(4),f"Jfinal={ll2['J']*1e6:.2f}mm^2 it={ll2['iters']}")
print("p2p trans err mm=",np.linalg.norm(lp2['xi'][:3]-exp_xi[:3])*1000,
      " rot err deg=",np.degrees(np.linalg.norm(lp2['xi'][3:]-exp_xi[3:])))

# ---- (3) real scan timing + gradient
zscan=M.load_scan(0); P=zscan["aligned"].astype(np.float64)
t0=time.perf_counter(); ghR=M.grad_hess(obj,P); dt=time.perf_counter()-t0
print(f"\n[REAL scan0] N={len(P)} J0 p2p={ghR['J0'][0]:.5f} p2l={ghR['J0'][1]:.5f}  gradHess {dt*1000:.0f}ms")
print("[REAL] g_p2p=",ghR['gp'].round(4)," |g|=",np.linalg.norm(ghR['gp']).round(4))
print("[REAL] g_p2l=",ghR['gl'].round(4)," |g|=",np.linalg.norm(ghR['gl']).round(4))
print("       eig(Hp2p)=",np.linalg.eigvalsh(ghR['Hp']).round(2))
t0=time.perf_counter(); M.landscape(obj,P); print("landscape %.0fms"%((time.perf_counter()-t0)*1000))
t0=time.perf_counter(); a=M.local_min_p2p(obj,P); b=M.local_min_p2l(obj,P)
print(f"localopt both {(time.perf_counter()-t0)*1000:.0f}ms  p2p xi*={a['xi'][:3].round(4)} rot={np.degrees(a['xi'][3:]).round(3)}")
print(f"                               p2l xi*={b['xi'][:3].round(4)} rot={np.degrees(b['xi'][3:]).round(3)}")
# FD step stability for real scan
for ht,hr in zip(M.FD_T_TRY,M.FD_R_TRY):
    g2=M.grad_hess(obj,P,ht,hr)
    print(f"  step ht={ht*1000}mm hr={np.degrees(hr):.3f}d |gp|={np.linalg.norm(g2['gp']):.5f} |gl|={np.linalg.norm(g2['gl']):.5f} cos_gp={M.cosine(ghR['gp'],g2['gp']):.4f}")
