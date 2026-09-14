import React,{useEffect,useState}from'react';

export default function Pyq({api,exam,back}){
  const[year,setYear]=useState(2026);
  const[subject,setSubject]=useState('');
  const[data,setData]=useState(null);
  const[loading,setLoading]=useState(false);
  const[error,setError]=useState('');

  async function load(){
    setLoading(true);setError('');
    try{
      const q=new URLSearchParams({exam,year:String(year)});
      if(subject.trim())q.set('subject',subject.trim());
      setData(await api('/pyq?'+q));
    }catch{setError('Official PYQ load नहीं हुआ।')}
    finally{setLoading(false)}
  }
  useEffect(()=>{load()},[exam]);

  return <>
    <button className="back" onClick={back}>← {exam==='prelims'?'PRELIMS':'MAINS'} PYQ</button>
    <div className="panel">
      <h2>Official UPSC Previous Papers</h2>
      <input type="number" min="2011" max="2100" value={year} onChange={e=>setYear(Number(e.target.value)||2026)}/>
      <input placeholder="Subject filter जैसे Anthropology / General Studies" value={subject} onChange={e=>setSubject(e.target.value)}/>
      <button className="primary" onClick={load}>PYQ देखें</button>
      {loading&&<p>लोड हो रहा है…</p>}
      {error&&<p>{error}</p>}
    </div>
    <div className="pyqList">
      {data?.papers?.map((p,i)=><a className="pyqCard" key={p.url||i} href={p.url} target="_blank" rel="noreferrer"><span><small>UPSC • {year}</small><b>{p.title}</b></span><span>↗</span></a>)}
      {!loading&&data&&data.papers?.length===0&&<div className="empty">इस filter के लिए direct paper नहीं मिला। Official previous-papers source देखें।</div>}
    </div>
    {data?.source_page&&<a className="sourceLink" href={data.source_page} target="_blank" rel="noreferrer">UPSC official source page</a>}
  </>
}
