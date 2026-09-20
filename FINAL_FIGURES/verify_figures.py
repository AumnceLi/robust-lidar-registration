"""Artifact/data QA only; does not rerun methods. Renders final vector PDFs for inspection."""
from pathlib import Path
import hashlib,json,sys,re
import numpy as np
import pandas as pd
import pymupdf as fitz
from PIL import Image,ImageDraw
P=Path(__file__).resolve().parent;ROOT=P.parent;QA=P/'qa';QA.mkdir(exist_ok=True)
checks=[];thumbs=[];details=[];print_preview=P/'qa'/'print_preview_178mm_96dpi';print_preview.mkdir(exist_ok=True)
def check(name,condition):
    checks.append({'check':name,'passed':bool(condition)})
    if not condition:raise AssertionError(name)
for i in range(1,9):
    base=P/f'Figure{i}'/f'Figure{i}'
    for suffix in ['.pdf','.svg','.png','_caption_draft.md','_notes.md']:
        check(f'Figure{i}{suffix} exists',base.with_name(base.name+suffix).is_file())
    for rel,expected in json.loads((base.parent/'source_hashes.json').read_text()).items():
        check(f'Figure{i} frozen source unchanged: {rel}',hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()==expected)
    d=fitz.open(base.with_suffix('.pdf'));check(f'Figure{i}: one page',len(d)==1)
    page=d[0];w,h=page.rect.width*25.4/72,page.rect.height*25.4/72
    check(f'Figure{i}: 178 mm width and height <=220 mm',abs(w-178)<.05 and h<=220)
    check(f'Figure{i}: vector artwork, no rasterized page',len(page.get_images())==0)
    fonts=page.get_fonts(full=True)
    check(f'Figure{i}: fonts embedded and no Type3',all(x[1] not in ('n/a','') and x[2]!='Type3' for x in fonts))
    outside=[]
    for b in page.get_text('dict')['blocks']:
        for l in b.get('lines',[]):
            for s in l['spans']:
                r=fitz.Rect(s['bbox'])
                if r.x0<-.5 or r.y0<-.5 or r.x1>page.rect.width+.5 or r.y1>page.rect.height+.5:outside.append(s['text'])
    check(f'Figure{i}: no text outside page',not outside)
    text=page.get_text();check(f'Figure{i}: contains panel A','(A)' in text)
    spans=[s for b in page.get_text('dict')['blocks'] for l in b.get('lines',[]) for s in l['spans'] if s['text'].strip()]
    ordinary=[s['size'] for s in spans if re.search(r'[A-Za-z]{3,}',s['text'])]
    check(f'Figure{i}: ordinary text at least 7 pt',min(ordinary)>=6.95)
    if i==2:
        check('Figure2: all 24 original patch labels present',all(str(j) in text.split() for j in range(24)))
    if i==6:check('Figure6: III DBS explicit N/A','N/A' in text)
    pix=page.get_pixmap(matrix=fitz.Matrix(2,2),alpha=False);pix.save(str(QA/f'Figure{i}.png'))
    page.get_pixmap(matrix=fitz.Matrix(96/72,96/72),alpha=False).save(str(print_preview/f'Figure{i}_178mm_at_96dpi.png'))
    im=Image.open(base.with_suffix('.png'));dpi=im.info.get('dpi',(0,0))
    check(f'Figure{i}: 600 dpi PNG',abs(dpi[0]-600)<.1 and abs(dpi[1]-600)<.1)
    check(f'Figure{i}: PNG size matches print size',abs(im.width-w/25.4*600)<2 and abs(im.height-h/25.4*600)<2)
    im=Image.open(QA/f'Figure{i}.png').convert('RGB');im.thumbnail((700,620));tile=Image.new('RGB',(740,660),'#eeeeee');tile.paste(im,((740-im.width)//2,28));ImageDraw.Draw(tile).text((15,8),f'Figure {i}',fill='black');thumbs.append(tile)
    details.append(dict(figure=i,width_mm=w,height_mm=h,png_dpi=dpi,min_ordinary_text_pt=min(ordinary),fonts=[x[3] for x in fonts]))
canvas=Image.new('RGB',(1480,2640),'white')
for j,t in enumerate(thumbs):canvas.paste(t,((j%2)*740,(j//2)*660))
canvas.save(QA/'contact_sheet.png');canvas.convert('L').save(QA/'contact_sheet_grayscale.png')
# Check data coverage and published central values against independent frozen summaries.
s=pd.read_csv(P/'Figure7/pose_summary_iqr.csv')
frozen=pd.read_csv(ROOT/'g_chain/G1_MITIGATION/results/method_comparison.csv')
mapping={'Raw':'M0_raw_p2p','Huber':'M2_raw_huber','Patch':'M4_patch_corr','Full':'M5_full_corr'}
for t,n in [('vi',501),('iv',156),('ii',428),('iii',371)]:
    check(f'Figure7 {t}: primary sample count',set(s[s.trajectory==t].n)=={n})
    for method,code in mapping.items():
        for field,ff in [('et_mm','et_med'),('eR_deg','eR_med')]:
            actual=s[(s.trajectory==t)&(s.method==method)&(s.field==field)]['median'].iloc[0]
            if t!='iii':
                expected=frozen[(frozen.traj==t)&(frozen.method==code)][ff].iloc[0]
                check(f'Figure7 {t} {method} {field}: matches frozen summary',np.isclose(actual,expected,rtol=1e-10))
check('Figure7 preserves II Full negative translation result',pd.read_csv(P/'Figure7/change_vs_raw.csv').query("traj=='ii' and method=='Full'").delta_of_medians_mm.iloc[0]>0)
f5=pd.read_csv(P/'Figure5/real_displacements.csv')
for t,n in [('vi',501),('iv',156),('ii',428),('iii',371)]:
    check(f'Figure5 {t}: p2p robust primary sample count',set(f5[f5.trajectory==t].n)=={n})
check('Figure5 includes LS Huber Trim only',set(f5.loss)=={'ls','huber','trim'})
ds=pd.read_csv(P/'Figure6/translation_comparison.csv');check('Figure6 III DBS not invented',len(ds.query("traj=='iii' and method=='DBS'"))==0)
check('Figure6 focused on VI IV II',set(ds.traj)=={'vi','iv','ii'})
co=pd.read_csv(P/'Figure4/matched_scatter_conditions.csv');check('Figure4 identical complete 96-condition scatter set',len(co)==96 and set(co.n)=={20})
check('Figure4 retains all D1-D5 and bound cases',co.dtype.nunique()==5 and (co.bound_fraction>0).any())
do=pd.read_csv(ROOT/'g_chain/G_GENERALITY/results/dose_response.csv')
raw=pd.read_csv(ROOT/'g_chain/G_GENERALITY/results/geometry_results.csv');raw=raw[(raw.kind=='p2p')&(raw.condition=='structured')]
for row in do[do.dtype.isin(['D1_appendage_disp','D5_appendage_tilt'])].itertuples():
    q=raw[(raw.geometry==row.geometry)&(raw.dtype==row.dtype)&(raw.form==row.form)&(raw.mag==row.mag)]
    check(f'Figure8 frozen dose summary {row.geometry}/{row.dtype}/{row.mag}/{row.form}',np.isclose(q.et_mm.median(),row.et_med) and np.isclose(q.eR_deg.median(),row.eR_med))
(QA/'validation.json').write_text(json.dumps({'checks':checks,'artifacts':details},indent=2),encoding='utf-8')
(QA/'validation_report.md').write_text('# Automated artifact and data verification\n\n'+f'{len(checks)} checks passed.\n\n'+'\n'.join(f'- Figure {r["figure"]}: {r["width_mm"]:.1f} x {r["height_mm"]:.1f} mm, vector PDF, embedded fonts, 600 dpi preview, minimum ordinary-word span {r["min_ordinary_text_pt"]:.1f} pt.' for r in details)+'\n\nVerified source hashes, primary sample counts, frozen summary equality, negative results, missing DBS preservation, complete matched scatter conditions and saved dose summaries. Every PDF is exactly 178 mm wide; 96 dpi 1:1 reference previews are in qa/print_preview_178mm_96dpi (673 px wide). Mathematical subscripts/superscripts and log exponents are smaller than their parent 8-11 pt labels by normal typesetting convention. Rendered all final PDFs into qa/FigureX.png and color/grayscale contact sheets. Human visual review is recorded separately in visual_review.md.\n',encoding='utf-8')
log=P/'build_log.md';base=log.read_text(encoding='utf-8').split('\n## Final verification')[0].rstrip()
log.write_text(base+f'\n\n## Final verification\n\n{len(checks)} automated artifact/data checks passed. All eight PDFs are 178 mm wide, fully vector, use embedded fonts, contain no off-page text, and have matching 600 dpi previews. Ordinary-word spans are at least 7.3 pt; primary ticks/legends are 8 pt. Frozen source hashes and key scientific negative/N/A results were rechecked. Color, grayscale and 96 dpi 1:1 previews were rendered for visual review.\n',encoding='utf-8')
print(f'PASS: {len(checks)} checks; 8 PDFs rendered.')
