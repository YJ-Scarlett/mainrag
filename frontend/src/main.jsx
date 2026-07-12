import React, {useEffect, useMemo, useRef, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {AlertCircle, BookOpen, Bot, Camera, ChartNoAxesCombined, CheckCircle2, ChevronRight, CircleUserRound, ClipboardList, Database, Eye, File, FileText, GraduationCap, LayoutDashboard, LogOut, Menu, MessageCircle, Music, Search, Send, Sparkles, Trash2, Upload, Users, Video, X} from 'lucide-react';
import {Area, AreaChart, Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis} from 'recharts';
import './styles.css';
import { RefreshCw } from 'lucide-react';
import EmptyFolder from './assets/illustrations/empty-folder.svg';
import EmptyQuestions from './assets/illustrations/empty-questions.svg';
import EmptyCelebration from './assets/illustrations/empty-celebration.svg';
import WelcomeLearning from './assets/illustrations/welcome-learning.svg';
import UploadCloud from './assets/illustrations/upload-cloud.svg';

const API = import.meta.env.VITE_API_URL || (import.meta.env.DEV ? 'http://localhost:8000/api' : '/api');
const requestCache=new Map();
async function request(path, options={}) { const {cache=true,...fetchOptions}=options;let role='';try{role=JSON.parse(localStorage.getItem('mainrag-user'))?.role||''}catch{}const method=(fetchOptions.method||'GET').toUpperCase();const cacheKey=`${role}:${path}`;if(method==='GET'&&cache&&requestCache.has(cacheKey)){const item=requestCache.get(cacheKey);if(Date.now()-item.time<10000)return item.data}const headers={...(fetchOptions.headers||{}),...(role?{'X-Role':role}:{})};const r=await fetch(API+path,{...fetchOptions,headers}); let data={};try{data=await r.json()}catch{data={detail:await r.text().catch(()=> '')}} if(!r.ok) throw new Error(data.detail||'请求失败'); if(method==='GET'&&cache)requestCache.set(cacheKey,{time:Date.now(),data}); return data; }
const post=(path, body)=>request(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});

function Login({onLogin}) {
  const [role,setRole]=useState('student');
  const [form,setForm]=useState({username:'student',password:'123456'});
  const [error,setError]=useState('');
  const [loading,setLoading]=useState(false);
  const [mode, setMode] = useState('login'); // 'login' 或 'register'
  const [registerForm, setRegisterForm] = useState({
    name: '',
    password: '',
    confirm: '',
    role: 'student'
  });

  const switchRole = (r) => {
    setRole(r);
    if (mode === 'login') {
      setForm({...form, username: r === 'student' ? 'student' : 'teacher', password: '123456'});
    } else {
      setRegisterForm({...registerForm, role: r});
    }
    setError('');
  };

  const switchMode = (m) => {
    setMode(m);
    setError('');
    if (m === 'login') {
      setForm({username: role === 'student' ? 'student' : 'teacher', password: '123456'});
    } else {
      setRegisterForm({name: '', password: '', confirm: '', role: role});
    }
  };

  const submit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      const d = await post('/login', {...form, role});
      localStorage.setItem('mainrag-user', JSON.stringify(d.user));
      history.replaceState({}, '', `/${role}/home`);
      onLogin(d.user);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    if (registerForm.password !== registerForm.confirm) {
      setError('两次密码输入不一致');
      return;
    }
    if (!registerForm.name || !registerForm.password) {
      setError('请填写完整信息');
      return;
    }
    setLoading(true);
    try {
      await post('/register', {
        name: registerForm.name,
        password: registerForm.password,
        role: registerForm.role
      });
      // 注册成功，自动切换到登录并填入账号
      setMode('login');
      const autoUsername = registerForm.role === 'student' ? `s_${registerForm.name}` : `t_${registerForm.name}`;
      setForm({username: autoUsername, password: registerForm.password});
      setError(`注册成功！你的登录账号是：${autoUsername}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-brand">
        <div className="brand-mark"><GraduationCap/></div>
        <div><b>知问课堂</b><span>轻量教学智能体</span></div>
      </div>
      <div className="login-copy">
        <span className="eyebrow"><Sparkles size={15}/> AI 驱动的个性化学习</span>
        <h1>让每一次提问<br/>都成为<span>成长的起点</span></h1>
        <p>连接课程知识与学习过程，为教师提供洞察，为学生提供随时可用的智能辅导。</p>
        <div className="feature-row">
          <i><Database/><span>课程知识库<small>统一沉淀教学资料</small></span></i>
          <i><Bot/><span>智能问答<small>答案有据可循</small></span></i>
          <i><ChartNoAxesCombined/><span>学情洞察<small>看见每一步成长</small></span></i>
        </div>
      </div>
      <form className="login-card" onSubmit={mode === 'login' ? submit : handleRegister}>
        <div className="mobile-logo"><GraduationCap/> 知问课堂</div>
        <h2>{mode === 'login' ? '欢迎回来' : '创建账号'}</h2>
        <p>{mode === 'login' ? '选择你的身份，开始今天的学习旅程' : '注册后即可使用知问课堂'}</p>

        {/* 角色选择 */}
        <div className="role-tabs" style={{ marginBottom: '12px' }}>
          <button type="button" className={role === 'student' ? 'active' : ''} onClick={() => switchRole('student')}><GraduationCap/>学生端</button>
          <button type="button" className={role === 'teacher' ? 'active' : ''} onClick={() => switchRole('teacher')}><Users/>教师端</button>
        </div>

        {mode === 'login' ? (
          <>
            <label>账号
              <input value={form.username} onChange={e => setForm({...form, username: e.target.value})} />
            </label>
            <label>密码
              <input type="password" value={form.password} onChange={e => setForm({...form, password: e.target.value})} />
            </label>
            <div className="role-tabs" style={{ marginBottom: '12px' }}>
              <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => switchMode('login')}>登录</button>
              <button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => switchMode('register')}>注册</button>
            </div>
            <button className="primary login-btn" disabled={loading}>
              {loading ? '正在登录…' : '进入知问课堂'}
              <ChevronRight size={18}/>
            </button>
            <small className="hint">演示账号：{role} / 123456</small>
          </>
        ) : (
          <>
            <label>姓名
              <input value={registerForm.name} onChange={e => setRegisterForm({...registerForm, name: e.target.value})} placeholder="请输入您的姓名（作为登录账号）" />
            </label>
            <label>密码
              <input type="password" value={registerForm.password} onChange={e => setRegisterForm({...registerForm, password: e.target.value})} placeholder="至少6位" />
            </label>
            <label>确认密码
              <input type="password" value={registerForm.confirm} onChange={e => setRegisterForm({...registerForm, confirm: e.target.value})} placeholder="再次输入密码" />
            </label>
            <div className="role-tabs" style={{ marginBottom: '12px' }}>
              <button type="button" className={mode === 'login' ? 'active' : ''} onClick={() => switchMode('login')}>登录</button>
              <button type="button" className={mode === 'register' ? 'active' : ''} onClick={() => switchMode('register')}>注册</button>
            </div>
            <button className="primary login-btn" disabled={loading}>
              {loading ? '注册中…' : '注册新账号'}
              <ChevronRight size={18}/>
            </button>
          </>
        )}

        {error && <div className="error">{error}</div>}
      </form>
    </div>
  );
}
const navs={student:[['dashboard','学习首页',LayoutDashboard],['knowledge','课程资料',Database],['exams','练习中心',ClipboardList],['wrongbook','错题本',AlertCircle],['chat','智能问答',MessageCircle],['analysis','我的学情',ChartNoAxesCombined]],teacher:[['dashboard','教学概览',LayoutDashboard],['knowledge','知识库',Database],['exams','习题管理',ClipboardList],['grading','试卷批改',CheckCircle2],['chat','问答助手',MessageCircle],['analysis','班级学情',ChartNoAxesCombined]]};
const pageSlug={dashboard:'home',knowledge:'knowledge',exams:'exams',grading:'grading',wrongbook:'wrongbook',chat:'chat',analysis:'analysis'};
const slugPage={home:'dashboard',knowledge:'knowledge',exams:'exams',grading:'grading',wrongbook:'wrongbook',chat:'chat',analysis:'analysis'};
function initialPage(role){const [pathRole,slug]=location.pathname.split('/').filter(Boolean);const page=slugPage[slug];return pathRole===role&&page&&navs[role].some(item=>item[0]===page)?page:'dashboard'}
function Shell({ user, onLogout }) {
  const [page, setPageState] = useState(() => initialPage(user.role)), [open, setOpen] = useState(false); const setPage = (next) => { setPageState(next); history.pushState({}, '', `/${user.role}/${pageSlug[next]}`) }; useEffect(() => { const pop = () => setPageState(initialPage(user.role)); addEventListener('popstate', pop); return () => removeEventListener('popstate', pop) }, [user.role]); const title = navs[user.role].find(n => n[0] === page)?.[1]; return <div className="app"><aside className={open ? 'open' : ''}><div className="logo"><div className="brand-mark"><GraduationCap /></div><span><b>知问课堂</b><small>TEACHING AGENT</small></span><button className="close" onClick={() => setOpen(false)}><X /></button></div><div className="side-label">{user.role === 'teacher' ? '教师工作台' : '学习空间'}</div><nav>{navs[user.role].map(([id, label, Icon]) => <button key={id} className={page === id ? 'active' : ''} onClick={() => { setPage(id); setOpen(false) }}><Icon />{label}</button>)}</nav><div className="side-user"><CircleUserRound /><span><b>{user.name}</b><small>{user.role === 'teacher' ? '计算机网络 · 教师' : '计算机网络 · 2023级'}</small></span><button onClick={onLogout}><LogOut /></button></div></aside><main>
    <header>
      <button className="hamburger" onClick={() => setOpen(true)}><Menu /></button>
      <div style={{ flex: 1 }}>
        <div>
          <small>{user.role === 'teacher' ? '教师工作台' : '我的学习空间'}</small>
          <h2 style={{ display: 'flex', alignItems: 'center', gap: '10px', margin: 0 }}>
            {title}
          </h2>
        </div>
      </div>

      {/* 刷新按钮保留 */}
      <button
        onClick={() => window.location.reload()}
        style={{
          background: 'transparent',
          border: 'none',
          cursor: 'pointer',
          color: '#9aa2b0',
          padding: '6px',
          display: 'flex',
          alignItems: 'center',
          borderRadius: '6px',
          transition: 'all 0.2s',
          marginRight: '12px',
        }}
        onMouseEnter={(e) => { e.currentTarget.style.background = '#f0f2f5'; e.currentTarget.style.color = '#5c74e4'; }}
        onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#9aa2b0'; }}
        title="刷新当前页面"
      >
        <RefreshCw size={18} />
      </button>

      <div className="header-user">
        <span>{user.name.slice(0, 1)}</span>
        <b>{user.name}</b>
      </div>
    </header>
    <ErrorBoundary resetKey={page}>
      <div className="content">
        {page === 'dashboard' ? <Dashboard user={user} go={setPage} /> : page === 'chat' ? <Chat user={user} /> : page === 'knowledge' ? <Knowledge user={user} /> : page === 'exams' ? <Exams user={user} /> : page === 'grading' ? <TeacherGrading /> : page === 'wrongbook' ? <Wrongbook user={user} /> : <Analysis role={user.role} />}
      </div>
    </ErrorBoundary></main></div>
}
class ErrorBoundary extends React.Component{constructor(props){super(props);this.state={error:null}}static getDerivedStateFromError(error){return{error}}componentDidUpdate(prev){if(prev.resetKey!==this.props.resetKey&&this.state.error){sessionStorage.removeItem('mainrag-error-refreshing');this.setState({error:null})}}componentDidCatch(){if(!sessionStorage.getItem('mainrag-error-refreshing')){sessionStorage.setItem('mainrag-error-refreshing','1');setTimeout(()=>location.reload(),80)}}componentDidMount(){sessionStorage.removeItem('mainrag-error-refreshing')}render(){if(this.state.error)return null;return this.props.children}}
function Stat({icon:Icon,label,value,detail,tone}){return <div className={'stat '+tone}><div className="stat-icon"><Icon/></div><div><small>{label}</small><strong>{value}</strong><span>{detail}</span></div></div>}
function Dashboard({user, go}) {
  const role = user.role;
  const [data, setData] = useState(null);
  
  useEffect(() => {
    request(role === 'teacher' ? '/analysis/class' : '/analysis/student')
      .then(setData);
  }, [role]);
  
  const s = data?.summary || {};
  
  return (
    <>
      <section className="welcome">
        <div>
          <span className="eyebrow"><Sparkles size={14} />{role === 'teacher' ? '智能教学助手' : '今日学习建议'}</span>
          <h1>下午好，{user.name} 👋</h1>
          <p>{role === 'teacher' ? '班级整体表现平稳，建议重点关注薄弱知识点。' : '保持好奇，今天也从一个好问题开始吧。'}</p>
        </div>
        <div className="welcome-right">
          <img src={WelcomeLearning} alt="学习插画" className="welcome-illustration" />
          <button className="primary" onClick={() => go('chat')}><MessageCircle />开始问答</button>
        </div>  {/* 👈 这个 </div> 要存在 */}
      </section>
      <div className="stats">
        <Stat icon={role === 'teacher' ? Users : ChartNoAxesCombined}
          label={role === 'teacher' ? '参与学生' : '平均掌握度'}
          value={role === 'teacher' ? (data?.students?.length || 0) + ' 人' : (s.average || 0) + '%'}
          detail="较上周稳步提升" tone="blue" />
        <Stat icon={MessageCircle} label="问答次数" value={s.questions || 0} detail="智能体已记录" tone="violet" />
        <Stat icon={Database} label="知识资料" value={s.documents || 0} detail="已建立检索索引" tone="green" />
        <Stat icon={BookOpen} label="学习记录" value={s.activities || 0} detail="持续积累中" tone="orange" />
      </div>
      <div className="dashboard-grid">
        <section className="panel chart-panel">
          <div className="panel-head">
            <div><h3>{role === 'teacher' ? '班级学习趋势' : '近期学习表现'}</h3><p>学习活动得分变化</p></div>
          </div>
          <div className="chart">
            <ResponsiveContainer>
              <AreaChart data={data?.trend || []}>
                <defs>
                  <linearGradient id="fill" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor="#5577ee" stopOpacity=".3"/>
                    <stop offset="1" stopColor="#5577ee" stopOpacity="0"/>
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="#eef1f7" vertical={false}/>
                <XAxis dataKey="date" axisLine={false} tickLine={false}/>
                <YAxis domain={[0,100]} axisLine={false} tickLine={false}/>
                <Tooltip/>
                <Area type="monotone" dataKey="score" stroke="#5577ee" strokeWidth={3} fill="url(#fill)"/>
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </section>
        <section className="panel quick">
          <div className="panel-head">
            <div><h3>快捷入口</h3><p>继续你的工作</p></div>
          </div>
          {(role === 'teacher' 
            ? [['knowledge','上传课程资料',Upload,'让智能体掌握新内容'],['analysis','查看班级学情',ChartNoAxesCombined,'定位班级薄弱点'],['chat','体验智能问答',Bot,'检验知识库效果']]
            : [['chat','向智能体提问',Bot,'获得基于课程的解答'],['chat','检索并询问知识',Search,'从课程资料中获得答案'],['analysis','查看我的学情',ChartNoAxesCombined,'了解优势与不足']]
          ).map(([p,t,I,d]) => (
            <button onClick={() => go(p)} key={p}>
              <i><I/></i>
              <span><b>{t}</b><small>{d}</small></span>
              <ChevronRight/>
            </button>
          ))}
        </section>
      </div>
    </>
  );
}
function renderInlineMarkdown(text){
  const parts=String(text||'').split(/(\*\*[^*]+\*\*)/g);
  return parts.map((part,i)=>part.startsWith('**')&&part.endsWith('**')?<strong key={i}>{part.slice(2,-2)}</strong>:part)
}
function SourceSup({source,index,onSourceClick}){
  if(!source)return null;
  return <sup className="source-sup" title={`来源 ${index+1}：${source.document}`} onClick={e=>{e.stopPropagation();onSourceClick?.(source)}}>[{index+1}]</sup>
}
function SourceSups({items=[],onSourceClick}){
  if(!items.length)return null;
  return <span className="source-sup-group">{items.map(({source,index})=><SourceSup key={index} source={source} index={index} onSourceClick={onSourceClick}/>)}</span>
}
function MarkdownText({text,sources=[],onSourceClick}){
  const cleanText=String(text||'').replace(/\n?\s*(参考资料|参考来源|资料来源|来源)\s*[:：][\s\S]*$/,'');
  const lines=cleanText.split('\n');
  const parsed=[];
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
      parsed.push({type:'ol',items});
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
      parsed.push({type:'ul',items});
      continue;
    }
    const heading=line.match(/^\s*#{1,3}\s+(.+)$/);
    if(heading){parsed.push({type:'heading',text:heading[1]});i++;continue}
    const paragraph=[];
    while(i<lines.length&&lines[i].trim()&&!/^\s*\d+[.)、]\s+/.test(lines[i])&&!/^\s*[-*]\s+/.test(lines[i])&&!/^\s*#{1,3}\s+/.test(lines[i])){paragraph.push(lines[i]);i++}
    parsed.push({type:'p',text:paragraph.join('\n')});
  }
  const citeTargets=parsed.map((block,index)=>block.type==='heading'?null:index).filter(index=>index!==null);
  const groups=parsed.map(()=>[]);
  if(citeTargets.length&&sources.length){
    sources.forEach((source,index)=>{
      const target=citeTargets[Math.min(index,citeTargets.length-1)];
      groups[target].push({source,index});
    });
  }
  const blocks=parsed.map((block,index)=>{
    const cites=<SourceSups items={groups[index]} onSourceClick={onSourceClick}/>;
    if(block.type==='ol')return <React.Fragment key={index}><ol>{block.items.map((item,j)=><li key={j}>{renderInlineMarkdown(item)}</li>)}</ol>{cites}</React.Fragment>;
    if(block.type==='ul')return <React.Fragment key={index}><ul>{block.items.map((item,j)=><li key={j}>{renderInlineMarkdown(item)}</li>)}</ul>{cites}</React.Fragment>;
    if(block.type==='heading')return <h4 key={index}>{renderInlineMarkdown(block.text)}</h4>;
    return <p key={index}>{renderInlineMarkdown(block.text)}{cites}</p>;
  });
  return <div className="markdown-body">{blocks}</div>
}
function formatSourceTime(seconds){
  const value=Math.max(0,Number(seconds)||0);
  const minutes=Math.floor(value/60);
  const rest=Math.floor(value%60);
  return `${String(minutes).padStart(2,'0')}:${String(rest).padStart(2,'0')}`
}
function sourceLocationLabel(source){
  if(source?.start_time!==undefined&&source?.start_time!==null&&source?.end_time!==undefined&&source?.end_time!==null){
    return `${formatSourceTime(source.start_time)} - ${formatSourceTime(source.end_time)}`
  }
  return source?.page?`第 ${source.page} 页`:`片段 ${source?.chunk||''}`
}
function parseMediaCaptions(content=''){
  const pattern=/\[\[TIME:(\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\]\]([\s\S]*?)(?=\[\[TIME:|$)/g;
  const rows=[];
  let match;
  while((match=pattern.exec(content||''))){
    const text=match[3].replace(/\[\[PAGE:\d+\]\]/g,'').replace(/音视频转写内容：?/g,'').trim();
    if(text)rows.push({start:Number(match[1]),end:Number(match[2]),text});
  }
  return rows;
}
function Chat({user}){
  const welcome={role:'ai',text:`你好，${user.name}！我是知问课堂智能体。你可以问我课程概念、知识区别或应用问题，我会从课程知识库中寻找依据。`};
  const [messages,setMessages]=useState([welcome]),[input,setInput]=useState(''),[loading,setLoading]=useState(false),[photoLoading,setPhotoLoading]=useState(false),[photoPreview,setPhotoPreview]=useState(null),[historyItems,setHistoryItems]=useState([]),[activeHistory,setActiveHistory]=useState('');
  const photoInputRef=useRef(null);
  useEffect(()=>()=>{if(photoPreview?.url)URL.revokeObjectURL(photoPreview.url)},[photoPreview?.url]);
  const loadHistory=()=>request(`/chat/history?student=${encodeURIComponent(user.name)}&limit=20`).then(d=>setHistoryItems(d.items||[])).catch(()=>{});
  useEffect(loadHistory,[user.name]);
  const openHistory=item=>{setActiveHistory(item.id);setMessages([welcome,{role:'user',text:item.question},{role:'ai',text:item.answer,sources:item.sources||[]}])};
  const deleteHistory=async(e,item)=>{e.stopPropagation();if(!confirm('确定删除这条历史问答吗？'))return;await request(`/chat/history/${encodeURIComponent(item.id)}?student=${encodeURIComponent(user.name)}`,{method:'DELETE'});setHistoryItems(items=>items.filter(x=>x.id!==item.id));if(activeHistory===item.id){setActiveHistory('');setMessages([welcome])}};
  const appendToLastAi=(patch)=>setMessages(items=>items.map((m,i)=>i===items.length-1&&m.role==='ai'?{...m,...patch,text:(patch.append?m.text+patch.append:patch.text??m.text)}:m));
  const openSource=s=>{if(!s?.document_id)return;const params=new URLSearchParams({doc:s.document_id,page:String(s.page||''),chunk:String(s.chunk||'')});if(s.start_time!==undefined&&s.start_time!==null)params.set('start',String(s.start_time));if(s.end_time!==undefined&&s.end_time!==null)params.set('end',String(s.end_time));location.assign(`/${user.role}/knowledge?${params.toString()}`)};
  const send=async(q=input)=>{
    if(!q.trim()||loading)return;
    const question=q.trim();
    setActiveHistory('');
    setMessages(m=>[...m,{role:'user',text:question},{role:'ai',text:'',sources:[],streaming:true}]);
    setInput('');
    setPhotoPreview(old=>{if(old?.url)URL.revokeObjectURL(old.url);return null});
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
  const photoSearch=async(e)=>{
    const file=e.target.files?.[0];
    if(!file||loading||photoLoading)return;
    e.target.value='';
    const previewUrl=URL.createObjectURL(file);
    setPhotoPreview(old=>{if(old?.url)URL.revokeObjectURL(old.url);return {url:previewUrl,name:file.name,ocrText:'',status:'正在扫描图片文字…'}});
    setActiveHistory('');
    setPhotoLoading(true);
    setMessages(m=>[...m,{role:'user',text:`拍照搜题：${file.name}`,image:previewUrl},{role:'ai',text:'正在识别题目并检索课程知识库…',sources:[],streaming:true}]);
    try{
      let role='';try{role=JSON.parse(localStorage.getItem('mainrag-user'))?.role||''}catch{}
      const fd=new FormData();
      fd.append('student',user.name);
      fd.append('file',file);
      const response=await fetch(API+'/chat/photo-search',{method:'POST',headers:{...(role?{'X-Role':role}:{})},body:fd});
      let data={};try{data=await response.json()}catch{data={detail:await response.text().catch(()=> '')}}
      if(!response.ok)throw new Error(data.detail||'拍照搜题失败');
      setPhotoPreview(old=>old?{...old,ocrText:data.ocr_text||'',status:'识别完成，可在输入框中修改题目文字'}:old);
      setMessages(items=>items.map((m,i)=>i===items.length-2&&m.role==='user'?{...m,ocrText:data.ocr_text||''}:m));
      appendToLastAi({text:`**识别题目：**\n${data.ocr_text}\n\n${data.answer}`,sources:data.sources||[],streaming:false});
      loadHistory();
    }catch(error){
      setPhotoPreview(old=>old?{...old,status:'识别失败',ocrText:error.message}:old);
      setMessages(items=>items.map((m,i)=>i===items.length-2&&m.role==='user'?{...m,ocrText:error.message}:m));
      appendToLastAi({text:error.message,streaming:false});
    }finally{
      setPhotoPreview(old=>{if(old?.url)URL.revokeObjectURL(old.url);return null});
      setInput('');
      setPhotoLoading(false);
    }
  };
  return <div className="chat-layout"><section className="chat-box"><div className="chat-top"><div className="bot-avatar"><Bot/></div> <div><b>课程智能体</b><small><i/>在线 · 基于知识库回答 · 流式输出 · 支持拍照搜题</small></div></div><div className="messages">{messages.map((m,i)=><div className={'message '+m.role} key={i}>{m.role==='ai'&&<div className="avatar"><Sparkles/></div>}<div><div className={'bubble '+(m.streaming?'streaming':'')}>{m.image&&<img className="chat-photo-thumb" src={m.image} alt="拍照搜题图片"/>}{m.ocrText&&<div className="chat-ocr-text"><b>识别文字</b><p>{m.ocrText}</p></div>}{m.role==='ai'?<MarkdownText text={m.text} sources={m.sources||[]} onSourceClick={openSource}/>:m.text}{m.streaming&&<span className="stream-cursor">|</span>}</div>{m.sources?.length>0&&<div className="sources"><b><FileText/>参考来源</b>{m.sources.map((s,j)=><button className="source-link" key={j} onClick={()=>openSource(s)} title={`来源 ${j+1}：点击跳转到对应文档和位置`}><i className="source-index">{j+1}</i><span>{s.document} · {sourceLocationLabel(s)}</span><em>{Math.round(s.score*100)}%</em></button>)}</div>}</div></div>)}</div><div className="composer">{photoPreview&&<div className="photo-preview-card"><img src={photoPreview.url} alt={photoPreview.name}/><div><b>{photoPreview.name}</b><small>{photoPreview.status}</small><p>{photoPreview.ocrText||'正在识别图片文字，结果会显示在对话中的图片下方。'}</p></div><button type="button" onClick={()=>{setPhotoPreview(old=>{if(old?.url)URL.revokeObjectURL(old.url);return null})}}><X/></button></div>}<div><button className="photo-search-btn" type="button" onClick={()=>photoInputRef.current?.click()} disabled={loading||photoLoading} title="拍照搜题 / 上传题目图片"><Camera/></button><input ref={photoInputRef} className="photo-search-input" type="file" accept="image/*" capture="environment" onChange={photoSearch}/><textarea placeholder={photoLoading?'正在识别题目，请稍候…':'输入你的问题，Enter 发送…'} value={input} onChange={e=>setInput(e.target.value)} onKeyDown={e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}}/><button onClick={()=>send()} disabled={loading||photoLoading}><Send/></button></div><small>回答由课程知识库生成，支持 Markdown 渲染；拍照搜题会先 OCR 识别，再检索知识库解答</small></div></section><aside className="suggestions chat-side"><div className="side-block"><h3><Sparkles/>试试这样问</h3>{['TCP 如何保证可靠传输？','HTTP 和 HTTPS 有什么区别？','什么是数据库事务的 ACID？','IPv4 与 IPv6 的主要区别？'].map(x=><button key={x} onClick={()=>send(x)}>{x}<ChevronRight/></button>)}</div><div className="side-block history-block"><h3><MessageCircle/>历史问答</h3>{historyItems.length===0?<p className="empty-history">暂无历史记录，提问后会自动保存。</p>:historyItems.map(item=><button className={activeHistory===item.id?'active':''} key={item.id} onClick={()=>openHistory(item)}><span className="history-text"><b>{item.question}</b><small>{item.topic} · {item.at?.replace('T',' ')}</small></span><i className="history-delete" title="删除历史问答" onClick={e=>deleteHistory(e,item)}><Trash2 size={15}/></i></button>)}</div><div className="tip"><BookOpen/><b>提问小技巧</b><p>问题越具体，检索到的课程内容越准确；拍照搜题建议拍清题干和选项。</p></div></aside></div>
}
function Knowledge({ user }) {
  const isTeacher = user.role === 'teacher';
  const [docs, setDocs] = useState([]), [selected, setSelected] = useState(null), [uploading, setUploading] = useState(false), [reindexing, setReindexing] = useState(false), [progress, setProgress] = useState(0), [stage, setStage] = useState(''), [uploadName, setUploadName] = useState(''), [msg, setMsg] = useState(''), [searchTerm, setSearchTerm] = useState('');
  const [targetPage, setTargetPage] = useState('');
  const [targetTime, setTargetTime] = useState(null);
  const [activeCaption, setActiveCaption] = useState(-1);
  const mediaRef = useRef(null);
  const captionListRef = useRef(null);
  const load = (fresh = false) => request('/knowledge', { cache: !fresh }).then(d => setDocs(d.items));
  useEffect(load, []);
  useEffect(() => { const params = new URLSearchParams(location.search); const target = params.get('doc'); const page = params.get('page') || ''; const start = params.get('start'); setTargetPage(page); setTargetTime(start !== null && start !== '' ? Number(start) : null); if (target) view(target, page) }, []);
  useEffect(() => { if (!docs.some(d => d.preview_status === 'processing')) return; const timer = setInterval(() => load(true), 3000); return () => clearInterval(timer) }, [docs]);
  useEffect(() => { if (!selected || selected.preview_status !== 'processing') return; const timer = setInterval(() => request('/knowledge/' + selected.id, { cache: false }).then(setSelected).catch(() => { }), 3000); return () => clearInterval(timer) }, [selected]);
  useEffect(() => { const player = mediaRef.current; if (!player || targetTime === null || Number.isNaN(targetTime)) return; const seek = () => { player.currentTime = Math.max(0, targetTime); player.play().catch(() => setMsg(`已定位到 ${formatSourceTime(targetTime)}，如未自动播放请点击播放器。`)) }; if (player.readyState >= 1) seek(); else player.addEventListener('loadedmetadata', seek, { once: true }); return () => player.removeEventListener('loadedmetadata', seek) }, [selected, targetTime]);
  const captions = useMemo(() => selected?.source_kind === 'media' ? parseMediaCaptions(selected.content) : [], [selected]);
  useEffect(() => { setActiveCaption(-1) }, [selected?.id]);
  useEffect(() => { const player = mediaRef.current; if (!player || !captions.length) return; const update = () => { const time = player.currentTime; const index = captions.findIndex(item => time >= item.start && time < Math.max(item.end, item.start + .5)); setActiveCaption(index) }; player.addEventListener('timeupdate', update); player.addEventListener('seeked', update); update(); return () => { player.removeEventListener('timeupdate', update); player.removeEventListener('seeked', update) } }, [captions, selected]);
  useEffect(() => { if (activeCaption < 0 || !captionListRef.current) return; const item = captionListRef.current.querySelector(`[data-caption-index="${activeCaption}"]`); item?.scrollIntoView({ block: 'center', behavior: 'smooth' }) }, [activeCaption]);
  const view = async (id, page = '') => { try { setTargetPage(page); setSelected(await request('/knowledge/' + id)) } catch (e) { setMsg(e.message) } };
  const download = d => { window.open(`${API}/knowledge/${d.id}/download`, '_blank') };
  const upload = e => { const file = e.target.files[0]; if (!file) return; e.target.value = ''; const isMedia = /\.(mp3|wav|m4a|aac|flac|ogg|wma|mp4|mov|avi|mkv|webm|wmv|flv)$/i.test(file.name); setUploading(true); setProgress(0); setStage('正在上传文件'); setUploadName(file.name); setMsg(''); const fd = new FormData(); fd.append('file', file); fd.append('category', '课程资料'); const xhr = new XMLHttpRequest(); let timer; xhr.open('POST', API + '/knowledge/upload'); xhr.setRequestHeader('X-Role', 'teacher'); xhr.upload.onprogress = event => { if (event.lengthComputable) setProgress(Math.round(event.loaded / event.total * 65)) }; xhr.upload.onload = () => { setProgress(p => Math.max(p, 66)); setStage(isMedia ? '正在转写音视频并建立向量索引' : '正在解析文档并建立向量索引'); timer = setInterval(() => setProgress(p => p < 94 ? p + 1 : p), 700) }; xhr.onload = () => { clearInterval(timer); let data = {}; try { data = JSON.parse(xhr.responseText) } catch { } if (xhr.status >= 200 && xhr.status < 300) { setProgress(100); setStage(isMedia ? '上传完成，音视频已转写入库' : '上传完成，预览后台处理中'); setMsg(data.message || (isMedia ? '上传成功，音视频已转写并可用于检索问答' : '上传成功，预览正在后台生成')); load(true); setTimeout(() => setUploading(false), 800) } else { setUploading(false); setMsg(data.detail || '上传处理失败') } }; xhr.onerror = () => { clearInterval(timer); setUploading(false); setMsg('网络错误，上传失败') }; xhr.send(fd) };
  const del = async id => { if (!confirm('确定删除这份资料吗？')) return; await request('/knowledge/' + id, { method: 'DELETE' }); if (selected?.id === id) setSelected(null); load(true) };
  const reindex = async () => { setReindexing(true); setMsg(''); try { const d = await post('/knowledge/reindex', {}); setMsg(`${d.message}：${d.documents} 个文档，${d.chunks} 个向量片段`); load(true) } catch (e) { setMsg(e.message) } finally { setReindexing(false) } };
  const previewText = d => d.source_kind === 'media' ? '可播放' : d.preview_status === 'processing' ? '正在处理预览' : (d.has_preview || d.preview_status === 'ready') ? '可查看' : d.preview_status === 'failed' ? '预览失败' : '暂无预览';
  const canPreview = d => d.source_kind === 'media' || d.has_preview || d.preview_status === 'ready';
  const fileExt = d => {
    const raw = ((d?.extension || '') + '').replace(/^\./, '').toUpperCase();
    if (raw) return raw;
    const match = ((d?.name || d?.stored_path || '') + '').match(/\.([a-z0-9]+)$/i);
    return match ? match[1].toUpperCase() : '';
  };
  const isVideo = d => ['MP4', 'MOV', 'AVI', 'MKV', 'WEBM', 'WMV', 'FLV', 'M4V'].includes(fileExt(d)) || /^video\//i.test((d?.mime_type || d?.media_type || d?.type || '') + '');
  const isAudio = d => ['MP3', 'WAV', 'M4A', 'AAC', 'FLAC', 'OGG', 'WMA', 'OPUS'].includes(fileExt(d)) || /^audio\//i.test((d?.mime_type || d?.media_type || d?.type || '') + '');
  const fileTypeLabel = d => isVideo(d) ? '视频' : isAudio(d) ? '音频' : (fileExt(d) || ((d?.type || '资料') + '').toUpperCase());
  const fileTypeClass = d => isVideo(d) ? 'video' : isAudio(d) ? 'audio' : ['PPT', 'PPTX'].includes(fileExt(d)) ? 'ppt' : ['DOC', 'DOCX'].includes(fileExt(d)) ? 'word' : fileExt(d) === 'PDF' ? 'pdf' : 'other';
  const jumpCaption = item => { const player = mediaRef.current; if (!player) return; player.currentTime = Math.max(0, item.start); player.play().catch(() => { }) };
  const captionPanel = captions.length > 0 && <div className="caption-panel"><div className="caption-head"><b>滚动字幕</b><span>{activeCaption >= 0 ? `${formatSourceTime(captions[activeCaption].start)} - ${formatSourceTime(captions[activeCaption].end)}` : '播放时自动定位'}</span></div><div className="caption-list" ref={captionListRef}>{captions.map((item, index) => <button type="button" data-caption-index={index} className={index === activeCaption ? 'active' : ''} key={`${item.start}-${index}`} onClick={() => jumpCaption(item)}><em>{formatSourceTime(item.start)}</em><span>{item.text}</span></button>)}</div></div>;
  // 实时筛选：输入即变化
  const filteredDocs = docs.filter(d => d.name.toLowerCase().includes(searchTerm.toLowerCase()));
  const clearSearch = () => setSearchTerm('');
  return <>
    <section className="knowledge-head">
      <div>
        <span className="eyebrow"><Database size={15} />{isTeacher ? '知识中枢' : '课程资源'}</span>
        <h1>{isTeacher ? '课程知识库' : '我的课程资料'}</h1>
        <p>{isTeacher ? '上传、查看和管理课程资料，文件会自动建立向量索引，原版式预览会在后台生成。' : '查看教师上传的课程文档，预览处理完成后即可打开原版式资料。'}</p>
      </div>
      {isTeacher && <div className="knowledge-actions">
        <button className="secondary-btn" onClick={reindex} disabled={reindexing || uploading}><Sparkles />{reindexing ? '正在重建…' : '重建向量索引'}</button>
        <label className="primary upload-btn"><Upload />{uploading ? '正在处理…' : '上传资料'}<input type="file" accept=".doc,.docx,.ppt,.pptx,.pdf,.mp3,.wav,.m4a,.aac,.flac,.ogg,.wma,.mp4,.mov,.avi,.mkv,.webm,.wmv,.flv" onChange={upload} disabled={uploading} /></label>
      </div>}
    </section>
    {uploading && <div className="upload-progress"><div className="progress-file"><i><FileText /></i><img src={UploadCloud} alt="上传中" className="upload-cloud-icon" /><span><b>{uploadName}</b><small>{stage}</small></span><strong>{progress}%</strong></div><div className="progress-track"><i style={{ width: progress + '%' }} /></div></div>}
    {msg && <div className="notice">{msg}</div>}
    <div className="kb-summary">
      <div><Database /><span><b>{filteredDocs.length}</b><small>知识文档</small></span></div>
      <div><FileText /><span><b>{filteredDocs.reduce((n, d) => n + d.chunks, 0)}</b><small>向量片段</small></span></div>
      <div><Sparkles /><span><b>{filteredDocs.filter(d => d.preview_status === 'processing').length}</b><small>预览处理中</small></span></div>
    </div>
    <div className="knowledge-search">
      <input
        type="text"
        placeholder="搜索资料名称..."
        value={searchTerm}
        onChange={(e) => setSearchTerm(e.target.value)}
        className="search-input"
      />
      <button className="search-btn" onClick={clearSearch} title="清空搜索">
        {searchTerm ? <X size={18} /> : <Search size={18} />}
      </button>
    </div>
    <section className="panel table-panel">
      <div className="panel-head"><div><h3>{isTeacher ? '全部资料' : '教师共享资料'}</h3><p>支持 DOC、DOCX、PPT、PPTX、PDF、音频和视频</p></div></div>
      <div className="doc-table">
        <div className="tr th"><span>资料名称</span><span>分类</span><span>片段</span><span>上传时间</span><span>预览</span></div>
        {filteredDocs.length === 0 ? (
          <div className="empty-state">
            <img src={EmptyFolder} alt={searchTerm ? "未找到匹配资料" : "暂无资料"} className="empty-illustration" />
            <h3>{searchTerm ? '未找到匹配资料' : '还没有资料'}</h3>
            <p>{searchTerm ? `没有包含“${searchTerm}”的资料，试试其他关键词` : (isTeacher ? '点击右上角「上传资料」按钮添加课程资料' : '教师上传课程资料后，这里就会显示啦')}</p>
          </div>
        ) : (
          filteredDocs.map(d => (
            <div className="tr" key={d.id}>
              <span className="doc-name"><i><FileText /></i><b>{d.name}<small>{d.size} KB</small></b></span>
              <span>
                <em className={`tag file-type ${fileTypeClass(d)}`}>
                  {fileTypeLabel(d) === 'PDF' && <File size={10} style={{ marginRight: 2 }} />}
                  {['PPT', 'PPTX'].includes(fileExt(d)) && <File size={10} style={{ marginRight: 2 }} />}
                  {['DOC', 'DOCX'].includes(fileExt(d)) && <FileText size={10} style={{ marginRight: 2 }} />}
                  {fileTypeLabel(d) === '视频' && <Video size={10} style={{ marginRight: 2 }} />}
                  {fileTypeLabel(d) === '音频' && <Music size={10} style={{ marginRight: 2 }} />}
                  {!['PDF', 'PPT', 'PPTX', 'DOC', 'DOCX', '视频', '音频'].includes(fileTypeLabel(d)) && <File size={10} style={{ marginRight: 2 }} />}
                  {fileTypeLabel(d)}
                </em>
              </span>
              <span>{d.chunks}</span>
              <span>{d.created_at}</span>
              <span className="doc-actions">
                <button className={'view-doc preview-action ' + (d.preview_status || '')} onClick={() => view(d.id)} disabled={!canPreview(d)}>{canPreview(d) ? <Eye size={14} /> : <AlertCircle />}{previewText(d)}</button>
                <button className="download-doc" onClick={() => download(d)} title="下载原始资料"><Upload />下载</button>
                {isTeacher && <button className="trash" onClick={() => del(d.id)}><Trash2 /></button>}
              </span>
            </div>
          ))
        )}
      </div>
    </section>
    {selected && <section className="panel document-reader">
      <div className="reader-head"><div><span className="eyebrow"><FileText size={14} />{selected.type}</span><h2>{selected.name}</h2><p>{selected.created_at} · {selected.size} KB{targetPage ? ` · 已定位到第 ${targetPage} 页` : ''}{targetTime !== null && !Number.isNaN(targetTime) ? ` · 已定位到 ${formatSourceTime(targetTime)}` : ''}</p></div><button onClick={() => setSelected(null)}><X /></button></div>
      {selected.source_kind === 'media' && isVideo(selected)
        ? <div className="media-preview"><video ref={mediaRef} key={`${selected.id}-${targetTime ?? 'top'}`} className="media-player video-player" controls src={`${API}/knowledge/${selected.id}/media${targetTime !== null && !Number.isNaN(targetTime) ? `#t=${Math.max(0, targetTime)}` : ''}`} title={selected.name} />{captionPanel}</div>
        : selected.source_kind === 'media' && isAudio(selected)
          ? <div className="media-preview"><div className="audio-preview"><FileText /><b>{selected.name}</b><audio ref={mediaRef} key={`${selected.id}-${targetTime ?? 'top'}`} className="media-player audio-player" controls src={`${API}/knowledge/${selected.id}/media${targetTime !== null && !Number.isNaN(targetTime) ? `#t=${Math.max(0, targetTime)}` : ''}`} /></div>{captionPanel}</div>
          : selected.has_preview
            ? <iframe key={`${selected.id}-${targetPage || 'top'}`} className="document-frame" src={`${API}/knowledge/${selected.id}/preview${targetPage ? `#page=${targetPage}&zoom=page-width` : ''}`} title={selected.name} />
            : <div className="no-preview"><AlertCircle /><b>{selected.preview_status === 'processing' ? '原版式预览正在处理中' : '暂无原版式预览'}</b><p>{selected.preview_status === 'processing' ? '上传已经成功，预览文件正在后台生成，完成后预览标签会自动变为可查看。' : (selected.preview_error || '该文件暂时没有可查看的原版式预览。')}</p></div>}
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
              <XAxis type="number" domain={[0, 100]} axisLine={false} />
              <YAxis type="category" dataKey="topic" width={90} axisLine={false} tickLine={false} tick={{ fontSize: 12 }} />
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
function questionTypeText(type){return type==='choice'?'单选题':type==='fill'?'填空题':type==='solution'?'解答题':'题目'}
function TeacherExams(){
  const [docs,setDocs]=useState([]),[items,setItems]=useState([]),[form,setForm]=useState({document_id:'',chapter:'全文',title:'',count:5,difficulty:'中等',question_types:['choice','fill','solution']}),[loading,setLoading]=useState(false),[msg,setMsg]=useState(''),[preview,setPreview]=useState(null),[selected,setSelected]=useState([]);
  const load=()=>Promise.all([request('/knowledge'),request('/exams')]).then(([d,e])=>{setDocs(d.items);setItems(e.items);setForm(f=>({...f,document_id:f.document_id||d.items[0]?.id||''}))});
  useEffect(load,[]);
  const toggleType=type=>setForm(f=>{const exists=f.question_types.includes(type);const next=exists?f.question_types.filter(x=>x!==type):[...f.question_types,type];return {...f,question_types:next.length?next:[type]}});
  const openPreview=exam=>{setPreview(exam);setSelected((exam.questions||[]).map(q=>q.id));setMsg('')};
  const generate=async e=>{e.preventDefault();setLoading(true);setMsg('');try{const exam=await post('/exams/generate',{...form,count:Number(form.count)});setMsg('习题生成成功，请预览并勾选后发布。');openPreview(exam);load()}catch(e){setMsg(e.message)}finally{setLoading(false)}};
  const toggleQuestion=id=>setSelected(ids=>ids.includes(id)?ids.filter(x=>x!==id):[...ids,id]);
  const publish=async (exam=preview)=>{if(!exam)return;if(!selected.length){setMsg('请至少勾选一道习题再发布。');return}await post(`/exams/${exam.id}/publish`,{question_ids:selected});setMsg('已发布到学生端');setPreview(null);setSelected([]);load()};
  const remove=async id=>{if(!confirm('确定删除这套习题吗？'))return;await request(`/exams/${id}`,{method:'DELETE'});if(preview?.id===id){setPreview(null);setSelected([])}load()};
  return <><section className="knowledge-head"><div><span className="eyebrow"><ClipboardList size={15}/>AI 出题</span><h1>习题生成与发布</h1><p>选择知识库文件和章节，由 DeepSeek 生成单选题、填空题和解答题；教师预览勾选后再发布给学生。</p></div></section><div className="exam-layout"><form className="panel exam-form" onSubmit={generate}><div className="panel-head"><div><h3>生成新习题</h3><p>题目答案严格来自所选资料</p></div></div><label>知识库文件<select value={form.document_id} onChange={e=>setForm({...form,document_id:e.target.value})}>{docs.map(d=><option value={d.id} key={d.id}>{d.name}</option>)}</select></label><label>章节或范围<input value={form.chapter} onChange={e=>setForm({...form,chapter:e.target.value})} placeholder="例如：第三章 传输层"/></label><label>习题标题<input value={form.title} onChange={e=>setForm({...form,title:e.target.value})} placeholder="留空将自动生成"/></label><div className="form-row"><label>题目数量<input type="number" min="1" max="20" value={form.count} onChange={e=>setForm({...form,count:e.target.value})}/></label><label>难度<select value={form.difficulty} onChange={e=>setForm({...form,difficulty:e.target.value})}><option>简单</option><option>中等</option><option>困难</option></select></label></div><div className="type-picker"><b>题型</b>{[['choice','单选题'],['fill','填空题'],['solution','解答题']].map(([type,label])=><label key={type}><input type="checkbox" checked={form.question_types.includes(type)} onChange={()=>toggleType(type)}/>{label}</label>)}</div><button className="primary" disabled={loading||!form.document_id}><Sparkles/>{loading?'DeepSeek 正在生成…':'生成习题'}</button>{msg&&<div className="notice">{msg}</div>}</form><section className="panel exam-list"><div className="panel-head"><div><h3>习题列表</h3><p>共 {items.length} 套习题</p></div></div>{items.length===0?<div className="empty">还没有生成习题</div>:items.map(exam=><article className="exam-card" key={exam.id}><div className="exam-card-icon"><ClipboardList/></div><div><h4>{exam.title}</h4><p>{exam.document_name} - {exam.chapter}</p><span>{exam.questions.length} 题</span><span>{exam.difficulty}</span><em className={exam.status}>{exam.status==='published'?'已发布':'草稿'}</em></div><div className="exam-actions">{exam.status!=='published'&&<button className="publish" onClick={()=>openPreview(exam)}>预览发布</button>}<button className="trash" onClick={()=>remove(exam.id)}><Trash2/></button></div></article>)}</section></div>{preview&&<section className="panel exam-preview"><div className="panel-head"><div><h3>预览并选择发布题目</h3><p>{preview.title} - 已选择 {selected.length}/{preview.questions.length} 题</p></div><div className="preview-actions"><button className="secondary-btn" onClick={()=>setSelected(preview.questions.map(q=>q.id))}>全选</button><button className="secondary-btn" onClick={()=>setSelected([])}>清空</button><button className="primary" onClick={()=>publish(preview)}>发布所选</button><button onClick={()=>setPreview(null)}><X/></button></div></div><div className="preview-questions">{preview.questions.map((q,i)=><article className="preview-question" key={q.id}><label className="preview-check"><input type="checkbox" checked={selected.includes(q.id)} onChange={()=>toggleQuestion(q.id)}/><span>{i+1}</span><em>{questionTypeText(q.type)}</em></label><div><h4>{q.question}</h4>{q.options?.length>0&&<ul>{q.options.map(o=><li key={o}>{o}</li>)}</ul>}<p><b>答案：</b>{q.answer}</p>{q.analysis&&<p><b>解析：</b>{q.analysis}</p>}<small>{q.knowledge_point}</small></div></article>)}</div></section>}</>}
function StudentExamsLegacy({user}){const [items,setItems]=useState([]),[subs,setSubs]=useState([]),[active,setActive]=useState(null),[answers,setAnswers]=useState({}),[result,setResult]=useState(null);const [showConfirm, setShowConfirm] = useState(false);const [pendingSubmit, setPendingSubmit] = useState(null); const load=()=>Promise.all([request('/exams?published_only=true'),request(`/exams/student/submissions?student=${encodeURIComponent(user.name)}`)]).then(([e,s])=>{setItems(e.items);setSubs(s.items)});useEffect(load,[]);const submitted=id=>subs.find(s=>s.exam_id===id);const open=exam=>{setActive(exam);setAnswers({});setResult(null)};const submit = () => {
  setShowConfirm(true);
};
const doSubmit = async () => {
  setShowConfirm(false);
  const data = await post(`/exams/${active.id}/submit`, { student: user.name, answers });
  setResult(data);
  load();
};if(active)return <section className="panel take-exam"><button className="back-link" onClick={()=>setActive(null)}>← 返回练习中心</button><div className="take-head"><div><h1>{active.title}</h1><p>{active.document_name} · {active.chapter}</p></div>{result&&<strong>{result.score}/{result.total}</strong>}</div>{active.questions.map((q,i)=>{const detail=result?.details.find(d=>d.id===q.id);return <article className={'question '+(detail?(detail.correct?'correct':'wrong'):'')} key={q.id}><h3><span>{i+1}</span><em className="question-type">{questionTypeText(q.type)}</em>{q.question}</h3>{q.options?.length>0?<div className="options">{q.options.map(option=>{const value=option.match(/^([A-Za-z])\./)?.[1]||option;return <label key={option}><input type="radio" name={q.id} disabled={!!result} checked={answers[q.id]===value} onChange={()=>setAnswers({...answers,[q.id]:value})}/><span>{option}</span></label>})}</div>:q.type==='fill'?<input className="fill-answer" disabled={!!result} value={answers[q.id]||''} onChange={e=>setAnswers({...answers,[q.id]:e.target.value})} placeholder="???????"/>:<textarea disabled={!!result} value={answers[q.id]||''} onChange={e=>setAnswers({...answers,[q.id]:e.target.value})} placeholder="???????"/>}{detail&&!detail.correct&&<div className="answer-detail"><b>正确答案：{detail.answer}</b><p>{detail.analysis}</p></div>}</article>})}{!result?<button className="primary submit-exam" onClick={submit}>提交练习</button>:<button className="primary submit-exam" onClick={()=>setActive(null)}>完成并返回</button>}{showConfirm && (
  <div className="modal-overlay" onClick={() => setShowConfirm(false)}>
    <div className="modal-box" onClick={(e) => e.stopPropagation()}>
      <p style={{ fontSize: 16, marginBottom: 20 }}>确认提交本次练习吗？</p>
      <div style={{ display: 'flex', gap: 12, justifyContent: 'center' }}>
        <button className="secondary" onClick={() => setShowConfirm(false)}>取消</button>
        <button className="primary" onClick={doSubmit}>确认提交</button>
      </div>
    </div>
  </div>
)}</section>;return <><section className="analysis-title"><div><span className="eyebrow"><ClipboardList size={15}/>课程练习</span><h1>练习中心</h1><p>完成教师发布的习题，结果会自动进入学情分析和错题本。</p></div></section><div className="exercise-grid">{items.length===0?<div className="panel empty">教师还没有发布习题</div>:items.map(exam=>{const done=submitted(exam.id);return <article className="panel exercise" key={exam.id}><div className="exercise-top"><i><ClipboardList/></i><em>{exam.difficulty}</em></div><h3>{exam.title}</h3><p>{exam.document_name} · {exam.chapter}</p><div><span>{exam.questions.length} 道题</span>{done&&<span className="done"><CheckCircle2/>已完成 {done.accuracy}%</span>}</div><button onClick={()=>open(exam)}>{done?'重新练习':'开始练习'}<ChevronRight/></button></article>})}</div></>}
function StudentExams({ user }) {
  const [items, setItems] = useState([]);
  const [subs, setSubs] = useState([]);
  const [active, setActive] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [gradingMode, setGradingMode] = useState('ai');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const load = () => Promise.all([
    request('/exams?published_only=true', { cache: false }),
    request(`/exams/student/submissions?student=${encodeURIComponent(user.name)}`, { cache: false })
  ]).then(([exams, submissions]) => { setItems(exams.items); setSubs(submissions.items) });
  useEffect(() => { load() }, []);
  const submitted = id => subs.find(item => item.exam_id === id);
  const open = exam => {
    const previous = submitted(exam.id);
    setActive(exam);
    setAnswers(previous ? Object.fromEntries(previous.details.map(detail => [detail.id, detail.student_answer])) : {});
    setResult(previous || null);
    setError('');
  };
  const startAgain = () => { setAnswers({}); setResult(null); setError('') };
  const doSubmit = async () => {
    setSubmitting(true); setError('');
    try {
      const data = await post(`/exams/${active.id}/submit`, {
        student: user.name, answers, solution_grading: gradingMode
      });
      setResult(data); setShowConfirm(false); await load();
    } catch (err) { setError(err.message) } finally { setSubmitting(false) }
  };
  if (active) {
    const hasSolutions = active.questions.some(question => question.type === 'solution');
    const pending = result?.status === 'pending_teacher';
    return <section className="panel take-exam">
      <button className="back-link" onClick={() => setActive(null)}>← 返回练习中心</button>
      <div className="take-head"><div><h1>{active.title}</h1><p>{active.document_name} · {active.chapter}</p></div>{result && (pending ? <strong>待教师批改</strong> : <div className="result-celebration"><img src={EmptyCelebration} alt="完成" className="celebration-icon" /><div className="celebration-text"><span className="celebration-score">{result.score}/{result.total}</span><span className="celebration-label">🎉 练习完成！</span></div></div>)}</div>
      {pending && <div className="grading-status pending">解答题已发送到教师端。教师完成评分和评语后，这里会显示最终成绩。</div>}
      {result?.status === 'graded' && result.overall_comment && <div className="grading-status graded"><b>教师总评：</b>{result.overall_comment}</div>}
      {active.questions.map((question, index) => {
        const detail = result?.details.find(item => item.id === question.id);
        const state = detail?.grading_status === 'pending' ? 'pending' : detail ? (detail.correct ? 'correct' : 'wrong') : '';
        return <article className={`question ${state}`} key={question.id}>
          <h3><span>{index + 1}</span><em className="question-type">{questionTypeText(question.type)}</em>{question.question}</h3>
          {question.options?.length > 0 ? <div className="options">{question.options.map(option => { const value = option.match(/^([A-Za-z])\./)?.[1] || option; return <label key={option}><input type="radio" name={question.id} disabled={!!result} checked={answers[question.id] === value} onChange={() => setAnswers({ ...answers, [question.id]: value })} /><span>{option}</span></label> })}</div> : question.type === 'fill' ? <input className="fill-answer" disabled={!!result} value={answers[question.id] || ''} onChange={event => setAnswers({ ...answers, [question.id]: event.target.value })} placeholder="请输入答案" /> : <textarea disabled={!!result} value={answers[question.id] || ''} onChange={event => setAnswers({ ...answers, [question.id]: event.target.value })} placeholder="请写出解答过程和结论" />}
          {detail?.grading_status === 'graded' && <div className="answer-detail"><b>得分：{detail.score_awarded}/{detail.score}</b>{detail.feedback && <p><b>评语：</b>{detail.feedback}</p>}{detail.correct === false && detail.answer && <p><b>参考答案：</b>{detail.answer}</p>}</div>}
          {detail?.grading_status === 'pending' && <div className="answer-detail pending-detail">等待教师评分与评语</div>}
        </article>
      })}
      {error && <div className="error">{error}</div>}
      {!result ? <button className="primary submit-exam" onClick={() => setShowConfirm(true)}>提交练习</button> : <div className="submit-actions"><button className="secondary-btn" onClick={startAgain}>重新练习</button><button className="primary" onClick={() => { load(); setActive(null) }}>完成并返回</button></div>}
      {showConfirm && <div className="modal-overlay" onClick={() => !submitting && setShowConfirm(false)}><div className="modal-box grading-choice" onClick={event => event.stopPropagation()}><h3>确认提交本次练习</h3>{hasSolutions && <><p>本试卷包含解答题，请选择批改方式：</p><label className={gradingMode === 'ai' ? 'selected' : ''}><input type="radio" checked={gradingMode === 'ai'} onChange={() => setGradingMode('ai')} /><span><b>AI 批改</b><small>提交后由 DeepSeek 按参考答案即时评分并给出评语</small></span></label><label className={gradingMode === 'teacher' ? 'selected' : ''}><input type="radio" checked={gradingMode === 'teacher'} onChange={() => setGradingMode('teacher')} /><span><b>教师批改</b><small>提交到教师端，等待教师评分并填写评语</small></span></label></>}<div className="modal-actions"><button className="secondary-btn" disabled={submitting} onClick={() => setShowConfirm(false)}>取消</button><button className="primary" disabled={submitting} onClick={doSubmit}>{submitting ? '正在提交…' : '确认提交'}</button></div></div></div>}
    </section>
  }
  return <><section className="analysis-title"><div><span className="eyebrow"><ClipboardList size={15} />课程练习</span><h1>练习中心</h1><p>解答题可选择 AI 即时批改，也可提交教师评分并获得评语。</p></div></section>
    {/* 顶部统计卡片 */}
    <div className="exam-stats">
      <div className="exam-stat">
        <span className="exam-stat-number">{items.length}</span>
        <span className="exam-stat-label">总习题</span>
      </div>
      <div className="exam-stat">
        <span className="exam-stat-number">{subs.length}</span>
        <span className="exam-stat-label">已完成</span>
      </div>
      <div className="exam-stat">
        <span className="exam-stat-number">
          {items.length > 0 ? Math.round((subs.length / items.length) * 100) : 0}%
        </span>
        <span className="exam-stat-label">完成率</span>
      </div>
      <div className="exam-stat">
        <span className="exam-stat-number">{items.length - subs.length}</span>
        <span className="exam-stat-label">待练习</span>
      </div>
    </div>
    <div className="exercise-grid">{items.length === 0 ? <div className="empty-state">
      <img src={EmptyQuestions} alt="暂无习题" className="empty-illustration" />
      <h3>还没有习题</h3>
      <p>教师发布习题后，这里就会显示啦</p>
    </div> : items.map(exam => { const done = submitted(exam.id); return <article className="panel exercise" key={exam.id}><div className="exercise-top"><i><ClipboardList /></i><em>{exam.difficulty}</em></div><h3>{exam.title}</h3><p>{exam.document_name} · {exam.chapter}</p><div><span>{exam.questions.length} 道题</span>{done && <span className={`done ${done.status === 'pending_teacher' ? 'pending' : ''}`}><CheckCircle2 />{done.status === 'pending_teacher' ? '待教师批改' : `已完成 ${done.accuracy}%`}</span>}</div><button onClick={() => open(exam)}>{done ? '查看结果' : '开始练习'}<ChevronRight /></button></article> })}</div></>
}
function TeacherGrading() {
  const [items, setItems] = useState([]);
  const [active, setActive] = useState(null);
  const [grades, setGrades] = useState({});
  const [overall, setOverall] = useState('');
  const [message, setMessage] = useState('');
  const [saving, setSaving] = useState(false);
  const load = () => request('/exams/submissions/all', { cache: false }).then(data => {
    setItems(data.items);
    setActive(current => data.items.find(item => item.id === current?.id) || data.items.find(item => item.status === 'pending_teacher') || data.items[0] || null);
  });
  useEffect(() => { load() }, []);
  useEffect(() => {
    if (!active) return;
    setGrades(Object.fromEntries(active.details.filter(detail => detail.type === 'solution').map(detail => [detail.id, { score: detail.score_awarded ?? '', comment: detail.teacher_comment || detail.feedback || '' }])));
    setOverall(active.overall_comment || '');
    setMessage('');
  }, [active?.id]);
  const update = (id, key, value) => setGrades(current => ({ ...current, [id]: { ...current[id], [key]: value } }));
  const submit = async () => {
    const pending = active.details.filter(detail => detail.type === 'solution' && detail.grading_status === 'pending');
    if (pending.some(detail => grades[detail.id]?.score === '')) { setMessage('请填写全部解答题分数。'); return }
    setSaving(true);
    setMessage('');
    try {
      const payload = { grades: Object.fromEntries(pending.map(detail => [detail.id, { score: Number(grades[detail.id].score), comment: grades[detail.id].comment || '' }])), overall_comment: overall };
      const graded = await post(`/exams/submissions/${active.id}/grade`, payload);
      setMessage('批改已完成，成绩和评语已同步到学生端。');
      setActive(graded);
      await load();
    } catch (error) { setMessage(error.message) } finally { setSaving(false) }
  };
  const pendingCount = items.filter(item => item.status === 'pending_teacher').length;

  // 获取知识点（兼容单值或数组）
  const getKnowledgePoints = (detail) => {
    if (detail.knowledge_points && Array.isArray(detail.knowledge_points)) {
      return detail.knowledge_points;
    }
    if (detail.knowledge_point) {
      return [detail.knowledge_point];
    }
    return [];
  };

  return <>
    <section className="analysis-title">
      <div>
        <span className="eyebrow"><CheckCircle2 size={15} />人工评分</span>
        <h1>试卷批改</h1>
        <p>查看学生提交的解答题，逐题评分并填写评语。</p>
      </div>
    </section>
    {/* 顶部横向标签 */}
    <div className="grading-tabs-wrapper">
      <div className="grading-tabs-head">
        <span className="grading-tabs-label">提交记录</span>
        <span className="grading-tabs-count">{pendingCount} 份待批改</span>
      </div>
      <div className="grading-tabs-list">
        {items.length === 0 ? (
          <span className="grading-tabs-empty">暂无学生提交</span>
        ) : (
          items.map(item => (
            <button
              key={item.id}
              className={`grading-tab ${active?.id === item.id ? 'active' : ''}`}
              onClick={() => setActive(item)}
            >
              <span className="grading-tab-name">{item.student}</span>
              <span className="grading-tab-meta">
                {item.exam_title}
                <em className={item.status}>{item.status === 'pending_teacher' ? '待批改' : '已完成'}</em>
              </span>
            </button>
          ))
        )}
      </div>
    </div>
    {/* 批改区 - 全宽 */}
    <section className="grading-paper-full">
      {!active ? (
        <div className="empty">请选择一份试卷</div>
      ) : (
        <>
          <div className="panel-head">
            <div>
              <h3>{active.exam_title}</h3>
              <p>{active.student} · 提交于 {active.submitted_at}</p>
            </div>
            <strong>{active.status === 'graded' ? `${active.score}/${active.total}` : '待评分'}</strong>
          </div>
          {active.details.map((detail, index) => {
            const isWrong = detail.correct === false;
            const knowledgePoints = getKnowledgePoints(detail);
            return (
              <article className="grading-question" key={detail.id}>
                <h4>
                  <span>{index + 1}</span>
                  <em>{questionTypeText(detail.type)}</em>
                  {detail.question}
                </h4>
                <div className={`student-answer ${isWrong ? 'wrong' : ''}`}>
                  <b>学生答案</b>
                  <p>{detail.student_answer || '（未作答）'}</p>
                  {isWrong && <span className="wrong-tag">✗ 错误</span>}
                </div>
                {detail.type === 'solution' ? (
                  <div className="teacher-grade">
                    <label>
                      得分（满分 {detail.score}）
                      <input
                        type="number"
                        min="0"
                        max={detail.score}
                        step="0.5"
                        disabled={active.status === 'graded'}
                        value={grades[detail.id]?.score ?? ''}
                        onChange={event => update(detail.id, 'score', event.target.value)}
                      />
                    </label>
                    <label>
                      教师评语
                      <textarea
                        disabled={active.status === 'graded'}
                        value={grades[detail.id]?.comment || ''}
                        onChange={event => update(detail.id, 'comment', event.target.value)}
                        placeholder="写出得分依据和改进建议"
                      />
                    </label>
                    <details>
                      <summary>查看参考答案</summary>
                      <p>{detail.answer}</p>
                    </details>
                    {/* 知识点标签 — 紧跟在参考答案下面 */}
                    {knowledgePoints.length > 0 && (
                      <div className="question-knowledge-footer" style={{ marginTop: '8px' }}>
                        {knowledgePoints.map(point => (
                          <span key={point} className="knowledge-tag-blue">{point}</span>
                        ))}
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="auto-grade">
                    <span>系统判分：{detail.score_awarded}/{detail.score}</span>
                    <p>标准答案：{detail.answer}</p>
                    {/* 知识点标签 — 紧跟在标准答案下面 */}
                    {knowledgePoints.length > 0 && (
                      <div className="question-knowledge-footer" style={{ marginTop: '6px' }}>
                        {knowledgePoints.map(point => (
                          <span key={point} className="knowledge-tag-blue">{point}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </article>
            );
          })}
          <label className="overall-comment">
            总评
            <textarea
              disabled={active.status === 'graded'}
              value={overall}
              onChange={event => setOverall(event.target.value)}
              placeholder="填写本次作答的整体评价与学习建议"
            />
          </label>
          {message && <div className="notice">{message}</div>}
          {active.status === 'pending_teacher' && (
            <button className="primary grade-submit" disabled={saving} onClick={submit}>
              {saving ? '正在保存…' : '完成批改并发送给学生'}
            </button>
          )}
        </>
      )}
    </section>
  </>
}
function Exams({user}){return user.role==='teacher'?<TeacherExams/>:<StudentExams user={user}/>}
function Wrongbook({ user }) {
  const [items, setItems] = useState([]);
  const [mastery, setMastery] = useState([]);
  const [filters, setFilters] = useState(() => {
    const params = new URLSearchParams(location.search);
    return params.getAll('knowledge');
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
    }).catch(() => { })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    loadData();
  }, [user.name]);

  // 监听 URL 变化（popstate 和 pushState 触发）
  useEffect(() => {
    const onPop = () => {
      const params = new URLSearchParams(location.search);
      setFilters(params.getAll('knowledge'));
    };

    window.addEventListener('popstate', onPop);

    return () => {
      window.removeEventListener('popstate', onPop);
    };
  }, []);

  // 点击标签：更新 URL 并设置 filter
  const handleTagClick = (topic) => {
    setFilters(previous => {
      // 点击“清除筛选”
      if (!topic) {
        history.pushState(null, '', '/student/wrongbook');
        return [];
      }

      // 已选择则取消，未选择则添加
      const next = previous.includes(topic)
        ? previous.filter(item => item !== topic)
        : [...previous, topic];

      // 把多个知识点写入 URL
      const params = new URLSearchParams();
      next.forEach(item => params.append('knowledge', item));

      const query = params.toString();
      const url = query
        ? `/student/wrongbook?${query}`
        : '/student/wrongbook';

      history.pushState(null, '', url);
      return next;
    });
  };

  // 过滤错题：未选择时显示全部，选择多个时显示任一知识点对应的错题
  const getQuestionKnowledgePoints = (question) => {
    if (Array.isArray(question.knowledge_points)) {
      return question.knowledge_points;
    }

    // 兼容旧错题
    if (question.knowledge_point) {
      return [question.knowledge_point];
    }

    return [];
  };

  const filteredItems = filters.length > 0
    ? items.filter(question => {
      const questionPoints = getQuestionKnowledgePoints(question);

      // 只要题目包含任意一个已选知识点，就显示
      return filters.some(filterPoint =>
        questionPoints.includes(filterPoint)
      );
    })
    : items;

  const knowledgePointTags = useMemo(() => {
    const topicMap = new Map();

    // 先加入掌握度中的知识点
    mastery.forEach(item => {
      topicMap.set(item.topic, {
        topic: item.topic,
        score: item.score,
      });
    });

    // 再加入错题中的全部知识点
    items.forEach(question => {
      getQuestionKnowledgePoints(question).forEach(point => {
        if (!topicMap.has(point)) {
          topicMap.set(point, {
            topic: point,
            score: null,
          });
        }
      });
    });

    return Array.from(topicMap.values());
  }, [mastery, items]);

  return (
    <>
      <section className="analysis-title">
        <div>
          <span className="eyebrow"><AlertCircle size={15} />查漏补缺</span>
          <h1>我的错题本</h1>
          <p>自动收集练习中的错题，结合解析进行针对性复习。</p>
        </div>
      </section>

      {/* 掌握度标签 */}
      {mastery.length > 0 && (
        <div className="mastery-tags" style={{ marginBottom: '20px', display: 'flex', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
          <span style={{ fontWeight: 'bold', marginRight: '10px' }}>知识点掌握度：</span>
          {knowledgePointTags.map(m => (
            <span
              key={m.topic}
              onClick={() => handleTagClick(m.topic)}
              style={{
                padding: '4px 14px',
                borderRadius: '20px',
                background: filters.includes(m.topic) ? '#5577ee' : '#eef1f7',
                color: filters.includes(m.topic) ? '#fff' : '#333',
                cursor: 'pointer',
                fontSize: '14px',
                transition: '0.2s',
                border: filters.includes(m.topic)
                  ? '1px solid #5577ee'
                  : '1px solid transparent',
              }}
            >
              {m.topic}{m.score !== null ? ` ${m.score}%` : ''}
            </span>
          ))}
          {filters.length > 0 && (
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
      {/* 筛选提示 */}


      <div className="wrong-list">
        {loading ? (
          <div className="panel empty">加载中...</div>
        ) : filteredItems.length === 0 ? (
          <div className="empty-state">
            <img src={EmptyCelebration} alt="暂无错题" className="empty-illustration" />
            <h3>{filters.length > 0 ? '该知识点暂无错题' : '暂无错题'}</h3>
            <p>{filters.length > 0 ? '换个知识点看看吧！' : '继续保持，再接再厉！'}</p>
          </div>
        ) : (
          filteredItems.map((q, i) => (
            <article className="panel wrong-item" key={q.exam_id + q.id}>
              <div className="wrong-meta">
                <span>{q.exam_title}</span>
              </div>
              <h3>{i + 1}. {q.question}</h3>
              <p className="your-answer">你的答案：{q.student_answer || '未作答'}</p>
              <p className="right-answer">正确答案：{q.answer}</p>
              <div className="explanation"><Sparkles /> {q.analysis}</div>
            </article>
          ))
        )}
      </div>
    </>
  );
}
function App(){const isLoginPage=location.pathname==='/login';const [user,setUser]=useState(()=>{if(isLoginPage)return null;try{return JSON.parse(localStorage.getItem('mainrag-user'))}catch{return null}});useEffect(()=>{if(!user&&location.pathname!='/login')history.replaceState({},'','/login')},[user]);return user&&!isLoginPage?<Shell user={user} onLogout={()=>{localStorage.removeItem('mainrag-user');history.replaceState({},'','/login');setUser(null)}}/>:<Login onLogin={setUser}/>}
createRoot(document.getElementById('root')).render(<App/>);