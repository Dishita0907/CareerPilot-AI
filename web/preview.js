// A browser-only preview for GitHub Pages. No credentials or network requests.
import data from '../data/jobs.json'
export const catalog=data
const vocab=[...new Set(data.jobs.flatMap(j=>j.skills))]
const norm=s=>s.toLowerCase().replaceAll('bangalore','bengaluru')
const tokenize=s=>norm(s).match(/[\p{L}\d+#.]+/gu)||[]
const ignored=new Set('a an for my me which find jobs fit i the and role roles in to best show of'.split(' '))
export function analyze(text){
  const words=' '+tokenize(text).join(' ')+' '
  return vocab.filter(s=>words.includes(' '+tokenize(s).join(' ')+' '))
}
export function shortlist(profile,question){
  const terms=[...new Set(tokenize(profile.goal+' '+question).filter(t=>!ignored.has(t)))]
  return data.jobs.map(j=>{
    const found=j.skills.filter(s=>profile.skills.includes(s))
    const title=tokenize(j.title+' '+j.skills.join(' '))
    const factors={}, weights={}
    function add(name,weight,value){factors[name]=Math.round(100*value);weights[name]=weight}
    if(terms.length)add('keywords',45,terms.filter(t=>title.includes(t)).length/terms.length)
    if(j.skills.length && profile.skills.length)add('skills',30,found.length/j.skills.length)
    if(profile.years!=null && j.years!=null)add('experience',15,j.years?Math.min(profile.years/j.years,1):1)
    if(profile.location.trim())add('location',10,Number(norm(j.location).includes(norm(profile.location.trim()))))
    const weight=Object.values(weights).reduce((a,b)=>a+b,0)
    const score=weight?Object.keys(weights).reduce((a,k)=>a+weights[k]*factors[k],0)/weight:0
    return {...j,score:Math.round(score),factors,missing:j.skills.filter(s=>!found.includes(s))}
  }).sort((a,b)=>b.score-a.score||a.id.localeCompare(b.id)).slice(0,5)
}
