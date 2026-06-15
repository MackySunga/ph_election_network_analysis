const DATA = window.APP_DATA;
const slides = Array.from(document.querySelectorAll('.slide'));
let current = 0;
let networks = {};
let timelineTimer = null;
let timelineIndex = 0;
const tooltip = document.createElement('div');
tooltip.className = 'tooltip';
document.body.appendChild(tooltip);

function fmt(n){
  if(n===null || n===undefined) return '—';
  if(Math.abs(n)>=1_000_000) return (n/1_000_000).toFixed(1)+'M';
  if(Math.abs(n)>=1_000) return (n/1_000).toFixed(1)+'K';
  if(typeof n==='number') return Number.isInteger(n)? n.toLocaleString() : n.toFixed(3);
  return n;
}
function showTip(html,x,y){tooltip.innerHTML=html;tooltip.style.display='block';tooltip.style.left=(x+14)+'px';tooltip.style.top=(y+14)+'px'}
function hideTip(){tooltip.style.display='none'}
function colorFor(i){const colors=['#0b5ed7','#d7263d','#ffc928','#06a5a5','#7c3aed','#16a34a','#f97316','#334155','#ec4899','#14b8a6']; return colors[i%colors.length]}

function initNav(){
  const nav = document.getElementById('slideNav');
  slides.forEach((s,i)=>{
    const b=document.createElement('button'); b.className='navItem'; b.innerHTML=`${String(i+1).padStart(2,'0')} · ${s.dataset.title}`; b.onclick=()=>go(i); nav.appendChild(b);
  });
  document.getElementById('nextBtn').onclick=()=>go(current+1);
  document.getElementById('prevBtn').onclick=()=>go(current-1);
  document.querySelectorAll('[data-next]').forEach(b=>b.onclick=()=>go(current+1));
  document.querySelectorAll('[data-jump]').forEach(b=>b.onclick=()=>go(Number(b.dataset.jump)));
  document.getElementById('menuToggle').onclick=()=>{document.getElementById('slideMenu').classList.toggle('open'); resizeVisibleNetworks();};
  document.addEventListener('keydown',e=>{
    if(e.key==='ArrowRight'||e.key===' '){e.preventDefault();go(current+1)}
    if(e.key==='ArrowLeft'){e.preventDefault();go(current-1)}
    if(e.key.toLowerCase()==='m')document.getElementById('slideMenu').classList.toggle('open');
  });
  updateNav();
}
function go(i){
  if(i<0) i=0; if(i>=slides.length) i=slides.length-1;
  slides[current].classList.remove('active'); current=i; slides[current].classList.add('active');
  updateNav();
  resizeVisibleNetworks();
}

function resizeVisibleNetworks(){
  if(current>=6 && current<=8){
    [60, 220, 520].forEach(delay=>{
      setTimeout(()=>{
        ['candidate','hashtag','bipartite'].forEach(key=>{
          if(networks[key] && networks[key].resize) networks[key].resize();
        });
      }, delay);
    });
  }
}

function updateNav(){
  document.querySelectorAll('.navItem').forEach((b,i)=>b.classList.toggle('active',i===current));
  document.getElementById('slideCounter').textContent=`${current+1} / ${slides.length}`;
  document.getElementById('progressBar').style.width=`${((current+1)/slides.length)*100}%`;
}

function metricCard(label, value){return `<div class="metric"><strong>${value}</strong><span>${label}</span></div>`}
function renderOverview(){
  const s=DATA.summary;
  document.getElementById('overviewMetrics').innerHTML = [
    metricCard('Tweets analyzed', fmt(s.tweets)),
    metricCard('Unique authors', fmt(s.uniqueAuthors)),
    metricCard('Senate candidates', s.candidates),
    metricCard('Hashtag nodes', fmt(s.hashtagNodes)),
    metricCard('Candidate links', fmt(s.candidateEdges)),
    metricCard('Bipartite edges', fmt(s.bipartiteEdges))
  ].join('');
}

function svgEl(tag, attrs={}){const el=document.createElementNS('http://www.w3.org/2000/svg',tag); Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,v)); return el;}
function clear(el){ while(el.firstChild) el.removeChild(el.firstChild); }

function barChart(elId, rows, opts){
  const el=document.getElementById(elId); clear(el); const w=el.clientWidth||700,h=el.clientHeight||500;
  const svg=svgEl('svg',{viewBox:`0 0 ${w} ${h}`, width:'100%', height:'100%'}); el.appendChild(svg);
  const m={l:opts.left||160,r:30,t:30,b:40}; const plotW=w-m.l-m.r, plotH=h-m.t-m.b;
  const data=[...rows]; const max=Math.max(...data.map(d=>Math.abs(+d[opts.value]||0)),1);
  const barH=Math.min(34, plotH/data.length*0.72); const gap=(plotH-data.length*barH)/(data.length+1);
  const zeroX = opts.diverging ? m.l + plotW/2 : m.l;
  data.forEach((d,i)=>{
    const y=m.t+gap+(barH+gap)*i; const val=+d[opts.value]||0;
    const label=String(d[opts.label]);
    const tx=svgEl('text',{x:m.l-10,y:y+barH*0.68,'text-anchor':'end','font-size':12,'font-weight':700,fill:'#17314d'}); tx.textContent=label.length>24?label.slice(0,23)+'…':label; svg.appendChild(tx);
    let x=zeroX, bw;
    if(opts.diverging){ bw=Math.abs(val)/max*(plotW/2); if(val<0) x=zeroX-bw; }
    else { bw=val/max*plotW; }
    const rect=svgEl('rect',{x,y,width:Math.max(2,bw),height:barH,rx:8,fill: val<0?'#d7263d':'#0b5ed7',opacity:.88}); svg.appendChild(rect);
    const tv=svgEl('text',{x: val<0?x-6:x+bw+6,y:y+barH*.68,'font-size':12,'font-weight':800,fill:'#526174','text-anchor':val<0?'end':'start'}); tv.textContent=opts.format?opts.format(val,d):fmt(val); svg.appendChild(tv);
  });
  if(opts.diverging){ svg.appendChild(svgEl('line',{x1:zeroX,x2:zeroX,y1:m.t,y2:h-m.b,stroke:'#334155','stroke-width':1,opacity:.35})); }
}

function scatterChart(elId, rows, opts={}){
  const el=document.getElementById(elId); clear(el); const w=el.clientWidth||720,h=el.clientHeight||520;
  const svg=svgEl('svg',{viewBox:`0 0 ${w} ${h}`, width:'100%', height:'100%'}); el.appendChild(svg);
  const m={l:70,r:40,t:30,b:70}; const plotW=w-m.l-m.r, plotH=h-m.t-m.b;
  const xs=rows.map(d=>+d.twitter_mention_count_rank).filter(Number.isFinite); const ys=rows.map(d=>+d.vote_rank).filter(Number.isFinite);
  const xMax=Math.max(...xs,66), yMax=Math.max(...ys,66), xMin=1, yMin=1;
  const xScale=x=>m.l+(x-xMin)/(xMax-xMin)*plotW; const yScale=y=>m.t+(y-yMin)/(yMax-yMin)*plotH;
  for(let i=0;i<=6;i++){
    const x=m.l+i/6*plotW, y=m.t+i/6*plotH;
    svg.appendChild(svgEl('line',{x1:x,x2:x,y1:m.t,y2:h-m.b,stroke:'#dbe5ef'}));
    svg.appendChild(svgEl('line',{x1:m.l,x2:w-m.r,y1:y,y2:y,stroke:'#dbe5ef'}));
  }
  svg.appendChild(svgEl('line',{x1:xScale(1),y1:yScale(1),x2:xScale(Math.min(xMax,yMax)),y2:yScale(Math.min(xMax,yMax)),stroke:'#ffc928','stroke-width':3,opacity:.8}));
  rows.forEach(d=>{
    if(!Number.isFinite(+d.twitter_mention_count_rank)||!Number.isFinite(+d.vote_rank))return;
    const c=svgEl('circle',{cx:xScale(+d.twitter_mention_count_rank),cy:yScale(+d.vote_rank),r:d.winner_top12?8:5,fill:d.winner_top12?'#0b5ed7':'#d7263d',opacity:.8,stroke:'#fff','stroke-width':1.5});
    c.addEventListener('mousemove',e=>showTip(`<b>${d.candidate}</b><br>Online rank: ${d.twitter_mention_count_rank}<br>Vote rank: ${d.vote_rank}<br>Votes: ${fmt(d.total_votes)}`,e.clientX,e.clientY)); c.addEventListener('mouseleave',hideTip);
    svg.appendChild(c);
  });
  const xLab=svgEl('text',{x:m.l+plotW/2,y:h-25,'text-anchor':'middle','font-size':13,'font-weight':900,fill:'#526174'}); xLab.textContent='Online mention rank'; svg.appendChild(xLab);
  const yLab=svgEl('text',{x:20,y:m.t+plotH/2,transform:`rotate(-90 20 ${m.t+plotH/2})`,'text-anchor':'middle','font-size':13,'font-weight':900,fill:'#526174'}); yLab.textContent='Actual vote rank'; svg.appendChild(yLab);
}

function lineChart(elId, rows){
  const el=document.getElementById(elId); clear(el); const w=el.clientWidth||800,h=el.clientHeight||500;
  const svg=svgEl('svg',{viewBox:`0 0 ${w} ${h}`, width:'100%', height:'100%'}); el.appendChild(svg);
  const m={l:64,r:28,t:30,b:56}; const plotW=w-m.l-m.r, plotH=h-m.t-m.b;
  const data=rows.map(d=>({date:d.date,count:+d.count})); const max=Math.max(...data.map(d=>d.count),1);
  const xScale=i=>m.l+i/(data.length-1)*plotW; const yScale=v=>m.t+(1-v/max)*plotH;
  for(let i=0;i<=5;i++){const y=m.t+i/5*plotH; svg.appendChild(svgEl('line',{x1:m.l,x2:w-m.r,y1:y,y2:y,stroke:'#dbe5ef'}));}
  const path=data.map((d,i)=>(i?'L':'M')+xScale(i)+','+yScale(d.count)).join(' ');
  svg.appendChild(svgEl('path',{d:path,fill:'none',stroke:'#0b5ed7','stroke-width':3}));
  data.forEach((d,i)=>{ if(i%14===0 || i===data.length-1){const c=svgEl('circle',{cx:xScale(i),cy:yScale(d.count),r:4,fill:'#d7263d'}); c.addEventListener('mousemove',e=>showTip(`<b>${d.date}</b><br>Tweets: ${fmt(d.count)}`,e.clientX,e.clientY)); c.addEventListener('mouseleave',hideTip); svg.appendChild(c);}});
  const title=svgEl('text',{x:m.l,y:20,'font-weight':900,'font-size':14,fill:'#17314d'}); title.textContent='Daily Twitter/X election discourse volume'; svg.appendChild(title);
}

class ForceNetwork{
  constructor(elId, data, options={}){this.el=document.getElementById(elId); this.raw=data; this.options=options; this.threshold=options.threshold||0; this.nodes=[]; this.edges=[]; this.anim=null; this.render();}
  resize(){this.draw();}
  setThreshold(t){this.threshold=+t; this.render();}
  render(){
    const edges=this.raw.edges.filter(e=>e.weight>=this.threshold).slice(0,this.options.maxEdges||999);
    const ids=new Set(); edges.forEach(e=>{ids.add(e.source);ids.add(e.target)});
    let nodes=this.raw.nodes.filter(n=>ids.has(n.id));
    if(this.options.maxNodes) nodes=nodes.slice(0,this.options.maxNodes);
    const valid=new Set(nodes.map(n=>n.id));
    this.nodes=nodes.map((n,i)=>({...n,x:0,y:0,vx:0,vy:0,index:i,community:i%7}));
    this.edges=edges.filter(e=>valid.has(e.source)&&valid.has(e.target)).map(e=>({...e,sourceNode:null,targetNode:null}));
    const map=new Map(this.nodes.map(n=>[n.id,n])); this.edges.forEach(e=>{e.sourceNode=map.get(e.source);e.targetNode=map.get(e.target)});
    this.initPositions(); this.draw(); this.simulate(90);
  }
  initPositions(){const w=this.el.clientWidth||700,h=this.el.clientHeight||500,cx=w/2,cy=h/2,r=Math.min(w,h)*.35; this.nodes.forEach((n,i)=>{const a=i/this.nodes.length*Math.PI*2; n.x=cx+Math.cos(a)*r+Math.random()*20; n.y=cy+Math.sin(a)*r+Math.random()*20;});}
  simulate(iter=60){cancelAnimationFrame(this.anim); let step=0; const tick=()=>{this.physics(); this.update(); if(++step<iter)this.anim=requestAnimationFrame(tick)}; tick();}
  physics(){const w=this.el.clientWidth||700,h=this.el.clientHeight||500; const centerX=w/2,centerY=h/2;
    for(const n of this.nodes){n.vx+=(centerX-n.x)*0.002; n.vy+=(centerY-n.y)*0.002;}
    for(let i=0;i<this.nodes.length;i++)for(let j=i+1;j<this.nodes.length;j++){const a=this.nodes[i],b=this.nodes[j]; let dx=a.x-b.x,dy=a.y-b.y,dist=Math.sqrt(dx*dx+dy*dy)+.01; let force=(this.options.charge||900)/(dist*dist); if(dist<80) force*=2; a.vx+=dx/dist*force; a.vy+=dy/dist*force; b.vx-=dx/dist*force; b.vy-=dy/dist*force;}
    const maxW=Math.max(...this.edges.map(e=>e.weight),1);
    for(const e of this.edges){const a=e.sourceNode,b=e.targetNode;if(!a||!b)continue; let dx=b.x-a.x,dy=b.y-a.y,dist=Math.sqrt(dx*dx+dy*dy)+.01; let target=(this.options.linkDistance||130)-Math.min(70,(e.weight/maxW)*60); let force=(dist-target)*0.012; a.vx+=dx/dist*force; a.vy+=dy/dist*force; b.vx-=dx/dist*force; b.vy-=dy/dist*force;}
    for(const n of this.nodes){n.vx*=0.86;n.vy*=0.86;n.x+=n.vx;n.y+=n.vy;n.x=Math.max(20,Math.min(w-20,n.x));n.y=Math.max(20,Math.min(h-20,n.y));}
  }
  draw(){
    clear(this.el); const w=this.el.clientWidth||700,h=this.el.clientHeight||500; const svg=svgEl('svg',{viewBox:`0 0 ${w} ${h}`,width:'100%',height:'100%'}); this.el.appendChild(svg); this.svg=svg;
    this.edgeLayer=svgEl('g'); this.nodeLayer=svgEl('g'); this.labelLayer=svgEl('g'); svg.appendChild(this.edgeLayer); svg.appendChild(this.nodeLayer); svg.appendChild(this.labelLayer);
    this.edgeEls=this.edges.map(e=>{const l=svgEl('line',{stroke:'#8da2b8','stroke-opacity':0.28}); this.edgeLayer.appendChild(l); return l;});
    const maxP=Math.max(...this.nodes.map(n=>n.pagerank||0.001),0.001), maxW=Math.max(...this.nodes.map(n=>n.weighted||n.degree||1),1);
    this.nodeEls=this.nodes.map((n,i)=>{let size=6+Math.sqrt((n.pagerank||0.0005)/maxP)*22; if(n.type==='hashtag') size=5+Math.sqrt((n.weighted||1)/maxW)*17; if(n.type==='candidate'&&n.winner) size+=3; n.r=size;
      const c=svgEl('circle',{r:size,fill:n.type==='hashtag'?'#ffc928':(n.winner?'#0b5ed7':'#d7263d'),stroke:n.type==='candidate'&&n.winner?'#061625':'white','stroke-width':n.winner?2.8:1.5,opacity:.9});
      c.addEventListener('mousemove',e=>{showTip(`<b>${n.label}</b><br>Type: ${n.type}<br>PageRank: ${fmt(n.pagerank)}<br>Weighted degree: ${fmt(n.weighted)}${n.voteRank?'<br>Vote rank: '+n.voteRank:''}${n.mentions?'<br>Mentions: '+fmt(n.mentions):''}`,e.clientX,e.clientY)}); c.addEventListener('mouseleave',hideTip);
      c.addEventListener('mousedown',ev=>{this.drag=n; ev.preventDefault();});
      this.nodeLayer.appendChild(c); return c;});
    this.labelEls=this.nodes.map((n,i)=>{const top=(n.pagerank||0)>0.03 || (n.weighted||0)>1000 || i<12; const t=svgEl('text',{'font-size': top?12:0,'font-weight':800,fill:'#081827','paint-order':'stroke',stroke:'white','stroke-width':3}); t.textContent=top?n.label:''; this.labelLayer.appendChild(t); return t;});
    svg.addEventListener('mousemove',ev=>{if(this.drag){const rect=svg.getBoundingClientRect(); this.drag.x=(ev.clientX-rect.left)*w/rect.width; this.drag.y=(ev.clientY-rect.top)*h/rect.height; this.drag.vx=this.drag.vy=0; this.update();}});
    window.addEventListener('mouseup',()=>{this.drag=null});
    this.update();
  }
  update(){if(!this.svg)return; const maxE=Math.max(...this.edges.map(e=>e.weight),1); this.edges.forEach((e,i)=>{const l=this.edgeEls[i]; l.setAttribute('x1',e.sourceNode.x); l.setAttribute('y1',e.sourceNode.y); l.setAttribute('x2',e.targetNode.x); l.setAttribute('y2',e.targetNode.y); l.setAttribute('stroke-width',1+Math.sqrt(e.weight/maxE)*7);}); this.nodes.forEach((n,i)=>{this.nodeEls[i].setAttribute('cx',n.x); this.nodeEls[i].setAttribute('cy',n.y); this.labelEls[i].setAttribute('x',n.x+n.r+4); this.labelEls[i].setAttribute('y',n.y+4);});}
}

function initNetworks(){
  networks.hero = new ForceNetwork('heroNetwork', DATA.networks.candidate, {threshold:180,maxEdges:40,charge:1200,linkDistance:140});
  networks.concept = new ForceNetwork('conceptNetwork', {nodes:[{id:'Tweet',label:'Tweet',type:'hashtag',weighted:9,pagerank:.04},{id:'Candidate',label:'Candidate',type:'candidate',weighted:8,pagerank:.03,winner:true},{id:'Hashtag',label:'Hashtag',type:'hashtag',weighted:7,pagerank:.03},{id:'User',label:'User',type:'candidate',weighted:5,pagerank:.01},{id:'Topic',label:'Topic',type:'hashtag',weighted:4,pagerank:.01}],edges:[{source:'Tweet',target:'Candidate',weight:5},{source:'Tweet',target:'Hashtag',weight:5},{source:'Tweet',target:'User',weight:3},{source:'Hashtag',target:'Topic',weight:2},{source:'Candidate',target:'Topic',weight:2}]},{threshold:0,charge:1000,linkDistance:120});
  networks.candidate = new ForceNetwork('candidateNetwork', DATA.networks.candidate, {threshold:50,maxEdges:160,charge:1300,linkDistance:145});
  networks.hashtag = new ForceNetwork('hashtagNetwork', DATA.networks.hashtag, {threshold:100,maxEdges:240,charge:1200,linkDistance:130});
  networks.bipartite = new ForceNetwork('bipartiteNetwork', DATA.networks.bipartite, {threshold:10,maxEdges:220,charge:1200,linkDistance:135});
  document.getElementById('candThreshold').oninput=e=>{document.getElementById('candThresholdLabel').textContent=e.target.value; networks.candidate.setThreshold(+e.target.value)};
  document.getElementById('hashThreshold').oninput=e=>{document.getElementById('hashThresholdLabel').textContent=e.target.value; networks.hashtag.setThreshold(+e.target.value)};
  document.getElementById('biThreshold').oninput=e=>{document.getElementById('biThresholdLabel').textContent=e.target.value; networks.bipartite.setThreshold(+e.target.value)};
  document.querySelectorAll('[data-reset-network]').forEach(b=>b.onclick=()=>{const id=b.dataset.resetNetwork; const key=id.replace('Network',''); if(networks[key]) networks[key].render();});
}

function buildTweetNetwork(){
  const txt=document.getElementById('tweetInput').value;
  const hashtags=[...txt.matchAll(/#([A-Za-z0-9_]+)/g)].map(m=>'#'+m[1]);
  const candidates=['Bam Aquino','Kiko Pangilinan','Bong Go','Bato Dela Rosa','Imee Marcos','Heidi Mendoza','Erwin Tulfo','Apollo Quiboloy'].filter(c=>txt.toLowerCase().includes(c.toLowerCase().split(' ')[0]) || txt.toLowerCase().includes(c.toLowerCase()));
  const nodes=[...candidates.map(c=>({id:c,label:c,type:'candidate',pagerank:.02,weighted:5,winner:false})),...hashtags.map(h=>({id:h,label:h,type:'hashtag',pagerank:.015,weighted:3}))];
  let edges=[]; for(let i=0;i<candidates.length;i++)for(let j=i+1;j<candidates.length;j++)edges.push({source:candidates[i],target:candidates[j],weight:4}); candidates.forEach(c=>hashtags.forEach(h=>edges.push({source:c,target:h,weight:3})));
  document.getElementById('extractionResult').innerHTML=`<b>Extracted candidates:</b> ${candidates.join(', ')||'None'}<br><b>Extracted hashtags:</b> ${hashtags.join(', ')||'None'}<br><b>Generated edges:</b> ${edges.length}`;
  networks.tweet = new ForceNetwork('tweetNetworkSim',{nodes,edges},{threshold:0,charge:1200,linkDistance:120});
}
function initTweetBuilder(){document.getElementById('buildTweetNetwork').onclick=buildTweetNetwork; document.getElementById('sampleTweet').onclick=()=>{const samples=['Bong Go and Bato Dela Rosa dominate discussion under #Halalan2025 and #Duterte.','Heidi Mendoza, Bam Aquino, and Luke Espiritu appear together in reform-themed tweets with #Eleksyon2025.','Erwin Tulfo and Ben Tulfo are frequently discussed in visibility and name-recall conversations.']; document.getElementById('tweetInput').value=samples[Math.floor(Math.random()*samples.length)]; buildTweetNetwork();}; buildTweetNetwork();}

function initCharts(){
  renderOverview();
  barChart('voteRankChart', DATA.topVote, {label:'candidate', value:'total_votes_m', left:170, format:v=>v.toFixed(1)+'M'});
  barChart('correlationChart', DATA.correlations, {label:'label', value:'spearman_r_vs_votes', left:240, format:v=>v.toFixed(3)});
  barChart('overperformanceChart', DATA.overperformance.sort((a,b)=>b.online_gap-a.online_gap), {label:'candidate', value:'online_gap', left:180, diverging:true, format:v=>v>0?'+'+v:v});
  scatterChart('rankScatter', DATA.scatter);
  lineChart('dailyTweetTimeline', DATA.timeline.dailyTweets);
  document.getElementById('scatterMode').onchange=e=>{let rows=DATA.scatter; if(e.target.value==='winners') rows=rows.filter(d=>d.winner_top12); if(e.target.value==='nonwinners') rows=rows.filter(d=>!d.winner_top12); scatterChart('rankScatter',rows);};
}

function initTimeline(){
  const dates=[...new Set(DATA.timeline.dailyTweets.map(d=>d.date))].sort(); const slider=document.getElementById('timeSlider'); slider.max=dates.length-1; slider.oninput=e=>{timelineIndex=+e.target.value; renderRace(dates[timelineIndex]);};
  document.getElementById('playTimeline').onclick=()=>{clearInterval(timelineTimer); timelineTimer=setInterval(()=>{timelineIndex=(timelineIndex+1)%dates.length; slider.value=timelineIndex; renderRace(dates[timelineIndex]);},420);};
  document.getElementById('pauseTimeline').onclick=()=>clearInterval(timelineTimer);
  renderRace(dates[0]);
}
function renderRace(date){
  document.getElementById('timeLabel').textContent=date;
  const rows=DATA.timeline.candidateDaily.filter(d=>d.date===date).sort((a,b)=>b.count-a.count).slice(0,10);
  const max=Math.max(...rows.map(d=>d.count),1); const el=document.getElementById('candidateRace');
  el.innerHTML=rows.length?rows.map(d=>`<div class="raceRow"><div class="raceLabel">${d.candidate}</div><div class="raceTrack"><div class="raceBar" style="width:${Math.max(2,d.count/max*100)}%"></div></div><div class="raceVal">${d.count}</div></div>`).join(''):'<p class="caption">No selected candidate mentions detected on this date.</p>';
}

function initConcepts(){document.querySelectorAll('.concept').forEach(c=>c.onclick=()=>{document.querySelectorAll('.concept').forEach(x=>x.classList.remove('active')); c.classList.add('active');});}

window.addEventListener('load',()=>{initNav(); initCharts(); initNetworks(); initTweetBuilder(); initTimeline(); initConcepts();});
