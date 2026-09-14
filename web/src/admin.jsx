import React,{useEffect,useState}from'react';
import{createRoot}from'react-dom/client';
import'./style.css';

const API=import.meta.env.VITE_API_BASE_URL||'http://localhost:8000';
async function api(path,opts={}){const token=localStorage.getItem('token');const headers={...(opts.headers||{}),...(token?{Authorization:`Bearer ${token}`}:{})};const r=await fetch(API+path,{...opts,headers});if(!r.ok)throw new Error(await r.text());return r.json()}

function Admin(){
 const[checking,setChecking]=useState(true);const[allowed,setAllowed]=useState(false);const[days,setDays]=useState(7);const[busy,setBusy]=useState(false);const[result,setResult]=useState(null);const[error,setError]=useState('');
 useEffect(()=>{api('/admin/status').then(x=>setAllowed(!!x.is_admin)).catch(()=>setAllowed(false)).finally(()=>setChecking(false))},[]);
 async function update(){setBusy(true);setError('');setResult(null);try{setResult(await api('/admin/current-affairs/update-now?backfill_days='+days,{method:'POST'}))}catch(e){setError('Update नहीं हुआ। Admin access/backend configuration जाँचें।')}finally{setBusy(false)}}
 if(checking)return <div className="center"><div className="panel"><p>Admin access जाँचा जा रहा है…</p></div></div>;
 if(!localStorage.getItem('token'))return <div className="center"><div className="panel"><h2>Login required</h2><p>पहले मुख्य Website में login करें।</p><a className="sourceLink" href="/">Login खोलें</a></div></div>;
 if(!allowed)return <div className="center"><div className="panel"><h2>Admin access नहीं है</h2><p>यह page केवल configured admin account के लिए है।</p><a className="sourceLink" href="/">Website पर वापस जाएँ</a></div></div>;
 return <div className="center"><div className="panel adminPanel"><a className="sourceLink" href="/">← Website</a><h2>Current Affairs Update</h2><p>PIB और configured official sources से नए UPSC-relevant items fetch करें। पिछली छूटी तारीखों के लिए backfill भी चलेगा।</p><label>Backfill days</label><input type="number" min="1" max="30" value={days} onChange={e=>setDays(Math.max(1,Math.min(30,Number(e.target.value)||7)))}/><button className="primary" disabled={busy} onClick={update}>{busy?'Update हो रहा है…':'आज का Update चलाएँ'}</button>{error&&<p>{error}</p>}{result&&<div className="studyBox"><b>Update पूरा</b><span>Backfill: {result.backfill_days} दिन</span><span>Core added: {result.core?.total_added??0}</span><span>PIB added: {result.core?.pib_added??0}</span><span>Core government added: {result.core?.government_added??0}</span><small>Official-source result: {JSON.stringify(result.official_sources)}</small></div>}</div></div>
}

createRoot(document.getElementById('root')).render(<Admin/>);
