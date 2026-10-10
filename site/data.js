import {FEATURES, validatePeople} from './engine.js';

const samples = [
  ['Aarav',9,8,4,2,3,['Coding','Music']], ['Vihaan',8,9,4,1,5,['Coding','Music']],
  ['Isha',7,3,8,1,3,['Sports','Social']], ['Meera',8,3,9,2,4,['Sports','Social']],
  ['Kabir',6,9,6,5,2,['Gaming','Music']], ['Dev',6,8,5,3,2,['Gaming','Music']],
  ['Tara',9,2,3,1,8,['Reading','Art']], ['Anaya',8,2,2,1,9,['Reading','Art']],
  ['Rohan',5,7,9,7,2,['Sports','Gaming']], ['Aditya',6,7,8,6,1,['Sports','Gaming']],
  ['Nila',8,5,5,2,6,['Music','Reading']], ['Sana',9,6,5,3,5,['Music','Art']],
  ['Arjun',7,4,7,5,5,['Coding','Sports']], ['Kiran',7,5,6,4,4,['Coding','Reading']],
  ['Reva',6,9,4,2,7,['Art','Gaming']], ['Neel',7,8,3,1,8,['Gaming','Reading']]
];
export function demoPeople() { return samples.map(([name,...values],i) => ({id:`demo-${i+1}`,name,...Object.fromEntries(FEATURES.map((k,j)=>[k,values[j]/10])),hobbies:values[5]})); }

export function parseCSV(text) {
  if (text.length > 2_000_000) throw new Error('Choose a CSV smaller than 2 MB.');
  text = text.replace(/^\uFEFF/,'');
  const rows = []; let row = [], field = '', quoted = false, closed = false;
  const push = () => { row.push(field); field=''; closed=false; };
  for (let i=0;i<text.length;i++) {
    const c=text[i];
    if (quoted) {
      if(c==='"' && text[i+1]==='"') {field+='"';i++;}
      else if(c==='"') {quoted=false;closed=true;} else field+=c;
    } else if (c==='"') {
      if (field || closed) throw new Error('Invalid quote in CSV. Export the file as comma-separated CSV.');
      quoted=true;
    } else if(c===',') push();
    else if(c==='\n'||c==='\r') {
      if(c==='\r'&&text[i+1]==='\n')i++;
      push(); if(row.some(x=>x.trim()))rows.push(row); row=[];
    } else if(closed) {if(c!==' '&&c!=='\t')throw new Error('Unexpected text after a quoted CSV value.');}
    else field+=c;
  }
  if(quoted)throw new Error('A quoted CSV value was not closed.');
  push(); if(row.some(x=>x.trim()))rows.push(row);
  if(rows.length<2)throw new Error('Include a header and at least one student.');
  const headers=rows.shift().map(s=>s.trim().toLowerCase());
  if(new Set(headers).size!==headers.length)throw new Error('CSV column headers must be unique.');
  return rows.map((r,i)=>{
    if(r.length!==headers.length)throw new Error(`CSV row ${i+2} has ${r.length} values; expected ${headers.length}.`);
    return Object.fromEntries(headers.map((h,j)=>[h,r[j].trim()]));
  });
}

const aliases = {
  name:['name','full name'], cleanliness:['cleanliness','cleaniliness'],
  sleep_time:['sleep_time','sleep time'], social:['social','how would you describe your social personality?'],
  snore_freq:['snore_freq','snore','how often do you snore?'], snore_sensitivity:['snore_sensitivity','how sensitive are you to snoring?']
};
export function importCSV(text, scale='ten', anonymous=true) {
  if(!['ten','one'].includes(scale))throw new Error('Choose the input scale.');
  const rows=parseCSV(text), warnings=[];
  if(rows.length>200)throw new Error('This browser demo supports up to 200 students. Split larger files into cohorts.');
  const usedNames=new Set();
  const people=rows.map((r,i)=>{
    const pick=key=>{
      const keys=scale==='one'&&key!=='name'?[`${key}_norm`,...aliases[key]]:aliases[key];
      return keys.find(k=>Object.hasOwn(r,k));
    };
    const rawName=r[pick('name')];
    if(!rawName)throw new Error(`Row ${i+2}: missing name or Full Name.`);
    const repeated=usedNames.has(rawName.toLowerCase());
    if(repeated && !warnings.some(w=>w.startsWith('Repeated names')))warnings.push('Repeated names found. All rows are preserved with unique IDs; review for duplicate submissions before using results.');
    usedNames.add(rawName.toLowerCase());
    const p={id:`csv-${i+1}`,name:anonymous?`Student ${String(i+1).padStart(3,'0')}`:repeated?`${rawName} (row ${i+2})`:rawName};
    for(const key of FEATURES){
      const value=r[pick(key)], number=Number(value), max=scale==='ten'?10:1;
      if(value===undefined||value===''||!Number.isFinite(number)||number<0||number>max)throw new Error(`Row ${i+2}: ${key} needs a number from 0 to ${max}. Check the selected scale; no missing values are guessed.`);
      p[key]=number/max;
    }
    const hobbyText=r.hobbies??r.hobbies_raw??r['🎯 what do you do in your spare time?']??'';
    p.hobbies=[...new Set(hobbyText.split(/[,;|]/).map(h=>h.trim().toLowerCase()).filter(Boolean).map(h=>h==='coding / tech'?'Coding':h==='music / arts'?'Music':h==='sports / fitness'?'Sports':h==='studies / academic focus'?'Studies':h==='social / hanging out'?'Social':h[0].toUpperCase()+h.slice(1)))];
    if(!p.hobbies.length && scale==='one')for(const h of ['coding','music','sports','gaming','studies','social'])if(r[`hobby_${h}`]==='1')p.hobbies.push(h[0].toUpperCase()+h.slice(1));
    return p;
  });
  if(people.some(p=>!p.hobbies.length))warnings.push('Some students have no hobbies listed. Empty hobby sets use lifestyle scores only when both students have no hobbies.');
  if(anonymous)warnings.push('Names replaced with row-based student labels. Emails and other unused fields are discarded.');
  validatePeople(people);
  return {people,warnings};
}
