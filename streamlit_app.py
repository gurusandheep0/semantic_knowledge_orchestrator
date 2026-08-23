from __future__ import annotations

from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st

from app.models import DocumentSummary, QueryResponse
from app.services.integrations import integration_statuses
from app.services.parser import DocumentParseError
from app.services.rag import RAGEngine, bootstrap_demo


st.set_page_config(page_title="PrismRAG — Document Intelligence", page_icon="◆", layout="wide", initial_sidebar_state="expanded")


@st.cache_resource
def get_engine() -> RAGEngine:
    return bootstrap_demo()


engine = get_engine()


st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700&display=swap');
:root {
  --ink:#18181b; --muted:#77747a; --line:#e7e2e3; --canvas:#f6f4f4; --white:#fff;
  --midnight:#08080a; --midnight-2:#17171a; --violet:#dc2638; --violet-soft:#fff0f1;
  --cyan:#ff4d5e; --cyan-soft:#fff1f2; --magenta:#a81424; --magenta-soft:#fbeaec;
  --amber:#3f3f46; --amber-soft:#efeff0; --blue:#262629; --blue-soft:#ececee;
}
html,body,[class*="css"] { font-family:'DM Sans',sans-serif; }
body { color:var(--ink); }
.stApp { position:relative; background:#f4f0f1; }
#MainMenu,footer,[data-testid="stHeader"] { visibility:hidden; }
[data-testid="stAppViewContainer"] {
  position:relative; isolation:isolate;
  background:
    radial-gradient(circle at 14% 9%,rgba(220,38,56,.11),transparent 25%),
    radial-gradient(circle at 88% 72%,rgba(8,8,10,.065),transparent 31%),
    linear-gradient(135deg,#faf8f8 0%,#f3eeef 52%,#faf8f8 100%);
}
[data-testid="stAppViewContainer"]::before {
  content:''; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.75;
  background-image:
    linear-gradient(rgba(113,27,39,.035) 1px,transparent 1px),
    linear-gradient(90deg,rgba(113,27,39,.035) 1px,transparent 1px),
    radial-gradient(circle,rgba(168,20,36,.11) 1px,transparent 1.6px);
  background-size:52px 52px,52px 52px,26px 26px;
  -webkit-mask-image:linear-gradient(to bottom,rgba(0,0,0,.78),transparent 92%);
  mask-image:linear-gradient(to bottom,rgba(0,0,0,.78),transparent 92%);
  animation:mesh-drift 26s linear infinite;
}
[data-testid="stAppViewContainer"]::after {
  content:''; position:fixed; width:510px; height:510px; right:-170px; top:90px; z-index:0; pointer-events:none;
  border-radius:46% 54% 58% 42%;
  background:radial-gradient(circle at 42% 42%,rgba(255,77,94,.15),rgba(168,20,36,.065) 42%,transparent 70%);
  filter:blur(8px); animation:ambient-float 13s ease-in-out infinite alternate;
}
[data-testid="stAppViewContainer"] > .main { position:relative; z-index:1; background:transparent; }
.main .block-container { position:relative; max-width:1500px; padding:34px 38px 55px; }
h1,h2,h3,.brand-name { font-family:'Manrope',sans-serif!important; letter-spacing:-.035em; }

@keyframes mesh-drift { to { background-position:52px 52px,52px 52px,26px 26px; } }
@keyframes ambient-float {
  0% { transform:translate3d(0,-14px,0) rotate(0deg) scale(.94); opacity:.65; }
  100% { transform:translate3d(-85px,120px,0) rotate(18deg) scale(1.14); opacity:1; }
}
@keyframes glow-pulse { 0%,100%{box-shadow:0 0 0 0 rgba(255,77,94,.38)} 50%{box-shadow:0 0 0 6px rgba(255,77,94,0)} }
@keyframes gem-breathe { 0%,100%{transform:translateY(0);box-shadow:0 10px 26px rgba(220,38,56,.30)} 50%{transform:translateY(-2px);box-shadow:0 14px 32px rgba(220,38,56,.48)} }
@keyframes orbit-drift { from{transform:translate3d(0,0,0) scale(1)} to{transform:translate3d(-28px,24px,0) scale(1.08)} }
@keyframes haze-drift { from{transform:translateX(0) scale(.95);opacity:.55} to{transform:translateX(85px) scale(1.18);opacity:1} }
@keyframes card-arrive { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
@keyframes arrow-flow { 0%,100%{opacity:.28;transform:translateX(-2px)} 50%{opacity:1;transform:translateX(2px)} }

/* Sidebar */
[data-testid="stSidebar"] { width:248px!important; background:var(--midnight); border-right:1px solid rgba(255,255,255,.06); }
[data-testid="stSidebar"] > div:first-child { width:248px!important; padding:22px 17px; }
[data-testid="stSidebar"] * { color:#e4dfe0; }
[data-testid="stSidebar"] .stMarkdown { margin:0; }
.brand { display:flex; align-items:center; gap:11px; padding:6px 5px 24px; }
.brand-gem { position:relative; display:grid; width:38px; height:38px; place-items:center; border-radius:12px; color:white; font-size:16px; font-weight:700; background:linear-gradient(145deg,#ff5967,var(--violet) 55%,#740d19); box-shadow:0 10px 26px rgba(220,38,56,.36); overflow:hidden; animation:gem-breathe 5s ease-in-out infinite; }
.brand-gem:after { content:''; position:absolute; width:17px; height:17px; right:-5px; top:-4px; border-radius:5px; transform:rotate(35deg); background:rgba(255,255,255,.34); }
.brand-name { color:white; font-size:18px; font-weight:700; }
.brand-sub { margin-top:2px; color:#8f8587; font-size:7px; letter-spacing:.22em; text-transform:uppercase; }
.workspace-card { display:flex; align-items:center; gap:10px; margin-bottom:20px; padding:10px; border:1px solid rgba(255,255,255,.08); border-radius:11px; background:rgba(255,255,255,.045); }
.workspace-icon { display:grid; width:34px; height:34px; place-items:center; border-radius:9px; background:linear-gradient(145deg,#3a191d,#651c26); color:#ff7782!important; font-size:11px; }
.workspace-title { color:#fff6f6!important; font-size:10px; font-weight:600; }
.workspace-copy { color:#8e8083!important; font-size:7.5px; margin-top:2px; }
.nav-label { margin:0 8px 7px; color:#675b5d!important; font-size:7px; font-weight:700; letter-spacing:.19em; text-transform:uppercase; }
[data-testid="stSidebar"] .stRadio > label { display:none; }
[data-testid="stSidebar"] .stRadio > div { gap:4px; }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] { min-height:39px; margin:0; padding:9px 10px; border-radius:8px; color:#a69b9d; font-size:10px; }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"]:has(input:checked) { color:white; background:linear-gradient(100deg,rgba(220,38,56,.38),rgba(255,77,94,.08)); box-shadow:inset 3px 0 0 var(--cyan); }
[data-testid="stSidebar"] .stRadio label[data-baseweb="radio"] > div:first-child { display:none; }
.engine-card { margin-top:24px; padding:14px; border:1px solid rgba(255,77,94,.20); border-radius:12px; background:linear-gradient(145deg,rgba(220,38,56,.17),rgba(116,13,25,.10)); }
.engine-orb { display:grid; width:31px; height:31px; place-items:center; margin-bottom:12px; border-radius:9px; color:white!important; background:linear-gradient(145deg,var(--cyan),var(--violet)); font-weight:700; box-shadow:0 0 22px rgba(220,38,56,.30); }
.engine-card strong { display:block; color:#fff4f5!important; font-size:9px; }
.engine-card p { margin:7px 0 10px; color:#9a898c!important; font-size:7.5px; line-height:1.55; }
.live-line { color:#ff7a86!important; font-size:7px; font-weight:600; }
.live-dot { display:inline-block; width:6px; height:6px; margin-right:5px; border-radius:50%; background:var(--cyan); box-shadow:0 0 10px var(--cyan); animation:glow-pulse 2.4s ease-out infinite; }
.profile { display:flex; align-items:center; gap:9px; margin-top:18px; padding:15px 5px 0; border-top:1px solid rgba(255,255,255,.07); }
.profile-avatar { display:grid; width:30px; height:30px; place-items:center; border-radius:9px; color:white!important; background:linear-gradient(145deg,#e93546,#73111c); font-size:7px; font-weight:700; }
.profile strong { display:block; color:#fff3f4!important; font-size:8px; }
.profile span { color:#77696c!important; font-size:7px; }

/* Page chrome */
.page-header { display:flex; justify-content:space-between; gap:20px; align-items:flex-start; margin-bottom:22px; }
.eyebrow { display:flex; align-items:center; gap:7px; margin-bottom:11px; color:#8c8385; font-size:7px; font-weight:700; letter-spacing:.20em; text-transform:uppercase; }
.eyebrow:before { content:''; width:7px; height:7px; border-radius:2px; background:linear-gradient(135deg,#ff6674,#b00f20); transform:rotate(45deg); }
.page-header h1 { margin:0; color:var(--ink); font-size:31px; line-height:1.1; font-weight:700; }
.page-copy { margin:10px 0 0; color:var(--muted); font-size:10px; }
.header-actions { display:flex; gap:8px; padding-top:2px; }
.header-chip { padding:8px 10px; border:1px solid var(--line); border-radius:8px; background:white; color:#6d6567; font-size:7.5px; box-shadow:0 3px 10px rgba(32,23,25,.03); }
.header-chip .dot { display:inline-block; width:6px; height:6px; margin-right:5px; border-radius:50%; background:var(--cyan); box-shadow:0 0 7px rgba(220,38,56,.5); animation:glow-pulse 2.4s ease-out infinite; }

/* Overview */
.hero { position:relative; display:grid; grid-template-columns:1.15fr .85fr; min-height:190px; margin-bottom:16px; overflow:hidden; border-radius:17px; background:linear-gradient(125deg,#08080a,#181315 62%,#421019); color:white; box-shadow:0 20px 48px rgba(73,12,21,.16); animation:card-arrive .7s cubic-bezier(.2,.75,.25,1) both; }
.hero:before { content:''; position:absolute; width:280px; height:280px; right:-90px; top:-120px; border-radius:50%; border:40px solid rgba(255,77,94,.09); animation:orbit-drift 9s ease-in-out infinite alternate; }
.hero:after { content:''; position:absolute; width:190px; height:190px; right:130px; bottom:-150px; border-radius:50%; background:rgba(168,20,36,.18); filter:blur(3px); animation:haze-drift 11s ease-in-out infinite alternate; }
.hero-copy { position:relative; z-index:2; padding:28px 30px; }
.hero-kicker { color:var(--cyan); font-size:7px; font-weight:700; letter-spacing:.20em; text-transform:uppercase; }
.hero h2 { max-width:500px; margin:12px 0 10px; color:white; font-size:27px; line-height:1.15; }
.hero p { max-width:530px; margin:0; color:#b2a4a6; font-size:9.5px; line-height:1.6; }
.hero-meta { display:flex; gap:8px; margin-top:20px; }
.hero-pill { padding:7px 9px; border-radius:7px; color:#eadfe0; background:rgba(255,255,255,.07); font-size:7px; }
.hero-pill strong { color:white; }
.hero-visual { position:relative; z-index:2; display:grid; align-content:center; gap:9px; padding:24px 28px 24px 10px; }
.flow-mini { display:grid; grid-template-columns:1fr 20px 1fr; align-items:center; }
.flow-mini .node { padding:11px; border:1px solid rgba(255,255,255,.10); border-radius:10px; background:rgba(255,255,255,.055); }
.flow-mini .node i { display:inline-grid; width:24px; height:24px; margin-right:7px; place-items:center; border-radius:7px; color:var(--midnight); font-style:normal; font-size:8px; font-weight:700; background:var(--cyan); }
.flow-mini .node.magenta i { background:var(--magenta); color:white; }
.flow-mini .node strong { color:#fff3f4; font-size:8px; }
.flow-mini .arrow { color:#72545a; text-align:center; font-size:12px; }
.metric-grid { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin-bottom:16px; }
.metric { position:relative; min-height:95px; padding:16px; overflow:hidden; border:1px solid rgba(231,226,227,.86); border-radius:13px; background:rgba(255,255,255,.91); backdrop-filter:blur(12px); box-shadow:0 7px 21px rgba(55,24,29,.04); animation:card-arrive .55s cubic-bezier(.2,.75,.25,1) both; transition:transform .25s ease,box-shadow .25s ease,border-color .25s ease; }
.metric:nth-child(2){animation-delay:.07s}.metric:nth-child(3){animation-delay:.14s}.metric:nth-child(4){animation-delay:.21s}
.metric:hover { transform:translateY(-3px); border-color:rgba(220,38,56,.22); box-shadow:0 14px 32px rgba(89,25,35,.09); }
.metric:after { content:''; position:absolute; width:46px; height:46px; right:-15px; bottom:-17px; border-radius:50%; background:var(--violet-soft); }
.metric.cyan:after { background:var(--cyan-soft); }.metric.magenta:after{background:var(--magenta-soft)}.metric.amber:after{background:var(--amber-soft)}
.metric-top { display:flex; align-items:center; justify-content:space-between; color:#888083; font-size:7px; }
.metric-icon { display:grid; width:25px; height:25px; place-items:center; border-radius:7px; color:#c81f32; background:var(--violet-soft); font-weight:700; }
.metric.cyan .metric-icon{color:#e13849;background:var(--cyan-soft)}.metric.magenta .metric-icon{color:#8e1421;background:var(--magenta-soft)}.metric.amber .metric-icon{color:#35353a;background:var(--amber-soft)}
.metric-value { margin-top:11px; color:var(--ink); font-family:'Manrope'; font-size:23px; font-weight:700; }
.metric-foot { margin-top:2px; color:#969093; font-size:7px; }
.metric-foot b { color:#5e5557; }
.panel-grid { display:grid; grid-template-columns:1.2fr .8fr; gap:14px; }
.panel { padding:18px; border:1px solid rgba(231,226,227,.88); border-radius:14px; background:rgba(255,255,255,.92); backdrop-filter:blur(12px); box-shadow:0 7px 22px rgba(55,24,29,.035); animation:card-arrive .65s .18s cubic-bezier(.2,.75,.25,1) both; transition:transform .25s ease,box-shadow .25s ease; }
.panel:hover { transform:translateY(-2px); box-shadow:0 14px 34px rgba(89,25,35,.075); }
.panel-head { display:flex; align-items:center; justify-content:space-between; margin-bottom:14px; }
.panel-title { color:var(--ink); font-family:'Manrope'; font-size:12px; font-weight:700; }
.panel-tag { padding:5px 7px; border-radius:6px; color:#bf1e31; background:var(--violet-soft); font-size:6.5px; font-weight:600; }
.pipeline { display:grid; grid-template-columns:1fr 18px 1fr 18px 1fr 18px 1fr 18px 1fr; align-items:center; gap:3px; }
.pipe-node { min-height:72px; padding:10px 8px; border:1px solid var(--line); border-radius:10px; background:#fbf9f9; }
.pipe-node i { display:grid; width:24px; height:24px; margin-bottom:8px; place-items:center; border-radius:7px; color:#bd1d2f; background:var(--violet-soft); font-style:normal; font-size:7px; font-weight:700; }
.pipe-node.cyan i{color:#df3041;background:var(--cyan-soft)}.pipe-node.magenta i{color:#8e1421;background:var(--magenta-soft)}.pipe-node.amber i{color:#343438;background:var(--amber-soft)}
.pipe-node strong { display:block; color:#403a3c; font-size:7.5px; }.pipe-node span{display:block;margin-top:2px;color:#9b9496;font-size:6px}
.pipe-arrow { color:#c8c0c2; text-align:center; animation:arrow-flow 2.2s ease-in-out infinite; }
.activity { display:flex; align-items:flex-start; gap:10px; padding:9px 0; border-bottom:1px solid #f1edee; }
.activity:last-child { border:0; }
.activity-icon { display:grid; min-width:28px; height:28px; place-items:center; border-radius:8px; color:#df3041; background:var(--cyan-soft); font-size:7px; font-weight:700; }
.activity:nth-of-type(3n+1) .activity-icon{color:#8e1421;background:var(--magenta-soft)}.activity:nth-of-type(3n+2) .activity-icon{color:#bd1d2f;background:var(--violet-soft)}
.activity strong { display:block; color:#484143; font-size:7.5px; }.activity p{margin:3px 0 0;color:#9a9395;font-size:6.5px;line-height:1.4}.activity time{margin-left:auto;color:#aaa3a5;font-size:6px;white-space:nowrap}

/* Ask */
.ask-layout { display:grid; grid-template-columns:minmax(0,1.5fr) minmax(270px,.5fr); gap:14px; }
.ask-card { padding:22px; border:1px solid rgba(231,226,227,.88); border-radius:15px; background:rgba(255,255,255,.92); backdrop-filter:blur(12px); box-shadow:0 8px 24px rgba(55,24,29,.04); animation:card-arrive .6s ease both; }
.user-bubble { max-width:77%; margin-left:auto; padding:13px 15px; border-radius:13px 13px 4px 13px; color:white; background:linear-gradient(120deg,#e33445,#a61020); font-size:9px; line-height:1.5; }
.assistant-row { display:flex; gap:10px; margin-top:18px; }
.assistant-avatar { display:grid; min-width:32px; height:32px; place-items:center; border-radius:9px; color:white; background:linear-gradient(145deg,#ff5967,#b01223); font-size:10px; font-weight:700; }
.answer-bubble { flex:1; padding:17px; border:1px solid #e9e3e4; border-radius:4px 13px 13px 13px; background:#fbf9f9; }
.answer-meta { display:flex; justify-content:space-between; align-items:center; margin-bottom:11px; }
.answer-meta strong { color:#383234; font-size:9px; }.answer-badge{padding:5px 7px;border-radius:6px;color:#c02032;background:var(--cyan-soft);font-size:6.5px;font-weight:700}
.answer-text { color:#625b5d; font-size:9.5px; line-height:1.7; }
.answer-stats { display:flex; gap:8px; margin-top:14px; }
.answer-stat { padding:6px 8px; border-radius:7px; color:#81797b; background:white; border:1px solid var(--line); font-size:6.5px; }.answer-stat b{color:#494143}
.composer { margin-top:17px; padding-top:16px; border-top:1px solid var(--line); }
.citation { margin-bottom:9px; padding:12px; border:1px solid var(--line); border-radius:10px; background:rgba(255,255,255,.9); transition:transform .22s ease,border-color .22s ease; }
.citation:hover { transform:translateX(-3px); border-color:rgba(220,38,56,.28); }
.citation-top { display:flex; justify-content:space-between; gap:8px; }.citation strong{color:#413a3c;font-size:8px}.citation-score{color:#c11e31;font-size:7px;font-weight:700}.citation p{margin:7px 0 0;color:#8d8587;font-size:7px;line-height:1.5}.citation small{display:block;margin-top:5px;color:#afa8aa;font-size:6px}
.side-title { margin-bottom:11px; color:#332d2f; font-family:'Manrope'; font-size:11px; font-weight:700; }
.suggestion { margin-bottom:7px; padding:10px; border:1px solid var(--line); border-radius:9px; color:#746c6e; background:#fbf9f9; font-size:7px; line-height:1.45; }

/* Sources */
.source-summary { display:grid; grid-template-columns:repeat(3,1fr); gap:11px; margin-bottom:15px; }
.summary-card { padding:15px; border-radius:12px; color:white; background:linear-gradient(135deg,#09090b,#292426); animation:card-arrive .55s ease both; transition:transform .25s ease,box-shadow .25s ease; }
.summary-card:nth-child(2){animation-delay:.08s}.summary-card:nth-child(3){animation-delay:.16s}.summary-card:hover{transform:translateY(-3px);box-shadow:0 14px 32px rgba(74,11,20,.16)}
.summary-card.cyan{background:linear-gradient(135deg,#6e0e19,#ab1626)}.summary-card.magenta{background:linear-gradient(135deg,#3c090f,#74111d)}
.summary-card span{color:#c1b3b6;font-size:7px}.summary-card strong{display:block;margin-top:8px;font-family:'Manrope';font-size:21px}.summary-card small{color:#a79699;font-size:6.5px}
.upload-shell { margin-bottom:15px; padding:18px; border:1px dashed #d0c4c6; border-radius:13px; background:linear-gradient(120deg,#fff,#fff7f8); }
.doc-row { display:grid; grid-template-columns:38px minmax(180px,1.2fr) minmax(120px,.65fr) 70px 70px 78px; align-items:center; gap:11px; margin-bottom:8px; padding:12px 13px; border:1px solid rgba(231,226,227,.88); border-radius:11px; background:rgba(255,255,255,.91); backdrop-filter:blur(10px); box-shadow:0 4px 14px rgba(55,24,29,.03); transition:transform .22s ease,border-color .22s ease,box-shadow .22s ease; }
.doc-row:hover { transform:translateX(4px); border-color:rgba(220,38,56,.25); box-shadow:0 8px 22px rgba(70,18,26,.07); }
.doc-icon { display:grid; width:35px; height:35px; place-items:center; border-radius:9px; color:#bf1d30; background:var(--violet-soft); font-size:7px; font-weight:700; text-transform:uppercase; }
.doc-row:nth-child(4n+2) .doc-icon{color:#e13748;background:var(--cyan-soft)}.doc-row:nth-child(4n+3) .doc-icon{color:#8d1421;background:var(--magenta-soft)}.doc-row:nth-child(4n+4) .doc-icon{color:#343438;background:var(--amber-soft)}
.doc-main strong{display:block;color:#40393b;font-size:8px}.doc-main span,.doc-cell span{display:block;margin-top:3px;color:#9c9597;font-size:6.5px}.doc-cell strong{color:#5e5658;font-size:7.5px}.status-pill{display:inline-flex!important;align-items:center;gap:4px;padding:5px 7px;border-radius:6px;color:#bd1d30!important;background:var(--cyan-soft);font-size:6px!important;font-weight:700}.status-pill:before{content:'';width:5px;height:5px;border-radius:50%;background:var(--cyan)}

/* Automation */
.automation-shell { position:relative; overflow:hidden; padding:20px; border-radius:16px; background:linear-gradient(135deg,#08080a,#160e10 68%,#350a11); color:white; box-shadow:0 18px 44px rgba(66,10,18,.18); animation:card-arrive .65s ease both; }
.automation-shell:after { content:''; position:absolute; width:230px; height:230px; right:-90px; bottom:-150px; border:35px solid rgba(255,77,94,.07); border-radius:50%; pointer-events:none; animation:orbit-drift 10s ease-in-out infinite alternate-reverse; }
.automation-head { display:flex; justify-content:space-between; align-items:center; margin-bottom:22px; }.automation-head strong{font-family:'Manrope';font-size:12px}.automation-head span{color:#8f7b7e;font-size:7px}
.workflow-lane { display:grid; grid-template-columns:repeat(9,minmax(20px,1fr)); align-items:center; gap:5px; margin:13px 0; }
.workflow-node { position:relative; z-index:1; min-height:74px; padding:10px; border:1px solid rgba(255,255,255,.08); border-radius:10px; background:var(--midnight-2); transition:transform .22s ease,border-color .22s ease,background .22s ease; }
.workflow-node:hover { transform:translateY(-3px); border-color:rgba(255,77,94,.32); background:#21171a; }
.workflow-node i{display:grid;width:25px;height:25px;margin-bottom:8px;place-items:center;border-radius:7px;background:var(--cyan-soft);color:#df3041;font-style:normal;font-size:7px;font-weight:700}.workflow-node.violet i{background:var(--violet-soft);color:#bd1d30}.workflow-node.magenta i{background:var(--magenta-soft);color:#8d1421}.workflow-node.amber i{background:var(--amber-soft);color:#343438}
.workflow-node strong{display:block;color:#fff1f2;font-size:7.5px}.workflow-node span{display:block;margin-top:3px;color:#827174;font-size:6px}.workflow-arrow{color:#624048;text-align:center;font-size:11px;animation:arrow-flow 2.2s ease-in-out infinite}.lane-label{grid-column:1/-1;color:#82686d;font-size:6.5px;font-weight:700;letter-spacing:.16em;text-transform:uppercase}
.integration-grid { display:grid; grid-template-columns:repeat(5,1fr); gap:10px; margin-top:15px; }
.integration { padding:13px; border:1px solid rgba(231,226,227,.88); border-radius:11px; background:rgba(255,255,255,.91); backdrop-filter:blur(10px); transition:transform .22s ease,box-shadow .22s ease; }.integration:hover{transform:translateY(-3px);box-shadow:0 10px 25px rgba(70,18,26,.08)}.integration-icon{display:grid;width:28px;height:28px;margin-bottom:10px;place-items:center;border-radius:8px;background:var(--violet-soft);color:#bd1d30;font-size:7px;font-weight:700}.integration.cyan .integration-icon{background:var(--cyan-soft);color:#df3041}.integration.magenta .integration-icon{background:var(--magenta-soft);color:#8d1421}.integration.amber .integration-icon{background:var(--amber-soft);color:#343438}.integration.blue .integration-icon{background:var(--blue-soft);color:#242428}.integration strong{display:block;color:#413a3c;font-size:8px}.integration p{min-height:22px;margin:5px 0;color:#999294;font-size:6.5px;line-height:1.4}.integration-status{color:#6d6466;font-size:6px;font-weight:700;text-transform:uppercase}

/* Streamlit controls */
.stButton > button { min-height:38px; border:0; border-radius:9px; color:white; background:linear-gradient(110deg,#e33445,#a61020); font-size:9px; font-weight:600; box-shadow:0 8px 18px rgba(220,38,56,.22); }
.stButton > button:hover { color:white; border:0; }
.stButton > button[kind="secondary"] { color:#4a4042; border:1px solid rgba(184,159,164,.42); background:rgba(255,255,255,.88); box-shadow:0 6px 16px rgba(64,23,30,.055); backdrop-filter:blur(10px); }
.stButton > button[kind="secondary"]:hover { color:#b51b2e; border-color:rgba(220,38,56,.32); background:#fff7f8; transform:translateY(-2px); }
.stDownloadButton > button { min-height:38px; width:100%; border-radius:9px; color:#4a4042; border:1px solid rgba(184,159,164,.42); background:rgba(255,255,255,.88); box-shadow:0 6px 16px rgba(64,23,30,.055); font-size:9px; font-weight:600; }
.stDownloadButton > button:hover { color:#b51b2e; border-color:rgba(220,38,56,.32); background:#fff7f8; transform:translateY(-2px); }
.quick-label { display:flex; align-items:center; justify-content:space-between; margin:1px 0 8px; color:#746a6c; font-size:7px; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }
.quick-label span { color:#a69da0; font-size:6px; font-weight:500; letter-spacing:.06em; text-transform:none; }
[data-testid="stFileUploader"] { background:white; border-radius:10px; }
.stTextInput input { min-height:42px; border-color:var(--line); border-radius:9px; font-size:9px; }
.stTextInput input:focus { border-color:var(--violet); box-shadow:0 0 0 1px var(--violet); }
.stAlert { font-size:8px; border-radius:10px; }

@media(prefers-reduced-motion:reduce){
  [data-testid="stAppViewContainer"]::before,[data-testid="stAppViewContainer"]::after,.brand-gem,.live-dot,.header-chip .dot,.hero,.hero:before,.hero:after,.metric,.panel,.summary-card,.ask-card,.automation-shell,.automation-shell:after,.pipe-arrow,.workflow-arrow { animation:none!important; }
  .metric,.panel,.summary-card,.citation,.doc-row,.workflow-node,.integration { transition:none!important; }
}

@media(max-width:1050px){
  .hero{grid-template-columns:1fr}.hero-visual{display:none}.metric-grid{grid-template-columns:repeat(2,1fr)}.panel-grid,.ask-layout{grid-template-columns:1fr}.integration-grid{grid-template-columns:repeat(3,1fr)}
  .doc-row{grid-template-columns:38px 1fr 70px}.doc-row .doc-cell:nth-of-type(2),.doc-row .doc-cell:nth-of-type(3){display:none}
}
@media(max-width:700px){
  .main .block-container{padding:22px 12px 45px}.page-header{display:block}.header-actions{margin-top:16px}.page-header h1{font-size:27px}.metric-grid,.source-summary{grid-template-columns:1fr 1fr}.panel-grid{display:block}.panel{margin-bottom:12px}.pipeline{grid-template-columns:1fr 12px 1fr}.pipeline .pipe-node:nth-of-type(n+4),.pipeline .pipe-arrow:nth-of-type(n+4){display:none}.ask-card{padding:14px}.user-bubble{max-width:92%}.workflow-lane{grid-template-columns:1fr 16px 1fr}.workflow-node:nth-of-type(n+4),.workflow-arrow:nth-of-type(n+4){display:none}.integration-grid{grid-template-columns:1fr 1fr}.doc-row{grid-template-columns:34px 1fr 58px;padding:10px}.doc-row .doc-cell:nth-of-type(4){display:none}
}
</style>
""",
    unsafe_allow_html=True,
)


def format_date(value: str) -> str:
    try:
        return datetime.fromisoformat(value).strftime("%d %b %Y")
    except ValueError:
        return value[:10]


def sidebar() -> str:
    with st.sidebar:
        st.markdown(
            """<div class="brand"><span class="brand-gem">◆</span><div><div class="brand-name">PrismRAG</div><div class="brand-sub">Document intelligence</div></div></div>
            <div class="workspace-card"><span class="workspace-icon">AT</span><div><div class="workspace-title">Atlas Research</div><div class="workspace-copy">Knowledge operations workspace</div></div></div>
            <div class="nav-label">Workspace</div>""",
            unsafe_allow_html=True,
        )
        if "page" not in st.session_state:
            st.session_state.page = "Overview"
        page = st.radio("Navigation", ["Overview", "Ask Prism", "Sources", "Automation"], key="page", label_visibility="collapsed")
        st.markdown(
            """<div class="engine-card"><div class="engine-orb">↗</div><strong>Retrieval engine</strong><p>Evidence-first answers with semantic search, confidence scoring, and traceable citations.</p><div class="live-line"><span class="live-dot"></span>Local vector index online</div></div>
            <div class="profile"><span class="profile-avatar">NK</span><div><strong>Nora Kim</strong><span>Knowledge architect</span></div></div>""",
            unsafe_allow_html=True,
        )
    return page


def page_header(eyebrow: str, title: str, copy: str) -> None:
    st.markdown(
        f"""<div class="page-header"><div><div class="eyebrow">{escape(eyebrow)}</div><h1>{escape(title)}</h1><p class="page-copy">{escape(copy)}</p></div>
        <div class="header-actions"><span class="header-chip"><span class="dot"></span>Retrieval online</span><span class="header-chip">↻ Synced 2 min ago</span></div></div>""",
        unsafe_allow_html=True,
    )


def metric(label: str, value: str, detail: str, icon: str, tone: str = "") -> str:
    return f"""<div class="metric {tone}"><div class="metric-top"><span>{escape(label)}</span><i class="metric-icon">{escape(icon)}</i></div><div class="metric-value">{escape(value)}</div><div class="metric-foot">{detail}</div></div>"""


def go_to(page: str) -> None:
    """Navigate through a widget callback before the next Streamlit rerun."""
    st.session_state.page = page


def run_suggested_question(question: str) -> None:
    """Run a suggested query and keep its result visible on the Ask page."""
    st.session_state.last_answer = engine.answer(question, channel="web")
    st.session_state.page = "Ask Prism"


def refresh_workspace() -> None:
    """Reload cached services while preserving the current navigation page."""
    st.cache_resource.clear()
    st.session_state.pop("last_answer", None)
    st.session_state.refresh_notice = True


def render_overview() -> None:
    if st.session_state.pop("refresh_notice", False):
        st.toast("Workspace refreshed from the local vector index.")
    stats = engine.repository.stats()
    docs = engine.repository.list_documents(limit=5)
    history = engine.repository.list_queries(limit=4)
    page_header("PrismRAG workspace · Live index", "Knowledge control center", "Monitor every document, retrieval, and automation path from one evidence-first workspace.")
    st.markdown(
        """<section class="hero"><div class="hero-copy"><div class="hero-kicker">Document intelligence fabric</div><h2>Your scattered files, transformed into cited answers.</h2><p>PrismRAG continuously converts operational documents into retrieval-ready knowledge, then delivers grounded answers wherever your team already works.</p><div class="hero-meta"><span class="hero-pill"><strong>4</strong> source formats</span><span class="hero-pill"><strong>3</strong> answer channels</span><span class="hero-pill"><strong>100%</strong> traceable</span></div></div>
        <div class="hero-visual"><div class="flow-mini"><div class="node"><i>GD</i><strong>Google Drive</strong></div><div class="arrow">→</div><div class="node magenta"><i>PX</i><strong>Pinecone</strong></div></div><div class="flow-mini"><div class="node"><i>Q</i><strong>Semantic query</strong></div><div class="arrow">→</div><div class="node magenta"><i>TG</i><strong>Telegram answer</strong></div></div></div></section>""",
        unsafe_allow_html=True,
    )
    st.markdown('<div class="quick-label">Quick actions <span>Every control below is live</span></div>', unsafe_allow_html=True)
    action_columns = st.columns(4)
    with action_columns[0]:
        st.button("Ask documents", key="overview-ask", type="primary", use_container_width=True, on_click=go_to, args=("Ask Prism",))
    with action_columns[1]:
        st.button("Upload source", key="overview-source", use_container_width=True, on_click=go_to, args=("Sources",))
    with action_columns[2]:
        st.button("View automation", key="overview-automation", use_container_width=True, on_click=go_to, args=("Automation",))
    with action_columns[3]:
        st.button("Refresh workspace", key="overview-refresh", use_container_width=True, on_click=refresh_workspace)
    st.markdown(
        '<div class="metric-grid">'
        + metric("Indexed documents", str(stats.documents), "<b>4 formats</b> · synced sources", "DOC")
        + metric("Retrieval chunks", f"{stats.chunks:,}", "<b>720 chars</b> · 110 overlap", "VEC", "cyan")
        + metric("Grounded queries", str(stats.queries), "<b>3 channels</b> · web, API, bot", "ASK", "magenta")
        + metric("Avg. confidence", f"{stats.average_confidence:.0f}%", "<b>Cited</b> · evidence threshold", "CF", "amber")
        + "</div>",
        unsafe_allow_html=True,
    )
    pipeline = """<div class="panel"><div class="panel-head"><span class="panel-title">Live retrieval pipeline</span><span class="panel-tag">n8n orchestrated</span></div><div class="pipeline">
    <div class="pipe-node cyan"><i>GD</i><strong>Drive trigger</strong><span>File created</span></div><div class="pipe-arrow">→</div>
    <div class="pipe-node"><i>TX</i><strong>Parse + chunk</strong><span>720 / 110</span></div><div class="pipe-arrow">→</div>
    <div class="pipe-node magenta"><i>EM</i><strong>Embeddings</strong><span>Semantic vectors</span></div><div class="pipe-arrow">→</div>
    <div class="pipe-node amber"><i>PX</i><strong>Pinecone</strong><span>workspace</span></div><div class="pipe-arrow">→</div>
    <div class="pipe-node cyan"><i>TG</i><strong>Answer</strong><span>With citations</span></div></div></div>"""
    activity_html = "".join(
        f"""<div class="activity"><span class="activity-icon">{escape(item.channel[:2].upper())}</span><div><strong>{escape(item.question)}</strong><p>{round(item.confidence * 100)}% confidence · {item.citation_count} cited sources</p></div><time>{format_date(item.created_at)}</time></div>"""
        for item in history
    )
    if not activity_html:
        activity_html = '<div class="activity"><span class="activity-icon">QA</span><div><strong>No queries yet</strong><p>Ask the workspace to start retrieval activity.</p></div></div>'
    st.markdown(f'<div class="panel-grid">{pipeline}<div class="panel"><div class="panel-head"><span class="panel-title">Recent retrievals</span><span class="panel-tag">Grounded</span></div>{activity_html}</div></div>', unsafe_allow_html=True)


def render_ask() -> None:
    page_header("Ask Prism · Evidence mode", "Ask your knowledge base", "Query every indexed document and inspect exactly which passages support the answer.")
    if "last_answer" not in st.session_state:
        st.session_state.last_answer = engine.answer("What is the 2030 emissions reduction target?", channel="web")
    result: QueryResponse = st.session_state.last_answer
    citations = "".join(
        f"""<div class="citation"><div class="citation-top"><strong>[{index}] {escape(item.document_name)}</strong><span class="citation-score">{round(item.score * 100)}% match</span></div><p>{escape(item.excerpt)}</p><small>Page {item.page} · Indexed source</small></div>"""
        for index, item in enumerate(result.citations, start=1)
    )
    if not citations:
        citations = '<div class="suggestion">No sources met the grounding threshold for this question.</div>'
    st.markdown(
        f"""<div class="ask-layout"><div class="ask-card"><div class="user-bubble">{escape(result.question)}</div><div class="assistant-row"><span class="assistant-avatar">◆</span><div class="answer-bubble"><div class="answer-meta"><strong>PrismRAG</strong><span class="answer-badge">Evidence grounded</span></div><div class="answer-text">{escape(result.answer)}</div><div class="answer-stats"><span class="answer-stat"><b>{round(result.confidence * 100)}%</b> confidence</span><span class="answer-stat"><b>{len(result.citations)}</b> sources</span><span class="answer-stat"><b>{result.retrieval_ms} ms</b> retrieval</span></div></div></div>
        <div class="composer"></div></div><div><div class="ask-card"><div class="side-title">Retrieved evidence</div>{citations}</div></div></div>""",
        unsafe_allow_html=True,
    )
    with st.form("question-form", clear_on_submit=False):
        left, right = st.columns([5, 1])
        with left:
            question = st.text_input("Question", placeholder="Ask about a policy, report, or process…", label_visibility="collapsed")
        with right:
            submitted = st.form_submit_button("Ask Prism", use_container_width=True)
        if submitted and question.strip():
            st.session_state.last_answer = engine.answer(question.strip(), channel="web")
            st.rerun()
    st.markdown('<div class="quick-label" style="margin-top:16px">Try a focused question <span>Click once to run retrieval</span></div>', unsafe_allow_html=True)
    suggestions = [
        "How quickly must a critical security incident be acknowledged?",
        "Which approvals apply to a $40,000 vendor purchase?",
        "How many remote-work days are permitted each week?",
    ]
    suggestion_columns = st.columns(3)
    for index, (column, suggestion) in enumerate(zip(suggestion_columns, suggestions)):
        with column:
            st.button(
                suggestion,
                key=f"suggestion-{index}",
                use_container_width=True,
                on_click=run_suggested_question,
                args=(suggestion,),
            )


def document_row(document: DocumentSummary, index: int) -> str:
    return f"""<div class="doc-row"><span class="doc-icon">{escape(document.file_type)}</span><div class="doc-main"><strong>{escape(document.name)}</strong><span>{escape(document.source)}</span></div><div class="doc-cell"><strong>{escape(document.namespace)}</strong><span>Vector namespace</span></div><div class="doc-cell"><strong>{document.pages}</strong><span>Pages</span></div><div class="doc-cell"><strong>{document.chunks}</strong><span>Chunks</span></div><div class="doc-cell"><span class="status-pill">Indexed</span><span>{format_date(document.created_at)}</span></div></div>"""


def render_sources() -> None:
    docs = engine.repository.list_documents()
    stats = engine.repository.stats()
    page_header("Knowledge sources · Vector ready", "Document library", "Ingest, inspect, and manage the trusted sources available to every retrieval channel.")
    st.markdown(
        f"""<div class="source-summary"><div class="summary-card"><span>Indexed files</span><strong>{stats.documents}</strong><small>PDF · DOCX · TXT · MD</small></div><div class="summary-card cyan"><span>Semantic chunks</span><strong>{stats.chunks}</strong><small>Local embeddings + reranking</small></div><div class="summary-card magenta"><span>Storage backend</span><strong style="font-size:15px">{escape(stats.vector_backend)}</strong><small>Workspace namespace healthy</small></div></div>""",
        unsafe_allow_html=True,
    )
    with st.container():
        st.markdown('<div class="upload-shell"><div class="panel-title">Add a trusted source</div><p class="page-copy">Upload a PDF, DOCX, TXT, or Markdown file. Duplicate content is detected automatically.</p>', unsafe_allow_html=True)
        uploaded = st.file_uploader("Document", type=["pdf", "docx", "txt", "md"], label_visibility="collapsed")
        if uploaded and st.button("Parse, embed & index", use_container_width=False):
            try:
                ingested = engine.ingest_bytes(uploaded.getvalue(), uploaded.name)
                if ingested.deduplicated:
                    st.info(f"{uploaded.name} is already indexed.")
                else:
                    st.success(f"Indexed {ingested.chunks_created} chunks from {uploaded.name}.")
                st.cache_resource.clear()
            except (DocumentParseError, ValueError) as exc:
                st.error(str(exc))
        st.markdown('</div>', unsafe_allow_html=True)
    rows = "".join(document_row(document, index) for index, document in enumerate(docs))
    st.markdown(f'<div class="panel-head"><span class="panel-title">All indexed documents</span><span class="panel-tag">{len(docs)} sources</span></div>{rows}', unsafe_allow_html=True)
    st.markdown('<div class="quick-label" style="margin-top:14px">Next step <span>Query all indexed sources</span></div>', unsafe_allow_html=True)
    st.button("Ask these documents", key="sources-ask", type="primary", on_click=go_to, args=("Ask Prism",))


def render_automation() -> None:
    page_header("Automation studio · n8n", "Connected knowledge workflow", "Trace how a Drive upload becomes a vector and how a Telegram question becomes a cited answer.")
    st.markdown(
        """<div class="automation-shell"><div class="automation-head"><strong>PrismRAG production workflow</strong><span>2 triggers · 10 operational nodes · workspace namespace</span></div>
        <div class="workflow-lane"><div class="lane-label">Ingestion lane</div><div class="workflow-node"><i>GD</i><strong>Drive trigger</strong><span>New PDF</span></div><div class="workflow-arrow">→</div><div class="workflow-node violet"><i>DL</i><strong>Download</strong><span>Binary file</span></div><div class="workflow-arrow">→</div><div class="workflow-node magenta"><i>SP</i><strong>Split</strong><span>720 / 110</span></div><div class="workflow-arrow">→</div><div class="workflow-node amber"><i>EM</i><strong>Embed</strong><span>Semantic</span></div><div class="workflow-arrow">→</div><div class="workflow-node violet"><i>PX</i><strong>Pinecone</strong><span>Upsert</span></div></div>
        <div class="workflow-lane"><div class="lane-label">Question-answering lane</div><div class="workflow-node"><i>TG</i><strong>Telegram</strong><span>Message</span></div><div class="workflow-arrow">→</div><div class="workflow-node violet"><i>AI</i><strong>Groq agent</strong><span>Tool use</span></div><div class="workflow-arrow">→</div><div class="workflow-node magenta"><i>SR</i><strong>Retrieve</strong><span>Top 4</span></div><div class="workflow-arrow">→</div><div class="workflow-node amber"><i>CT</i><strong>Citations</strong><span>Grounded</span></div><div class="workflow-arrow">→</div><div class="workflow-node"><i>TX</i><strong>Reply</strong><span>Telegram</span></div></div></div>""",
        unsafe_allow_html=True,
    )
    cards = "".join(
        f"""<div class="integration {escape(item.accent)}"><span class="integration-icon">{escape(item.name[:2].upper())}</span><strong>{escape(item.name)}</strong><p>{escape(item.detail)}</p><span class="integration-status">{escape(item.status.replace('-', ' '))}</span></div>"""
        for item in integration_statuses()
    )
    st.markdown(f'<div class="integration-grid">{cards}</div>', unsafe_allow_html=True)
    workflow_path = Path(__file__).parent / "workflows" / "prismrag-workflow.json"
    st.markdown('<div class="quick-label" style="margin-top:15px">Workflow actions <span>Navigate or export</span></div>', unsafe_allow_html=True)
    workflow_columns = st.columns(3)
    with workflow_columns[0]:
        st.button("Ask indexed documents", key="automation-ask", type="primary", use_container_width=True, on_click=go_to, args=("Ask Prism",))
    with workflow_columns[1]:
        st.button("Add knowledge source", key="automation-source", use_container_width=True, on_click=go_to, args=("Sources",))
    with workflow_columns[2]:
        st.download_button("Download n8n workflow", workflow_path.read_bytes(), file_name="prismrag-workflow.json", mime="application/json", use_container_width=True)


page = sidebar()
if page == "Overview":
    render_overview()
elif page == "Ask Prism":
    render_ask()
elif page == "Sources":
    render_sources()
else:
    render_automation()
