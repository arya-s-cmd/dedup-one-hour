import React, { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_BASE || "http://localhost:8000";
const fmt = (s)=> s || <em>—</em>;

export default function App(){
  const [groups,setGroups] = useState([]);
  const [loading,setLoading] = useState(false);
  const [msg,setMsg] = useState("");

async function runDedupe(){
  setLoading(true);
  try {
    const res = await fetch(`${API}/dedupe/run`, { method: "POST" });
    if (!res.ok) throw new Error(`API ${res.status}`);
    await loadGroups();
    setMsg("Dedup complete");
  } catch (e) {
    console.error(e);
    setMsg("Error: " + (e?.message || "network"));
  } finally {
    setLoading(false);
  }
}
  async function loadGroups(){
    const res = await fetch(`${API}/groups?status=suggested`);
    setGroups(await res.json());
  }
  async function decide(groupId, decision, target=null){
    const body = { decision, actor:"reviewer@i4c", target_canonical_id: target };
    const res = await fetch(`${API}/groups/${groupId}/decision`, {method:"POST", headers:{"Content-Type":"application/json"}, body: JSON.stringify(body)});
    if(res.ok){ setMsg("Saved"); loadGroups(); } else { setMsg("Error"); }
  }

  useEffect(()=>{ loadGroups(); },[]);
  return (
    <div style={{fontFamily:"Inter, system-ui", margin:"24px"}}>
      <h1>Duplicate Review</h1>
      <p>
        <button onClick={runDedupe} disabled={loading}>{loading?"Running…":"Run Deduplication"}</button>
        <button style={{marginLeft:12}} onClick={async()=>{
          const r = await fetch(`${API}/audit/export`); const j=await r.json();
          const blob = new Blob([JSON.stringify(j)], {type:"application/json"});
          const url = URL.createObjectURL(blob); const a=document.createElement("a"); a.href=url; a.download="audit_export.json"; a.click(); URL.revokeObjectURL(url);
        }}>Export Audit</button>
        <span style={{marginLeft:12, color:"#0a0"}}>{msg}</span>
      </p>
      <Groups groups={groups} onDecide={decide}/>
    </div>
  );
}

function Groups({groups,onDecide}){
  if(!groups.length) return <p>No suggested groups. Click “Run Deduplication”.</p>;
  return groups.map(g=>(
    <div key={g.id} style={{border:"1px solid #ccc", padding:12, borderRadius:10, marginBottom:16}}>
      <div style={{display:"flex", justifyContent:"space-between"}}>
        <strong>Group #{g.id}</strong>
        <small>{g.score_summary}</small>
      </div>
      <table width="100%" cellPadding="4" style={{marginTop:8}}>
        <thead><tr><th>ID</th><th>Name</th><th>Phone</th><th>Email</th><th>Timestamp</th><th>Text</th></tr></thead>
        <tbody>
        {g.members.map(m=>(
          <tr key={m.id}>
            <td>{m.id}</td><td>{fmt(m.name)}</td><td>{fmt(m.phone)}</td><td>{fmt(m.email)}</td><td>{fmt(m.timestamp)}</td><td>{(m.text||"").slice(0,80)}</td>
          </tr>
        ))}
        </tbody>
      </table>
      <div style={{marginTop:8}}>
        <button onClick={()=>onDecide(g.id,"approve")}>Approve as Duplicates</button>
        <button style={{marginLeft:8}} onClick={()=>onDecide(g.id,"keep_separate")}>Keep Separate</button>
        <button style={{marginLeft:8}} onClick={()=> {
          const id = prompt("Canonical complaint ID to merge into?");
          if(id) onDecide(g.id, "merge_into", parseInt(id,10));
        }}>Merge into Case…</button>
        <span style={{marginLeft:12, color:"#555"}}>Evidence: same_phone={String(g.top_evidence?.same_phone)} same_email={String(g.top_evidence?.same_email)}</span>
      </div>
    </div>
  ));
}
