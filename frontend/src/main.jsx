import React, {useEffect, useMemo, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {AlertCircle, BookOpen, Bot, ChartNoAxesCombined, CheckCircle2, ChevronRight, CircleUserRound, ClipboardList, Database, FileText, GraduationCap, LayoutDashboard, LogOut, Menu, MessageCircle, Search, Send, Sparkles, Trash2, Upload, Users, X} from 'lucide-react';
import {Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import './styles.css';

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000/api' : '/api');
async function request(path, options={}) { let role='';try{role=JSON.parse(localStorage.getItem('mainrag-user'))?.role||''}catch{}const headers={...(options.headers||{}),...(role?{'X-Role':role}:{})};const r=await fetch(API+path,{...options,headers}); let data={};try{data=await r.json()}catch{data={detail:await r.text().catch(()=> '')}} if(!r.ok) throw new Error(data.detail||'请求失败'); return data; }
const post=(path, body)=>request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});

function Login({onLogin}) {
  const [role,setRole]=useState('student'), [form,setForm]=useState({username:'student',password:'123456'}), [error,setError]=useState(''), [loading,setLoading]=useState(false);
  const switchRole=r=>{setRole(r);setForm({username:r,password:'123456'});setError('')};
  const submit=async e=>{e.preventDefault();setLoading(true);try{const d=await post('/login',{...form,role});localStorage.setItem('mainrag-user',JSON.stringify(d.user));history.replaceState({},'',`/${role}/home`);onLogin(d.user)}catch(e){setError(e.message)}finally{setLoading(false)}};
  return <div className="login-page"><div className="login-brand"><div className="brand-mark"><GraduationCap/></div><div><b>知问课堂</b><span>轻量教学智能体</span></div></div><div className="login-copy"><span className="eyebrow"><Sparkles size={15}/> AI 驱动的个性化学习</span><h1>让每一次提问<br/>都成为<span>成长的起点</span></h1><p>连接课程知识与学习过程，为教师提供洞察，为学生提供随时可用的智能辅导。</p><div className="feature-row"><i><Database/><span>课程知识库<small>统一沉淀教学资料</small></span></i><i><Bot/><span>智能问答<small>答案有据可循</small></span></i><i><ChartNoAxesCombined/><span>学情洞察<small>看见每一步成长</small></span></i></div></div><form className="login-card" onSubmit={submit}><div className="mobile-logo"><GraduationCap/> 知问课堂</div><h2>欢迎回来</h2><p>选择你的身份，开始今天的学习旅程</p><div className="role-tabs"><button type="button" className={role==='student'?'active':''} onClick={()=>switchRole('student')}><GraduationCap/>学生端</button><button type="button" className={role==='teacher'?'active':''} onClick={()=>switchRole('teacher')}><Users/>教师端</button></div><label>账号<input value={form.username} onChange={e=>setForm({...form,username:e.target.value})}/></label><label>密码<input type="password" value={form.password} onChange={e=>setForm({...form,password:e.target.value})}/></label>{error&&<div className="error">{error}</div>}<button className="primary login-btn" disabled={loading}>{loading?'正在登录…':'进入知问课堂'}<ChevronRight size={18}/></button><small className="hint">演示账号：{role} / 123456</small></form></div>
}

const navs={student:[['dashboard','学习首页',LayoutDashboard],['knowledge','课程资料',Database],['exams','练习中心',ClipboardList],['wrongbook','错题本',AlertCircle],['chat','智能问答',MessageCircle],['analysis','我的学情',ChartNoAxesCombined]],teacher:[['dashboard','教学概览',LayoutDashboard],['knowledge','知识库',Database],['exams','习题管理',ClipboardList],['chat','问答助手',MessageCircle],['analysis','班级学情',ChartNoAxesCombined]]};
const pageSlug={dashboard:'home',knowledge:'knowledge',exams:'exams',wrongbook:'wrongbook',chat:'chat',analysis:'analysis'};
const slugPage={home:'dashboard',knowledge:'knowledge',exams:'exams',wrongbook:'wrongbook',chat:'chat',analysis:'analysis'};
function initialPage(role){const [pathRole,slug]=location.pathname.split('/').filter(Boolean);return pathRole===role&&slugPage[slug]?slugPage[slug]:'dashboard'}
class ErrorBoundary extends React.Component{constructor(props){super(props);this.state={error:null}}static getDerivedStateFromError(error){return{error}}componentDidUpdate(prev){if(prev.resetKey!==this.props.resetKey&&this.state.error)this.setState({error:null});if(this.state.error&&!sessionStorage.getItem('mainrag-auto-refreshing')){sessionStorage.setItem('mainrag-auto-refreshing','1');setTimeout(()=>location.reload(),80)}}componentDidMount(){sessionStorage.removeItem('mainrag-auto-refreshing')}render(){if(this.state.error)return null;return this.props.children}}
function Shell({user,onLogout}){const [page,setPageState]=useState(()=>initialPage(user.role)),[open,setOpen]=useState(false);const setPage=(next)=>{const url=`/${user.role}/${pageSlug[next]}`;if(location.pathname!==url)location.assign(url);else location.reload()};useEffect(()=>{const pop=()=>setPageState(initialPage(user.role));addEventListener('popstate',pop);return()=>removeEventListener('popstate',pop)},[user.role]);const title=navs[user.role].find(n=>n[0]===page)?.[1];return <div className="app"><aside className={open?'open':''}><div className="logo"><div className="brand-mark"><GraduationCap/></div><span><b>知问课堂</b><small>TEACHING AGENT</small></span><button className="close" onClick={()=>setOpen(false)}><X/></button></div><div className="side-label">{user.role==='teacher'?'教师工作台':'学习空间'}</div><nav>{navs[user.role].map(([id,label,Icon])=><button key={id} className={page===id?'active':''} onClick={()=>{setPage(id);setOpen(false)}}><Icon/>{label}</button>)}</nav><div className="side-user"><CircleUserRound/><span><b>{user.name}</b><small>{user.role==='teacher'?'计算机网络 · 教师':'计算机网络 · 2023级'}</small></span><button onClick={onLogout}><LogOut/></button></div></aside><main><header><button className="hamburger" onClick={()=>setOpen(true)}><Menu/></button><div><small>{user.role==='teacher'?'教师工作台':'我的学习空间'}</small><h2>{title}</h2></div><div className="header-user"><span>{user.name.slice(0,1)}</span><b>{user.name}</b></div></header><ErrorBoundary resetKey={page}><div className="content">{page==='dashboard'?<Dashboard role={user.role} go={setPage}/>:page==='chat'?<Chat user={user}/>:page==='knowledge'?<Knowledge user={user}/>:page==='exams'?<Exams user={user}/>:page==='wrongbook'?<Wrongbook user={user}/>:<Analysis role={user.role}/>}</div></ErrorBoundary></main></div>}

function Stat({icon:Icon,label,value,detail,tone}){return <div className={'stat '+tone}><div className="stat-icon"><Icon/></div><div><small>{label}</small><strong>{value}</strong><span>{detail}</span></div></div>}
function Dashboard({role,go}){const [data,setData]=useState(null);useEffect(()=>{request(role==='teacher'?'/analysis/class':'/analysis/student').then(setData)},[role]);const s=data?.summary||{};return <><section className="welcome"><div><span className="eyebrow"><Sparkles size={14}/>{role==='teacher'?'智能教学助手':'今日学习建议'}</span><h1>{role==='teacher'?'下午好，陈老师':'下午好，张同学'} 👋</h1><p>{role==='teacher'?'班级整体表现平稳，建议重点关注薄弱知识点。':'保持好奇，今天也从一个好问题开始吧。'}</p></div><button className="primary" onClick={()=>go('chat')}><MessageCircle/>开始问答</button></section><div className="stats"><Stat icon={role==='teacher'?Users:ChartNoAxesCombined} label={role==='teacher'?'参与学生':'平均掌握度'} value={role==='teacher'?(data?.students?.length||0)+' 人':(s.average||0)+'%'} detail="较上周稳步提升" tone="blue"/><Stat icon={MessageCircle} label="问答次数" value={s.questions||0} detail="智能体已记录" tone="violet"/><Stat icon={Database} label="知识资料" value={s.documents||0} detail="已建立检索索引" tone="green"/><Stat icon={BookOpen} label="学习记录" value={s.activities||0} detail="持续积累中" tone="orange"/></div><div className="dashboard-grid"><section className="panel chart-panel"><div className="panel-head"><div><h3>{role==='teacher'?'班级学习趋势':'近期学习表现'}</h3><p>学习活动得分变化</p></div></div><div className="chart"><ResponsiveContainer><AreaChart data={data?.trend||[]}><defs><linearGradient id="fill" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stopColor="#5577ee" stopOpacity=".3"/><stop offset="1" stopColor="#5577ee" stopOpacity="0"/></linearGradient></defs><CartesianGrid stroke="#eef1f7" vertical={false}/><XAxis dataKey="date" axisLine={false} tickLine={false}/><YAxis domain={[0,100]} axisLine={false} tickLine={false}/><Tooltip/><Area type="monotone" dataKey="score" stroke="#5577ee" strokeWidth={3} fill="url(#fill)"/></AreaChart></ResponsiveContainer></div></section><section className="panel quick"><div className="panel-head"><div><h3>快捷入口</h3><p>继续你的工作</p></div></div>{(role==='teacher'?[['knowledge','上传课程资料',Upload,'让智能体掌握新内容'],['analysis','查看班级学情',ChartNoAxesCombined,'定位班级薄弱点'],['chat','体验智能问答',Bot,'检验知识库效果']]:[['chat','向智能体提问',Bot,'获得基于课程的解答'],['chat','检索并询问知识',Search,'从课程资料中获得答案'],['analysis','查看我的学情',ChartNoAxesCombined,'了解优势与不足']]).map(([p,t,I,d])=><button onClick={()=>go(p)} key={p}><i><I/></i><span><b>{t}</b><small>{d}</small></span><ChevronRight/></button>)}</section></div></>}

function renderInlineMarkdown(text){
  const parts=String(text||'').split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part,i)=>part.startsWith('**')&&part.endsWith('**')?<strong key={i}>{part.slice(2,-2)}</strong>:part)
}

function MarkdownText({text}){
  const cleanText=String(text||'').replace(/\n?\s*(参考资料|参考来源|资料来源|来源)\s*[:：][\s\S]*$/,'');
  const lines=cleanText.split('\n');
  const blocks=[];
  let i=0;
  while(i<lines.length){
    const line=lines[i];
    if(!line.trim()){i++;continue}
    const ordered=line.match(/^\s*\d+[.)、]\s+(.+)$/);
    if(ordered){
      const items=[];
      while(i<lines.length){
        const m=lines[i].match(/^\s*\d+[.)、]\s+(.+)$/);
        if(!m)break;
        items.push(m[1]);
        i++;
      }
      blocks.push(<ol key={blocks.length}>{items.map((item,j)=><li key={j}>{renderInlineMarkdown(item)}</li>)}</ol>);
      continue;
    }
    const bullet=line.match(/^\s*[-*]\s+(.+)$/);
    if(bullet){
      const items=[];
      while(i<lines.length){
        const m=lines[i].match(/^\s*[-*]\s+(.+)$/);
        if(!m)break;
        items.push(m[1]);
        i++;
      }
      blocks.push(<ul key={blocks.length}>{items.map((item,j)=><li key={j}>{renderInlineMarkdown(item)}</li>)}</ul>);
      continue;
    }
    const heading=line.match(/^\s*#{1,3}\s+(.+)$/);
    if(heading){blocks.push(<h4 key={blocks.length}>{renderInlineMarkdown(heading[1])}</h4>);i++;continue}
    const paragraph=[];
    while(i<lines.length&&lines[i].trim()&&!/^\s*\d+[.)、]\s+/.test(lines[i])&&!/^\s*[-*]\s+/.test(lines[i])&&!/^\s*#{1,3}\s+/.test(lines[i])){paragraph.push(lines[i]);i++}
    blocks.push(<p key={blocks.length}>{renderInlineMarkdown(paragraph.join('\n'))}</p>);
  }
  return <div className="markdown-body">{blocks}</div>
}

function Chat({user}){
  const welcome={role:'ai',text:`你好，${user.name}！我是知问课堂智能体。你可以问我课程概念、知识区别或应用问题，我会从课程知识库中寻找依据。`};
  const [messages,setMessages]=useState([welcome]),[input,setInput]=useState(''),[loading,setLoading]=useState(false),[historyItems,setHistoryItems]=useState([]),[activeHistory,setActiveHistory]=useState('');
  const loadHistory=()=>request(`/chat/history?student=${encodeURIComponent(user.name)}&limit=20`).then(d=>setHistoryItems(d.items||[])).catch(()=>{});
  useEffect(loadHistory,[user.name]);
  const openHistory=item=>{setActiveHistory(item.id);setMessages([welcome,{role:'user',text:item.question},{role:'ai',text:item.answer,sources:item.sources||[]}])};
  const appendToLastAi=(patch)=>setMessages(items=>items.map((m,i)=>i===items.length-1&&m.role==='ai'?{...m,...patch,text:(patch.append?m.text+patch.append:patch.text??m.text)}:m));
  const openSource=s=>{if(!s?.document_id)return;location.assign(`/${user.role}/knowledge?doc=${encodeURIComponent(s.document_id)}&page=${encodeURIComponent(s.page||'')}&chunk=${encodeURIComponent(s.chunk||'')}`)};
  const send=async(q=input)=>{
    if(!q.trim()||loading)return;
    const question=q.trim();
    setActiveHistory('');
    setMessages(m=>[...m,{role:'user',text:question},{role:'ai',text:'',sources:[],streaming:true}]);
    setInput('');
    setLoading(true);
    try{
      let role='';try{role=JSON.parse(localStorage.getItem('mainrag-user'))?.role||''}catch{}
      const response=await fetch(API+'/chat/stream',{method:'POST',headers:{'Content-Type':'application/json',...(role?{'X-Role':role}:{})},body:JSON.stringify({message:question,student:user.name})});
      if(!response.ok){let data={};try{data=await response.json()}catch{data={detail:await response.text().catch(()=> '')}}throw new Error(data.detail||'请求失败')}
      const reader=response.body.getReader();
      const decoder=new TextDecoder('utf-8');
      let buffer='';
      while(true){
        const {value,done}=await reader.read();
        if(done)break;
        buffer+=decoder.decode(value,{stream:true});
        const events=buffer.split('\n\n');
        buffer=events.pop()||'';
        for(const raw of events){
          const line=raw.split('\n').find(x=>x.startsWith('data:'));
          if(!line)continue;
          const event=JSON.parse(line.slice(5).trim());
          if(event.type==='delta')appendToLastAi({append:event.content,streaming:true});
          if(event.type==='sources')appendToLastAi({sources:event.sources||[]});
          if(event.type==='done')appendToLastAi({text:event.answer,sources:event.sources||[],streaming:false});
        }
      }
      loadHistory();
    }catch(e){appendToLastAi({text:e.message,streaming:false})}
    finally{setLoading(false)}
  };
  return <div className="chat-layout"><section className="chat-box"><div className="chat-top"><div className="bot-avatar"><Bot/></div><div><b>课程智能体</b><small><i/>在线 · 基于知识库回答 · 流式输出</small></div></div><div className="messages">{messages.map((m,i)=><div className={'message '+m.role} key={i}>{m.role==='ai'&&<div className="avatar"><Sparkles/></div>}<div><div className={'bubble '+(m.streaming?'streaming':'')}>{m.role==='ai'?<MarkdownText text={m.text}/>:m.text}{m.streaming&&<span className="stream-cursor">|</span>}</div>{m.sources?.length>0&&<div className="sources"><b><FileText/>参考来源</b>{m.sources.map((s,j)=><button className="source-link" key={j} onClick={()=>openSource(s)} title="点击跳转到对应文档和页面"><span>{s.document} · {s.page?`第 ${s.page} 页`:`片段 ${s.chunk}`}</span><em>{Math.round(s.score*100)}%</em></button>)}</div>}</div></div>)}</div><div className="composer"><div><textarea placeholder="输入你的问题，Enter 发送…" value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}}/><button onClick={()=>send()} disabled={loading}><Send/></button></div><small>回答由课程知识库生成，支持 Markdown 渲染，请结合课堂内容判断</small></div></section><aside className="suggestions chat-side"><div className="side-block"><h3><Sparkles/>试试这样问</h3>{['TCP 如何保证可靠传输？','HTTP 和 HTTPS 有什么区别？','什么是数据库事务的 ACID？','IPv4 与 IPv6 的主要区别？'].map(x=><button key={x} onClick={()=>send(x)}>{x}<ChevronRight/></button>)}</div><div className="side-block history-block"><h3><MessageCircle/>历史问答</h3>{historyItems.length===0?<p className="empty-history">暂无历史记录，提问后会自动保存。</p>:historyItems.map(item=><button className={activeHistory===item.id?'active':''} key={item.id} onClick={()=>openHistory(item)}><span>{item.question}</span><small>{item.topic} · {item.at?.replace('T',' ')}</small></button>)}</div><div className="tip"><BookOpen/><b>提问小技巧</b><p>问题越具体，检索到的课程内容越准确。</p></div></aside></div>
}

function Knowledge({user}) {
  const isTeacher=user.role==='teacher';
  const [docs,setDocs]=useState([]),[selected,setSelected]=useState(null),[uploading,setUploading]=useState(false),[reindexing,setReindexing]=useState(false),[progress,setProgress]=useState(0),[stage,setStage]=useState(''),[uploadName,setUploadName]=useState(''),[msg,setMsg]=useState('');
  const [targetPage,setTargetPage]=useState('');
  const load=()=>request('/knowledge').then(d=>setDocs(d.items));
  useEffect(load,[]);
  useEffect(()=>{const params=new URLSearchParams(location.search);const target=params.get('doc');const page=params.get('page')||'';setTargetPage(page);if(target)view(target,page)},[]);
  useEffect(()=>{if(!docs.some(d=>d.preview_status==='processing'))return;const timer=setInterval(load,3000);return()=>clearInterval(timer)},[docs]);
  useEffect(()=>{if(!selected||selected.preview_status!=='processing')return;const timer=setInterval(()=>request('/knowledge/'+selected.id).then(setSelected).catch(()=>{}),3000);return()=>clearInterval(timer)},[selected]);
  const view=async(id,page='')=>{try{setTargetPage(page);setSelected(await request('/knowledge/'+id))}catch(e){setMsg(e.message)}};
  const upload=e=>{const file=e.target.files[0];if(!file)return;e.target.value='';setUploading(true);setProgress(0);setStage('正在上传文件');setUploadName(file.name);setMsg('');const fd=new FormData();fd.append('file',file);fd.append('category','课程资料');const xhr=new XMLHttpRequest();let timer;xhr.open('POST',API+'/knowledge/upload');xhr.setRequestHeader('X-Role','teacher');xhr.upload.onprogress=event=>{if(event.lengthComputable)setProgress(Math.round(event.loaded/event.total*65))};xhr.upload.onload=()=>{setProgress(p=>Math.max(p,66));setStage('正在解析文档并建立向量索引');timer=setInterval(()=>setProgress(p=>p<94?p+1:p),700)};xhr.onload=()=>{clearInterval(timer);let data={};try{data=JSON.parse(xhr.responseText)}catch{}if(xhr.status>=200&&xhr.status<300){setProgress(100);setStage('上传完成，预览后台处理中');setMsg(data.message||'上传成功，预览正在后台生成');load();setTimeout(()=>setUploading(false),800)}else{setUploading(false);setMsg(data.detail||'上传处理失败')}};xhr.onerror=()=>{clearInterval(timer);setUploading(false);setMsg('网络错误，上传失败')};xhr.send(fd)};
  const del=async id=>{if(!confirm('确定删除这份资料吗？'))return;await request('/knowledge/'+id,{method:'DELETE'});if(selected?.id===id)setSelected(null);load()};
  const reindex=async()=>{setReindexing(true);setMsg('');try{const d=await post('/knowledge/reindex',{});setMsg(`${d.message}：${d.documents} 个文档，${d.chunks} 个向量片段`);load()}catch(e){setMsg(e.message)}finally{setReindexing(false)}};
  const previewText=d=>d.preview_status==='processing'?'正在处理预览':(d.has_preview||d.preview_status==='ready')?'可查看':d.preview_status==='failed'?'预览失败':'暂无预览';
  const canPreview=d=>d.has_preview||d.preview_status==='ready';
  return <>
    <section className="knowledge-head">
      <div>
        <span className="eyebrow"><Database size={15}/>{isTeacher?'知识中枢':'课程资源'}</span>
        <h1>{isTeacher?'课程知识库':'我的课程资料'}</h1>
        <p>{isTeacher?'上传、查看和管理课程资料，文件会自动建立向量索引，原版式预览会在后台生成。':'查看教师上传的课程文档，预览处理完成后即可打开原版式资料。'}</p>
      </div>
      {isTeacher&&<div className="knowledge-actions">
        <button className="secondary-btn" onClick={reindex} disabled={reindexing||uploading}><Sparkles/>{reindexing?'正在重建…':'重建向量索引'}</button>
        <label className="primary upload-btn"><Upload/>{uploading?'正在处理…':'上传资料'}<input type="file" accept=".doc,.docx,.ppt,.pptx,.pdf" onChange={upload} disabled={uploading}/></label>
      </div>}
    </section>

    {uploading&&<div className="upload-progress"><div className="progress-file"><i><FileText/></i><span><b>{uploadName}</b><small>{stage}</small></span><strong>{progress}%</strong></div><div className="progress-track"><i style={{width:progress+'%'}}/></div></div>}
    {msg&&<div className="notice">{msg}</div>}

    <div className="kb-summary">
      <div><Database/><span><b>{docs.length}</b><small>知识文档</small></span></div>
      <div><FileText/><span><b>{docs.reduce((n,d)=>n+d.chunks,0)}</b><small>向量片段</small></span></div>
      <div><Sparkles/><span><b>{docs.filter(d=>d.preview_status==='processing').length}</b><small>预览处理中</small></span></div>
    </div>

    <section className="panel table-panel">
      <div className="panel-head"><div><h3>{isTeacher?'全部资料':'教师共享资料'}</h3><p>支持 DOC、DOCX、PPT、PPTX、PDF</p></div></div>
      <div className="doc-table">
        <div className="tr th"><span>资料名称</span><span>分类</span><span>片段</span><span>上传时间</span><span>预览</span></div>
        {docs.map(d=><div className="tr" key={d.id}>
          <span className="doc-name"><i><FileText/></i><b>{d.name}<small>{d.size} KB</small></b></span>
          <span><em className="tag">{d.type}</em></span>
          <span>{d.chunks}</span>
          <span>{d.created_at}</span>
          <span className="doc-actions">
            <button className={'view-doc preview-action '+(d.preview_status||'')} onClick={()=>view(d.id)} disabled={!canPreview(d)}>{canPreview(d)?<CheckCircle2/>:<AlertCircle/>}{previewText(d)}</button>
            {isTeacher&&<button className="trash" onClick={()=>del(d.id)}><Trash2/></button>}
          </span>
        </div>)}
      </div>
    </section>

    {selected&&<section className="panel document-reader">
      <div className="reader-head"><div><span className="eyebrow"><FileText size={14}/>{selected.type}</span><h2>{selected.name}</h2><p>{selected.created_at} · {selected.size} KB{targetPage?` · 已定位到第 ${targetPage} 页`:''}</p></div><button onClick={()=>setSelected(null)}><X/></button></div>
      {selected.has_preview
        ? <iframe key={`${selected.id}-${targetPage||'top'}`} className="document-frame" src={`${API}/knowledge/${selected.id}/preview${targetPage?`#page=${targetPage}&zoom=page-width`:''}`} title={selected.name}/>
        : <div className="no-preview"><AlertCircle/><b>{selected.preview_status==='processing'?'原版式预览正在处理中':'暂无原版式预览'}</b><p>{selected.preview_status==='processing'?'上传已经成功，预览文件正在后台生成，完成后预览标签会自动变为可查看。':(selected.preview_error||'该文件暂时没有可查看的原版式预览。')}</p></div>}
    </section>}
  </>
}

function Analysis({role}){
  const [data,setData]=useState(null);
  useEffect(()=>{
    request(role==='teacher'?'/analysis/class':'/analysis/student')
      .then(setData)
      .catch(()=>setData({summary:{},mastery:[],trend:[],students:[],suggestion:'学情数据暂时无法加载，请稍后再试。'}));
  },[role]);
  const mastery=data?.mastery||[], summary=data?.summary||{}, students=data?.students||[];
  return <>
    <section className="analysis-title">
      <div>
        <span className="eyebrow"><ChartNoAxesCombined size={15}/>{role==='teacher'?'班级数据洞察':'个性化学习报告'}</span>
        <h1>{role==='teacher'?'班级学情分析':'我的学情分析'}</h1>
        <p>{role==='teacher'?'基于学习记录与问答行为，快速掌握班级学习状态。':'看见自己的进步，也找到下一步努力的方向。'}</p>
      </div>
    </section>
    <div className="stats">
      <Stat icon={ChartNoAxesCombined} label="平均掌握度" value={(summary.average||0)+'%'} detail="综合学习活动" tone="blue"/>
      <Stat icon={BookOpen} label="学习活动" value={summary.activities||0} detail="已纳入分析" tone="green"/>
      <Stat icon={MessageCircle} label="主动提问" value={summary.questions||0} detail="探索意识良好" tone="violet"/>
      <Stat icon={Database} label="课程资料" value={summary.documents||0} detail="可供检索" tone="orange"/>
    </div>
    <div className="analysis-grid">
      <section className="panel">
        <div className="panel-head">
          <div><h3>知识点掌握度</h3><p>按学习活动综合评估</p></div>
        </div>
        <div className="chart">
          <ResponsiveContainer>
            <BarChart data={mastery} layout="vertical" margin={{left:20,right:30}}>
              <CartesianGrid stroke="#eef1f7" horizontal={false}/>
              <XAxis type="number" domain={[0,100]} axisLine={false}/>
              <YAxis type="category" dataKey="topic" width={90} axisLine={false} tickLine={false}/>
              <Tooltip/>
              <Bar
                dataKey="score"
                fill="#627eea"
                radius={[0,8,8,0]}
                barSize={20}
                minPointSize={8}
                onClick={(data) => {
                  const topic = data?.topic || data?.payload?.topic || data?.[0]?.payload?.topic;
                  if (topic) {
                    location.assign(`/student/wrongbook?knowledge=${encodeURIComponent(topic)}`);
                  }
                }}
                style={{ cursor: 'pointer' }}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </section>
      <section className="panel insight">
        <div className="insight-icon"><Sparkles/></div>
        <h3>智能学习建议</h3>
        <p>{data?.suggestion||'暂无足够学习记录。'}</p>
        <div className="insight-list">
          {mastery.slice(0,3).map((m,i)=><div key={m.topic}><span>{i+1}</span><b>{m.topic}<small>{m.score<70?'建议重点复习':m.score<85?'继续巩固':'掌握良好'}</small></b><em>{m.score}%</em></div>)}
        </div>
      </section>
    </div>
    {role==='teacher'&&<section className="panel student-panel">
      <div className="panel-head"><div><h3>学生概览</h3><p>班级个体学习状态</p></div></div>
      <div className="student-list">
        {students.map((s,i)=><div key={s.name||i}><span className="student-avatar">{(s.name||'学')[0]}</span><b>{s.name||'学生'}<small>{s.activities||0} 次学习活动</small></b><div className="mini-progress"><i style={{width:(s.average||0)+'%'}}/></div><em>{s.average||0}%</em></div>)}
      </div>
    </section>}
  </>;
}

function TeacherExams(){const [docs,setDocs]=useState([]),[items,setItems]=useState([]),[form,setForm]=useState({document_id:'',chapter:'全文',title:'',count:5,difficulty:'中等'}),[loading,setLoading]=useState(false),[msg,setMsg]=useState('');const load=()=>Promise.all([request('/knowledge'),request('/exams')]).then(([d,e])=>{setDocs(d.items);setItems(e.items);setForm(f=>({...f,document_id:f.document_id||d.items[0]?.id||''}))});useEffect(load,[]);const generate=async e=>{e.preventDefault();setLoading(true);setMsg('');try{await post('/exams/generate',{...form,count:Number(form.count)});setMsg('习题生成成功，请检查后发布。');load()}catch(e){setMsg(e.message)}finally{setLoading(false)}};const publish=async id=>{await post(`/exams/${id}/publish`,{});setMsg('已发布到学生端');load()};const remove=async id=>{if(!confirm('确定删除这套习题吗？'))return;await request(`/exams/${id}`,{method:'DELETE'});load()};return <><section className="knowledge-head"><div><span className="eyebrow"><ClipboardList size={15}/>AI 出题</span><h1>习题生成与发布</h1><p>选择知识库文件和章节，由 DeepSeek 生成课程习题并发布给学生。</p></div></section><div className="exam-layout"><form className="panel exam-form" onSubmit={generate}><div className="panel-head"><div><h3>生成新习题</h3><p>题目答案严格来自所选资料</p></div></div><label>知识库文件<select value={form.document_id} onChange={e=>setForm({...form,document_id:e.target.value})}>{docs.map(d=><option value={d.id} key={d.id}>{d.name}</option>)}</select></label><label>章节或范围<input value={form.chapter} onChange={e=>setForm({...form,chapter:e.target.value})} placeholder="例如：第三章 传输层"/></label><label>习题标题<input value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder="留空将自动生成"/></label><div className="form-row"><label>题目数量<input type="number" min="1" max="20" value={form.count} onChange={e=>setForm({...form,count:e.target.value})}/></label><label>难度<select value={form.difficulty} onChange={e=>setForm({...form,difficulty:e.target.value})}><option>简单</option><option>中等</option><option>困难</option></select></label></div><button className="primary" disabled={loading||!form.document_id}><Sparkles/>{loading?'DeepSeek 正在生成…':'生成习题'}</button>{msg&&<div className="notice">{msg}</div>}</form><section className="panel exam-list"><div className="panel-head"><div><h3>习题列表</h3><p>共 {items.length} 套习题</p></div></div>{items.length===0?<div className="empty">还没有生成习题</div>:items.map(exam=><article className="exam-card" key={exam.id}><div className="exam-card-icon"><ClipboardList/></div><div><h4>{exam.title}</h4><p>{exam.document_name} · {exam.chapter}</p><span>{exam.questions.length} 题</span><span>{exam.difficulty}</span><em className={exam.status}>{exam.status==='published'?'已发布':'草稿'}</em></div><div className="exam-actions">{exam.status!=='published'&&<button className="publish" onClick={()=>publish(exam.id)}>发布</button>}<button className="trash" onClick={()=>remove(exam.id)}><Trash2/></button></div></article>)}</section></div></>}

function StudentExams({user}){const [items,setItems]=useState([]),[subs,setSubs]=useState([]),[active,setActive]=useState(null),[answers,setAnswers]=useState({}),[result,setResult]=useState(null);const load=()=>Promise.all([request('/exams?published_only=true'),request(`/exams/student/submissions?student=${encodeURIComponent(user.name)}`)]).then(([e,s])=>{setItems(e.items);setSubs(s.items)});useEffect(load,[]);const submitted=id=>subs.find(s=>s.exam_id===id);const open=exam=>{setActive(exam);setAnswers({});setResult(null)};const submit=async()=>{if(!confirm('确认提交本次练习吗？'))return;const data=await post(`/exams/${active.id}/submit`,{student:user.name,answers});setResult(data);load()};if(active)return <section className="panel take-exam"><button className="back-link" onClick={()=>setActive(null)}>← 返回练习中心</button><div className="take-head"><div><h1>{active.title}</h1><p>{active.document_name} · {active.chapter}</p></div>{result&&<strong>{result.score}/{result.total}</strong>}</div>{active.questions.map((q,i)=>{const detail=result?.details.find(d=>d.id===q.id);return <article className={'question '+(detail?(detail.correct?'correct':'wrong'):'')} key={q.id}><h3><span>{i+1}</span>{q.question}</h3>{q.options?.length>0?<div className="options">{q.options.map(option=>{const value=option.match(/^([A-Za-z])\./)?.[1]||option;return <label key={option}><input type="radio" name={q.id} disabled={!!result} checked={answers[q.id]===value} onChange={()=>setAnswers({...answers,[q.id]:value})}/><span>{option}</span></label>})}</div>:<textarea disabled={!!result} value={answers[q.id]||''} onChange={e=>setAnswers({...answers,[q.id]:e.target.value})} placeholder="请输入你的答案"/>}{detail&&!detail.correct&&<div className="answer-detail"><b>正确答案：{detail.answer}</b><p>{detail.analysis}</p></div>}</article>})}{!result?<button className="primary submit-exam" onClick={submit}>提交练习</button>:<button className="primary submit-exam" onClick={()=>setActive(null)}>完成并返回</button>}</section>;return <><section className="analysis-title"><div><span className="eyebrow"><ClipboardList size={15}/>课程练习</span><h1>练习中心</h1><p>完成教师发布的习题，结果会自动进入学情分析和错题本。</p></div></section><div className="exercise-grid">{items.length===0?<div className="panel empty">教师还没有发布习题</div>:items.map(exam=>{const done=submitted(exam.id);return <article className="panel exercise" key={exam.id}><div className="exercise-top"><i><ClipboardList/></i><em>{exam.difficulty}</em></div><h3>{exam.title}</h3><p>{exam.document_name} · {exam.chapter}</p><div><span>{exam.questions.length} 道题</span>{done&&<span className="done"><CheckCircle2/>已完成 {done.accuracy}%</span>}</div><button onClick={()=>open(exam)}>{done?'重新练习':'开始练习'}<ChevronRight/></button></article>})}</div></>}

function Exams({user}){return user.role==='teacher'?<TeacherExams/>:<StudentExams user={user}/>}

function Wrongbook({user}) {
  const [items, setItems] = useState([]);
  const [mastery, setMastery] = useState([]);
  const [filter, setFilter] = useState(() => {
    const params = new URLSearchParams(location.search);
    return params.get('knowledge') || '';
  });
  const [loading, setLoading] = useState(true);

  // 加载错题和学情数据
  const loadData = () => {
    setLoading(true);
    Promise.all([
      request(`/exams/student/wrongbook?student=${encodeURIComponent(user.name)}`),
      request('/analysis/student')
    ]).then(([wrongRes, analysisRes]) => {
      setItems(wrongRes.items || []);
      setMastery(analysisRes.mastery || []);
    }).catch(() => {})
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [user.name]);

  // 监听 URL 变化（popstate 和 pushState 触发）
  useEffect(() => {
    const onPop = () => {
      const params = new URLSearchParams(location.search);
      setFilter(params.get('knowledge') || '');
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  // 点击标签：更新 URL 并设置 filter
  const handleTagClick = (topic) => {
    const url = topic
      ? `/student/wrongbook?knowledge=${encodeURIComponent(topic)}`
      : '/student/wrongbook';
    history.pushState(null, '', url);
    setFilter(topic || '');
  };

  // 过滤错题
  const filteredItems = filter
    ? items.filter(q => q.knowledge_point === filter)
    : items;

  // 计算当前筛选知识点的掌握度
  const currentMastery = mastery.find(m => m.topic === filter);

  return (
    <>
      <section className="analysis-title">
        <div>
          <span className="eyebrow"><AlertCircle size={15}/>查漏补缺</span>
          <h1>我的错题本</h1>
          <p>自动收集练习中的错题，结合解析进行针对性复习。</p>
        </div>
      </section>

      {/* 掌握度标签 */}
      {mastery.length > 0 && (
        <div className="mastery-tags" style={{ marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
          <span style={{ fontWeight: 'bold', marginRight: '10px' }}>知识点掌握度：</span>
          {mastery.map(m => (
            <span
              key={m.topic}
              onClick={() => handleTagClick(m.topic)}
              style={{
                padding: '4px 14px',
                borderRadius: '20px',
                background: filter === m.topic ? '#5577ee' : '#eef1f7',
                color: filter === m.topic ? '#fff' : '#333',
                cursor: 'pointer',
                fontSize: '14px',
                transition: '0.2s',
                border: filter === m.topic ? '1px solid #5577ee' : '1px solid transparent',
              }}
            >
              {m.topic} {m.score}%
            </span>
          ))}
          {filter && (
            <button
              onClick={() => handleTagClick('')}
              style={{
                padding: '4px 14px',
                borderRadius: '20px',
                background: '#f0f0f0',
                border: '1px solid #ccc',
                cursor: 'pointer',
                fontSize: '14px',
              }}
            >
              清除筛选
            </button>
          )}
        </div>
      )}

      {/* 筛选提示 */}
      {filter && (
        <div style={{ marginBottom: '16px', color: '#5577ee' }}>
          当前筛选：<strong>{filter}</strong>
          {currentMastery && `（掌握度 ${currentMastery.score}%）`}
          {filteredItems.length === 0 && '，暂无相关错题'}
        </div>
      )}

      <div className="wrong-list">
        {loading ? (
          <div className="panel empty">加载中...</div>
        ) : filteredItems.length === 0 ? (
          <div className="panel empty">
            {filter ? <CheckCircle2/> : <CheckCircle2/>}
            {filter ? '该知识点暂无错题，继续保持！' : '暂无错题，继续保持！'}
          </div>
        ) : (
          filteredItems.map((q, i) => (
            <article className="panel wrong-item" key={q.exam_id + q.id}>
              <div className="wrong-meta">
                <span>{q.exam_title}</span>
                <em>{q.knowledge_point}</em>
              </div>
              <h3>{i+1}. {q.question}</h3>
              <p className="your-answer">你的答案：{q.student_answer || '未作答'}</p>
              <p className="right-answer">正确答案：{q.answer}</p>
              <div className="explanation"><Sparkles/> {q.analysis}</div>
            </article>
          ))
        )}
      </div>
    </>
  );
}

function App(){const [user,setUser]=useState(()=>{try{return JSON.parse(localStorage.getItem('mainrag-user'))}catch{return null}});useEffect(()=>{if(!user&&location.pathname!='/login')history.replaceState({},'','/login')},[user]);return user?<Shell user={user} onLogout={()=>{localStorage.removeItem('mainrag-user');history.replaceState({},'','/login');setUser(null)}}/>:<Login onLogin={setUser}/>}
createRoot(document.getElementById('root')).render(<App/>);










