"""Build the six-page review PDF and standalone IEEEtran LaTeX source."""
import html
import hashlib
import json
import re
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Preformatted, Spacer, PageBreak, KeepInFrame, Table, TableStyle, BalancedColumns
from reportlab.graphics.shapes import Drawing, Rect, Line, String, Polygon, PolyLine

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT/'output/pdf'
OUT.mkdir(parents=True, exist_ok=True)
data = json.loads((HERE/'workflow_timing_results.json').read_text())
benchmark = json.loads((HERE/'trajectory_benchmark_results.json').read_text())
for snapshot in [data, benchmark]:
    for filename, digest in snapshot['metadata']['sha256'].items():
        actual = hashlib.sha256((ROOT/filename).read_text(encoding='utf-8').encode('utf-8')).hexdigest()
        if actual != digest:
            raise ValueError(f'Evidence snapshot is stale: {filename}')
sample = (HERE/'sample_contract.json').read_text().strip()
policies = ['none','operation_only','no_history','count_only','intentguard']
result_rows = [['Policy','Agreement','Unauth.','Auth.']]
for label, policy in zip(['No guard','Operation only','No history','Count only','IntentGuard'],policies):
    row=benchmark['summary'][policy]
    result_rows.append([label,f"{row['matched_decisions']}/{row['actions']}",str(row['unauthorized_executions']),f"{row['authorized_executions']}/{row['authorized_actions']}"])
outcome_rows = [['Separate proposal','History h','Decision'],['Read invoice_123','0','ALLOW'],['Read payroll','0','BLOCK'],['Send to external address','0','BLOCK'],['Send to user@example.com','0','CONFIRM'],['Read invoice_123','2','BLOCK']]
source = (HERE/'IntentGuard_IEEE_Draft.md').read_text(encoding='utf-8')
source = source.replace('Z. Zhan et al.', 'Q. Zhan, Z. Liang, Z. Ying, and D. Kang')
(HERE/'IntentGuard_IEEE_Draft.md').write_text(source, encoding='utf-8')
W = 252
styles = {
 'body': ParagraphStyle('body', fontName='Times-Roman',fontSize=10,leading=11.6,alignment=TA_JUSTIFY,firstLineIndent=10,spaceAfter=4),
 'abstract': ParagraphStyle('abstract',fontName='Times-Bold',fontSize=9,leading=10.4,alignment=TA_JUSTIFY,spaceAfter=7),
 'h1': ParagraphStyle('h1',fontName='Times-Roman',fontSize=10,leading=12,alignment=TA_CENTER,spaceBefore=10,spaceAfter=6,keepWithNext=True),
 'h2': ParagraphStyle('h2',fontName='Times-Italic',fontSize=10,leading=11.6,spaceBefore=6,spaceAfter=4,keepWithNext=True),
 'caption': ParagraphStyle('caption',fontName='Times-Roman',fontSize=8,leading=9.2,spaceBefore=4,spaceAfter=8),
 'ref': ParagraphStyle('ref',fontName='Times-Roman',fontSize=8,leading=9.2,spaceAfter=4,leftIndent=12,firstLineIndent=-12),
 'small': ParagraphStyle('small',fontName='Times-Roman',fontSize=8,leading=9.4),
}
def p(text, style='body'):
    return Paragraph(html.escape(text), styles[style])
def txt(d,x,y,s,size=8,anchor='middle'):
    d.add(String(x,y,s,fontName='Times-Roman',fontSize=size,textAnchor=anchor))
def arrow(d,x1,y1,x2,y2):
    d.add(Line(x1,y1,x2,y2,strokeWidth=.7))
    if y1==y2:
        direction=1 if x2>x1 else -1
        pts=[x2,y2,x2-direction*4,y2-2,x2-direction*4,y2+2]
    else:
        direction=1 if y2>y1 else -1
        pts=[x2,y2,x2-2,y2-direction*4,x2+2,y2-direction*4]
    d.add(Polygon(pts,fillColor=colors.black,strokeColor=colors.black))
def box(d,x,y,w,h,lines,dashed=False):
    d.add(Rect(x,y,w,h,fillColor=colors.white,strokeColor=colors.black,strokeWidth=.7,strokeDashArray=[3,2] if dashed else None))
    for i,s in enumerate(lines): txt(d,x+w/2,y+h/2+(len(lines)-1)*4.5-i*9-2.5,s)
def architecture():
    d=Drawing(W,205)
    box(d,4,164,243,31,['Proposed: natural-language compiler -> host validation','Current: manually supplied structured contract'],dashed=True)
    arrow(d,54,164,54,149)
    box(d,4,121,100,28,['Host-supplied contract','validated policy object'])
    box(d,147,121,100,28,['Agent proposal','normalized action'])
    box(d,41,74,170,28,['Registry + predicate + trajectory state','GuardedRuntime with task lock'])
    arrow(d,54,121,105,102); arrow(d,197,121,147,102)
    box(d,6,24,73,27,['BLOCK','no execution'])
    box(d,91,24,73,27,['CONFIRM','suspend'])
    box(d,176,24,73,27,['ALLOW','charge + execute'])
    arrow(d,95,74,42,51); arrow(d,127,74,127,51); arrow(d,157,74,212,51)
    txt(d,126,6,'Implemented paths; authenticated approval remains future work',7)
    return d
def flow():
    d=Drawing(W,151)
    box(d,22,113,145,26,['Adapter / operand / contract','budget / sequence violation?'])
    box(d,183,115,64,22,['BLOCK'])
    arrow(d,167,126,183,126); txt(d,175,132,'yes',7)
    box(d,22,62,145,27,['Trusted side effect','requires confirmation?'])
    arrow(d,94,113,94,89); txt(d,103,98,'no',7)
    box(d,183,64,64,22,['CONFIRM'])
    arrow(d,167,76,183,76); txt(d,175,82,'yes',7)
    box(d,62,12,64,22,['ALLOW']); arrow(d,94,62,94,34); txt(d,103,45,'no',7)
    return d
def axes(d, xlabel, ylabel, ylim, yticks):
    x0,y0,x1,y1=38,29,239,115
    for v in yticks:
        y=y0+(y1-y0)*v/ylim
        d.add(Line(x0,y,x1,y,strokeColor=colors.Color(.85,.85,.85),strokeWidth=.4))
        txt(d,33,y-2,f'{v:g}',7,'end')
    d.add(Line(x0,y0,x1,y0)); d.add(Line(x0,y0,x0,y1))
    txt(d,139,3,xlabel,8); txt(d,38,128,ylabel,8,'start')
    return x0,y0,x1,y1
def comparison():
    d=Drawing(W,142); x0,y0,x1,y1=axes(d,'Policy','Unauthorized mock executions (lower is better)',24,[0,6,12,18,24])
    for i,policy in enumerate(policies):
        score=benchmark['summary'][policy]['unauthorized_executions']
        x=43+i*40; h=score/24*(y1-y0)
        d.add(Rect(x,y0,25,h,fillColor=colors.Color(.25+i*.13,.25+i*.13,.25+i*.13),strokeColor=colors.black,strokeWidth=.5))
        txt(d,x+12.5,y0+h+4,str(score),8)
        txt(d,x+12.5,18,['None','Op.','No hist.','Count','Full'][i],7)
    return d
def percentile_plot(conditions, labels, xlabel):
    d=Drawing(W,142); x0,y0,x1,y1=axes(d,xlabel,'Three-call workflow latency (microseconds)',60,[0,20,40,60])
    for j,q in enumerate(['p50','p95','p99']):
        pts=[]
        shade=j*.3
        for i,c in enumerate(conditions):
            x=x0+12+i*(x1-x0-24)/(len(conditions)-1)
            y=y0+data['summary_us'][c][q]/60*(y1-y0)
            pts.extend([x,y]);d.add(Rect(x-2,y-2,4,4,fillColor=colors.Color(shade,shade,shade)))
            if j==0:txt(d,x,18,labels[i],7)
        d.add(PolyLine(pts,strokeWidth=1,strokeColor=colors.Color(shade,shade,shade)))
        txt(d,90+j*53,117,q,7)
    return d

def scalability():
    return percentile_plot(['trajectory_'+str(n) for n in [1,10,100,1000,10000]],['1','10','100','1k','10k'],'Allowed-resource entries (log spacing)')

def stability():
    return percentile_plot(['tools_only','static_runtime','trajectory_1'],['Tools','Static','Full'],'Workflow condition')
captions={
 'ARCHITECTURE':'Fig. 1. Proposed compilation (dashed) and implemented execution boundary. Trusted registry metadata and a task lock mediate mock tools. CONFIRM suspends; authenticated approval and resumption remain future work.',
 'FLOW':'Fig. 2. Runtime decision flow after proposal validation. Missing required destinations and hard violations block before confirmation; side effects come from trusted metadata.',
 'COMPARISON':'Fig. 3. Unauthorized mock executions among 22 BLOCK- or CONFIRM-labeled proposals. Full denotes IntentGuard. All policies execute the same 47 authorized proposals.',
 'SCALABILITY':'Fig. 5. Whole-runtime resource-set scaling, with p50 (black), p95 (dark gray), and p99 (light gray). Contracts are preconstructed; histories remain short.',
 'STABILITY':'Fig. 4. Local three-call workflow percentiles over 2,000 samples per condition: p50 (black), p95 (dark gray), p99 (light gray). No LLM or network is involved.',
}
alg = ['Input: contract C, proposal a, trusted registry T', 'State: counts, destinations, sequence index; lock L', '1  Validate proposal; acquire L; reject reentrancy', '2  Derive effects and validate adapter operands', '3  Check static boundaries and global count', '4  Check operation/resource budgets, destinations,', '     and next successful-sequence operation', '5  Apply confirmation after hard constraints', '6  If BLOCK or CONFIRM: trace; return', '7  Charge all budgets; record destination', '8  Execute handler; retain result or exception', '9  Advance sequence only if handler succeeds', '10 Trace outcome; release L on every exit']


def tabular_pdf(rows, widths, caption):
    t=Table([[p(x,'small') for x in row] for row in rows],colWidths=widths)
    t.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,0),(-1,0),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.7,colors.black),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
    return KeepInFrame(W,1000,[p(caption,'caption'),t,Spacer(1,9)],mode='error')

def special_pdf(key):
    if key=='CONTRACT':
        code=Preformatted(sample,ParagraphStyle('json',fontName='Courier',fontSize=7,leading=9))
        return KeepInFrame(W,1000,[p('Listing 1. Worked task authorization contract','caption'),code,Spacer(1,6)],mode='error')
    if key=='OUTCOMES':
        return tabular_pdf(outcome_rows,[145,45,62],'TABLE I. WORKED CONTRACT OUTCOMES')
    if key=='RESULTTABLE':
        return tabular_pdf(result_rows,[85,60,49,58],'TABLE II. DECISION AGREEMENT AND MOCK EXECUTIONS')
    if key=='ALGORITHM':
        lines=[p('Algorithm 1. Guarded execution with shared history','caption')]+[p(s,'small') for s in alg]
        return KeepInFrame(W,1000,lines+[Spacer(1,8)],mode='error')
    if key=='CASETABLE':
        rows=[['Case','Prior count','Expected'],['In-scope read','0','ALLOW'],['Prohibited send','0','BLOCK'],['Resource drift','0','BLOCK'],['Count violation','2','BLOCK']]
        t=Table([[p(x,'small') for x in row] for row in rows],colWidths=[117,60,75])
        t.setStyle(TableStyle([('LINEABOVE',(0,0),(-1,0),.7,colors.black),('LINEBELOW',(0,0),(-1,0),.5,colors.black),('LINEBELOW',(0,-1),(-1,-1),.7,colors.black),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),3),('RIGHTPADDING',(0,0),(-1,-1),3)]))
        return KeepInFrame(W,1000,[p('TABLE I. FOUR DIAGNOSTIC CONDITIONS','caption'),t,Spacer(1,9)],mode='error')
    drawing=globals()[key.lower()]()
    return KeepInFrame(W,1000,[drawing,p(captions[key],'caption')],mode='error')

parts=source.split('<!-- PAGE -->')
story=[]
for page,part in enumerate(parts):
    blocks=[b.strip() for b in part.strip().split('\n\n') if b.strip()]
    flowables=[]
    abstract=False
    algorithm_column_split=None
    for block in blocks:
        if page==2 and block=="[[FLOW]]": algorithm_column_split=len(flowables)
        if block.startswith('# '):
            story.append(Paragraph(html.escape(block[2:]),ParagraphStyle('title',fontName='Times-Roman',fontSize=23,leading=26,alignment=TA_CENTER,spaceAfter=15)))
        elif block.startswith('Prabhu '):
            story.append(Paragraph('Prabhu Sivapunniyam<br/><i>Independent Researcher</i>',ParagraphStyle('author',fontName='Times-Roman',fontSize=11,leading=13,alignment=TA_CENTER,spaceAfter=22)))
        elif block=='## Abstract': abstract=True
        elif abstract:
            flowables.append(p('Abstract - '+block,'abstract'));abstract=False
        elif block.startswith('**Index Terms:'):
            flowables.append(p(block.replace('**',''),'abstract'))
        elif block.startswith('### '):flowables.append(p(block[4:],'h2'))
        elif block.startswith('## '):flowables.append(p(block[3:].upper(),'h1'))
        elif block.startswith('[['):flowables.append(special_pdf(block[2:-2]))
        elif re.match(r'^\[\d\]',block):flowables.append(p(block,'ref'))
        else:flowables.append(p(block))
    if algorithm_column_split is not None:
        columns=Table([[flowables[:algorithm_column_split],flowables[algorithm_column_split:]]],colWidths=[267,267])
        columns.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),15),('TOPPADDING',(0,0),(-1,-1),0),('BOTTOMPADDING',(0,0),(-1,-1),0)]))
        story.append(columns)
    else:
        story.append(BalancedColumns(flowables,nCols=2,innerPadding=18,leftPadding=0,rightPadding=0,needed=40,spaceAfter=0))
    if page<len(parts)-1:story.append(PageBreak())
pdf=OUT/'IntentGuard_IEEE_6Page_Reviewed.pdf'
doc=SimpleDocTemplate(str(pdf),pagesize=(612,792),rightMargin=39,leftMargin=39,topMargin=47,bottomMargin=43,title='IntentGuard: Stateful Task-Scoped Authorization for AI Agent Trajectories',author='Prabhu Sivapunniyam')
doc.build(story)

def esc(t):
    return ''.join({'&':r'\&','%':r'\%','$':r'\$','#':r'\#','_':r'\_','{':r'\{','}':r'\}','~':r'\textasciitilde{}','^':r'\textasciicircum{}','<':r'\textless{}','>':r'\textgreater{}'}.get(c,c) for c in t)
def latex_figure(key):
    if key=='CONTRACT':
        return '\\begin{center}\n\\begin{minipage}{\\columnwidth}\n\\scriptsize\\textbf{Listing 1. Worked task contract}\n\\begin{verbatim}\n'+sample+'\n\\end{verbatim}\n\\end{minipage}\n\\end{center}\n'
    if key in ['OUTCOMES','RESULTTABLE']:
        rows=outcome_rows if key=='OUTCOMES' else result_rows
        caption='Worked contract outcomes' if key=='OUTCOMES' else 'Decision agreement and mock executions'
        columns=r'p{.53\columnwidth}cc' if key=='OUTCOMES' else 'lccc'
        result='\\begin{table}[ht]\n\\caption{'+caption+'}\\centering\\scriptsize\n\\begin{tabular}{'+columns+'}\\hline\n'
        result+=' \\\\\n'.join(' & '.join(esc(cell) for cell in row) for row in rows)
        return result+' \\\\\\hline\n\\end{tabular}\\end{table}\n'
    if key=='ALGORITHM':
        return '\\begin{center}\n\\begin{minipage}{.98\\columnwidth}\n\\small\\textbf{Algorithm 1. Guarded execution}\\par\n'+'\n'.join(esc(s)+r'\par' for s in alg)+'\n\\end{minipage}\n\\end{center}\n'
    if key=='CASETABLE':
        return r'''\begin{table}[ht]
\caption{Four diagnostic conditions}\centering\small
\begin{tabular}{lcc}\hline Case & Prior count & Expected\\\hline
In-scope read & 0 & ALLOW\\ Prohibited send & 0 & BLOCK\\
Resource drift & 0 & BLOCK\\ Count violation & 2 & BLOCK\\\hline
\end{tabular}\end{table}
'''
    if key in ['ARCHITECTURE','FLOW']:
        d=globals()[key.lower()]()
        cmds=[]
        for s in d.contents:
            if isinstance(s,Rect):
                dash=',dashed' if s.strokeDashArray else ''
                cmds.append(f'\\draw[line width=.5pt{dash}] ({s.x},{s.y}) rectangle ({s.x+s.width},{s.y+s.height});')
            elif isinstance(s,Line):cmds.append(f'\\draw[line width=.5pt] ({s.x1},{s.y1}) -- ({s.x2},{s.y2});')
            elif isinstance(s,Polygon):
                pts=' -- '.join(f'({s.points[i]},{s.points[i+1]})' for i in range(0,len(s.points),2))
                cmds.append('\\fill '+pts+' -- cycle;')
            elif isinstance(s,String):cmds.append(f'\\node[anchor=base,font=\\fontsize{{{s.fontSize}}}{{9}}\\selectfont] at ({s.x},{s.y}) {{{esc(s.text)}}};')
        graphic='\\begin{tikzpicture}[x=1pt,y=1pt]\n'+'\n'.join(cmds)+'\n\\end{tikzpicture}'
    else:
        opt=r'width=\columnwidth,height=1.75in,scale only axis=false,tick label style={font=\scriptsize},label style={font=\scriptsize},ymajorgrids=true,grid style={gray!25},ymin=0,'
        if key=='COMPARISON':
            opt+=r'ymax=24,ytick={0,6,12,18,24},ylabel={Unauthorized mock executions},symbolic x coords={None,Op. only,No hist.,Count,Full},xtick=data,ybar,bar width=14pt,nodes near coords,'
            vals=' '.join(f"({label},{benchmark['summary'][policy]['unauthorized_executions']})" for label,policy in zip(['None','Op. only','No hist.','Count','Full'],policies))
            plot=r'\addplot[fill=gray!50,draw=black] coordinates {'+vals+'};'
        else:
            opt+=r'ymax=60,ytick={0,20,40,60},ylabel={Workflow latency ($\mu$s)},legend style={font=\tiny},'
            if key=='SCALABILITY':
                conditions=['trajectory_'+str(n) for n in [1,10,100,1000,10000]]
                xs=[1,10,100,1000,10000]
                opt+=r'xlabel={Allowed-resource entries},xmode=log,xtick={1,10,100,1000,10000},'
            else:
                conditions=['tools_only','static_runtime','trajectory_1'];xs=[1,2,3]
                opt+=r'xtick={1,2,3},xticklabels={Tools,Static,Full},'
            plot=''
            for q,color in zip(['p50','p95','p99'],['black','black!70','black!40']):
                vals=' '.join(f"({x},{data['summary_us'][c][q]})" for x,c in zip(xs,conditions))
                plot+=r'\addplot['+color+r',mark=square*] coordinates {'+vals+r'};\addlegendentry{'+q+'}'
        graphic='\\begin{tikzpicture}\n\\begin{axis}['+opt+']\n'+plot+'\n\\end{axis}\n\\end{tikzpicture}'
    cap=re.sub(r'^Fig\. \d\. ','',captions[key])
    return '\\begin{figure}[ht]\n\\centering\n'+graphic+'\n\\caption{'+esc(cap)+'}\n\\end{figure}\n'

tex=[r'''\documentclass[conference,letterpaper]{IEEEtran}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{tikz}
\usepackage{pgfplots}
\pgfplotsset{compat=1.18}
\usepackage{url}
\usepackage[hidelinks]{hyperref}
\interdisplaylinepenalty=2500
\title{IntentGuard: Stateful Task-Scoped Authorization for AI Agent Trajectories}
\author{\IEEEauthorblockN{Prabhu Sivapunniyam}\IEEEauthorblockA{Independent Researcher}}
\begin{document}
\maketitle
''']
abstract=False;refs=False
for page,part in enumerate(parts):
    # Let IEEEtran paginate naturally; the review PDF uses six balanced spreads.
    for block in [b.strip() for b in part.strip().split('\n\n') if b.strip()]:
        if block.startswith('# ') or block.startswith('Prabhu '):continue
        if block=='## Abstract':abstract=True;continue
        if abstract:tex.append('\\begin{abstract}\n'+esc(block)+'\n\\end{abstract}');abstract=False;continue
        if block.startswith('**Index Terms:'):tex.append('\\begin{IEEEkeywords}'+esc(block.replace('**Index Terms:** ','').replace('**',''))+'\\end{IEEEkeywords}');continue
        if block=='## References':refs=True;tex.append(r'\begin{thebibliography}{00}');continue
        if refs:
            m=re.match(r'\[(\d)\] (.*)',block,re.S)
            tex.append(r'\bibitem{ref'+m[1]+'} '+esc(m[2]));continue
        if block.startswith('### '):tex.append('\\subsection{'+esc(re.sub(r'^[A-Z]\. ','',block[4:]))+'}');continue
        if block.startswith('## '):tex.append('\\section{'+esc(re.sub(r'^[IVX]+\. ','',block[3:]))+'}');continue
        if block.startswith('[['):tex.append(latex_figure(block[2:-2]));continue
        text=esc(block)
        text=re.sub(r'\[(\d)\]',lambda m:r'\cite{ref'+m[1]+'}',text)
        tex.append(text+'\n')
tex.extend([r'\end{thebibliography}',r'\end{document}'])
(HERE/'IntentGuard_IEEE_Draft.tex').write_text('\n\n'.join(tex)+'\n',encoding='utf-8')
print(pdf)
print(HERE/'IntentGuard_IEEE_Draft.tex')
