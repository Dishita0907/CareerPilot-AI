import React,{useEffect,useState} from 'react'
import {createRoot} from 'react-dom/client'
import {catalog,analyze,shortlist} from './preview'
import './style.css'

const demo=import.meta.env.VITE_PREVIEW==='1'
const empty={goal:'',location:'',years:null,skills:[]}
const prefix='careerpilot.v1.'
async function api(path,method='GET',body){
  const upload=body instanceof FormData
  const headers={Authorization:'Bearer '+(localStorage.getItem(prefix+'token')||'')}
  if(body&&!upload)headers['Content-Type']='application/json'
  const res=await fetch('/api/'+path,{method,headers,body:upload?body:JSON.stringify(body)})
  if(!res.ok){const err=await res.json().catch(()=>({}));throw new Error(typeof err.detail==='string'?err.detail:'Could not complete the request')}
  return res.json()
}
function App(){
  const [p,setP]=useState(empty),[resume,setResume]=useState(''),[q,setQ]=useState(''),[jobs,setJobs]=useState([]),[history,setHistory]=useState([]),[busy,setBusy]=useState(true),[err,setErr]=useState(''),[mode,setMode]=useState(demo?'Browser preview':'Career workspace'),[ready,setReady]=useState(demo)
  useEffect(()=>{async function init(){
    if(demo){const saved=JSON.parse(localStorage.getItem(prefix+'demo')||'null');if(saved){setP(saved.profile);setHistory(saved.history);setJobs(saved.jobs||[])}}
    else{
      const s=await api('status');setMode(s.mode)
      if(!localStorage.getItem(prefix+'token')){const session=await api('session','POST');localStorage.setItem(prefix+'token',session.token)}
      const w=await api('workspace');setP(w.profile);setHistory(w.history)
    }
    setReady(true)
  }init().catch(e=>setErr(e.message)).finally(()=>setBusy(false))},[])
  function edit(k,v){setP({...p,[k]:v})}
  async function submit(e){e.preventDefault();setErr('');setBusy(true)
    try{
      const question=q.trim()||'Which jobs fit my career goal?'
      const profile=demo?{...p,skills:resume.trim()?analyze(resume):p.skills}:await api('profile','PUT',{...p,resume:resume.trim()||null})
      let result
      if(demo){
        const list=shortlist(profile,question),first=list[0]
        result={jobs:list,answer:'Your closest keyword match is '+first.title+' ('+first.id+'). '+(first.missing.length?'Compare your experience with these listed skills: '+first.missing.slice(0,3).join(', ')+'.':'Read the employer listing for the full requirements.')}
      }else result=await api('ask','POST',{text:question})
      const turns=[...history,{role:'user',text:question},{role:'assistant',text:result.answer}].slice(-40)
      if(demo)localStorage.setItem(prefix+'demo',JSON.stringify({profile,history:turns,jobs:result.jobs}))
      setP(profile);setJobs(result.jobs);setHistory(turns);setResume('');setQ('')
    }catch(e){setErr(e.message)}finally{setBusy(false)}
  }
  async function upload(e){if(!e.target.files.length)return;setBusy(true);setErr('')
    try{const f=new FormData();f.set('file',e.target.files[0]);setResume((await api('resume','POST',f)).text)}catch(e){setErr(e.message)}finally{setBusy(false)}
  }
  return <><header><b>↗ &nbsp; CareerPilot <em>AI</em></b><span>{mode}</span></header><main><section className="intro"><div><small>CAREER WORKSPACE</small><h1>Find your next role.</h1><p>Explore real openings through your skills, goals, and location.</p></div><aside><strong>{catalog.jobs.length}</strong> Stripe postings<br/><small>Snapshot · {catalog.retrieved}</small></aside></section>
  <div className="layout"><form onSubmit={submit}><h2>Your profile</h2><label>Career goal<input required maxLength="300" value={p.goal} onChange={e=>edit('goal',e.target.value)} placeholder="e.g. Machine learning engineer"/></label>
  <div className="pair"><label>Location<input value={p.location} maxLength="120" onChange={e=>edit('location',e.target.value)} placeholder="e.g. Bengaluru"/></label><label>Years of experience<input type="number" min="0" max="80" step=".1" value={p.years??''} onChange={e=>edit('years',e.target.value===''?null:+e.target.value)}/></label></div>
  <label>Résumé text<textarea maxLength="80000" rows="4" placeholder="Paste your skills and experience" value={resume} onChange={e=>setResume(e.target.value)}/></label>
  {!demo&&<label>Or import a PDF (2 MB)<input type="file" accept="application/pdf" onChange={upload} disabled={busy}/></label>}
  {!!p.skills.length&&<p className="muted">Saved skills · {p.skills.join(', ')}</p>}
  <label>{demo?'Search terms':'Ask your advisor'}<input value={q} maxLength="1500" onChange={e=>setQ(e.target.value)} placeholder={demo?'e.g. Backend, payments':'Which skills should I develop?'}/></label>
  <button disabled={busy||!ready}>{busy?'Working…':'Find matches ↗'}</button>{err&&<p role="alert">{err}</p>}
  <p className="note">{demo?'This preview uses keyword matching and saves your profile in this browser. The full app adds FAISS retrieval, PDF import, and PostgreSQL memory.':'Only extracted skills are saved from your résumé. In OpenAI mode, the advisor receives your profile, recent conversation, and retrieved jobs.'}</p></form>
  <section className="results" aria-live="polite"><h2>Your shortlist</h2>{!jobs.length&&<div className="empty"><strong>Your matches will appear here.</strong><p>Add a career goal to explore the employer listings.</p></div>}
  {jobs.map(j=><article key={j.id}><div className="row"><small>{j.company} · {j.location}</small><b>{j.score}% fit</b></div><h3><a href={j.url} target="_blank" rel="noreferrer">{j.title} ↗</a></h3><p>{j.years!=null?j.years+' years mentioned':'Experience unspecified'} · ID {j.id}</p><details><summary>Match details</summary><p>{Object.entries(j.factors).map(([k,v])=>k+' '+v+'%').join(' · ')}</p><p>Skills to review · {j.missing.join(', ')||'None identified'}</p></details></article>)}
  {!!history.length&&<section className="conversation"><h2>{demo?'Search history':'Conversation'}</h2>{history.map((m,i)=><p key={i}><b>{m.role==='user'?'You':'CareerPilot'}</b>{m.text}</p>)}</section>}</section></div></main></>
}
createRoot(document.getElementById('root')).render(<App/>)
