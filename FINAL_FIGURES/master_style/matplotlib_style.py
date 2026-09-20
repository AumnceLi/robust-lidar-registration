"""Shared print style. All dimensions and font sizes are final-print sizes."""
import matplotlib as mpl
COLORS = {'Raw':'#4D4D4D','Huber':'#4C78A8','Trim':'#9DB4CA','DBS':'#F58518',
          'Global':'#A7B3A8','Patch':'#1B9E77','Full':'#E45756','Estimated Full':'#E45756',
          'Self-null':'#BDBDBD','p2l':'#79706E'}
MARKERS = {'Raw':'o','Huber':'s','Trim':'^','DBS':'D','Global':'v','Patch':'P','Full':'o','Estimated Full':'o','p2l':'x'}
REGIME_COLORS = ['#4C78A8','#B279A2','#59A14F','#B6992D','#E07B62']
MM = 1/25.4
SINGLE_MM, DOUBLE_MM = 85,178
def apply():
    mpl.rcParams.update({'font.family':'sans-serif','font.sans-serif':['Arial','Liberation Sans','Helvetica'],
      'font.size':8.5,'axes.labelsize':9,'axes.titlesize':9,'xtick.labelsize':8,'ytick.labelsize':8,
      'legend.fontsize':8,'axes.linewidth':.85,'lines.linewidth':1.5,'lines.markersize':4.5,
      'patch.linewidth':.8,'xtick.major.width':.8,'ytick.major.width':.8,
      'axes.spines.top':False,'axes.spines.right':False,'axes.grid':False,
      'figure.facecolor':'white','axes.facecolor':'white','savefig.facecolor':'white',
      'pdf.fonttype':42,'ps.fonttype':42,'svg.fonttype':'path','mathtext.fontset':'dejavusans',
      'savefig.dpi':600,'axes.unicode_minus':False})
