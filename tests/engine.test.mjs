import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {scorePair,matchPeople,exportMatches} from '../site/engine.js';
import {demoPeople,parseCSV,importCSV} from '../site/data.js';
const p=(id,overrides={})=>({id,name:id,cleanliness:.5,sleep_time:.5,social:.5,snore_freq:0,snore_sensitivity:0,hobbies:[],...overrides});
test('snoring conflict is symmetric and increases when snoring meets sensitivity',()=>{
  const a=p('a',{snore_freq:1}),b=p('b',{snore_sensitivity:1});
  assert.equal(scorePair(a,b).conflict,.5);
  assert.deepEqual(scorePair(a,b),scorePair(b,a));
  assert.equal(scorePair(p('a'),p('b',{snore_sensitivity:1})).conflict,0);
});
test('empty interests redistribute weights rather than treating missing evidence as disagreement',()=>assert.equal(scorePair(p('a'),p('b')).compatibility,1));
test('shared hobbies use intersection over union',()=>assert.equal(scorePair(p('a',{hobbies:['Music','Gaming']}),p('b',{hobbies:['Music','Art']})).hobbies,1/3));
test('empty, singleton and fully excluded cohorts keep all unmatched people',()=>{
  assert.equal(matchPeople([]).pairs.length,0);
  assert.equal(matchPeople([p('a')]).unmatched.length,1);
  const r=matchPeople([p('a',{snore_freq:1,snore_sensitivity:1}),p('b',{snore_freq:1,snore_sensitivity:1})],{threshold:0});
  assert.equal(r.unmatched.length,2);assert.equal(r.pruned,1);
});
test('matching is deterministic and no person appears twice',()=>{
  const r=matchPeople(demoPeople());assert.deepEqual(r,matchPeople(demoPeople()));
  const ids=[...r.pairs.flatMap(x=>[x.a.id,x.b.id]),...r.unmatched.map(x=>x.id)];
  assert.equal(new Set(ids).size,16);assert.equal(ids.length,16);
});
test('refinement explores both alternatives and improves a known greedy trap',()=>{
  // Search a fixed deterministic corpus for a case requiring an improving swap.
  let seed=13;const rnd=()=>((seed=(seed*1664525+1013904223)>>>0)/2**32);
  let found=false;
  for(let trial=0;trial<100;trial++){
    const cohort=Array.from({length:8},(_,i)=>p(String(i),{cleanliness:rnd(),sleep_time:rnd(),social:rnd()}));
    const greedy=matchPeople(cohort,{passes:0}),refined=matchPeople(cohort);
    assert.ok(refined.total>=greedy.total-1e-10);
    if(refined.total>greedy.total+1e-6)found=true;
  }
  assert.ok(found,'The corpus must exercise improving swaps.');
});
test('constraints, score monotonicity and unique assignment hold across 120 generated cohorts',()=>{
  let seed=21;const rnd=()=>((seed=(seed*1664525+1013904223)>>>0)/2**32);
  for(let trial=0;trial<120;trial++){
    const cohort=Array.from({length:trial%31},(_,i)=>p(String(i),{cleanliness:rnd(),sleep_time:rnd(),social:rnd(),snore_freq:rnd(),snore_sensitivity:rnd(),hobbies:rnd()>.5?['Music']:['Gaming']}));
    const options={lambda:rnd()*2,threshold:rnd()},r=matchPeople(cohort,options);
    assert.ok(r.total>=r.initialTotal-1e-9);assert.ok(r.passes<=10);
    const ids=[...r.pairs.flatMap(x=>[x.a.id,x.b.id]),...r.unmatched.map(x=>x.id)];
    assert.equal(ids.length,cohort.length);assert.equal(new Set(ids).size,cohort.length);
    for(const pair of r.pairs){assert.ok(pair.conflict<=options.threshold);assert.ok(pair.score>0);}
  }
});
test('invalid inputs and unsafe settings fail explicitly',()=>{
  assert.throws(()=>matchPeople([p('a'),p('a')]));assert.throws(()=>matchPeople([p('a',{cleanliness:NaN})]));
  assert.throws(()=>matchPeople([],{passes:100}));assert.throws(()=>matchPeople([],{lambda:-1}));
});
test('CSV parser supports BOM, CRLF, quoted commas, newlines, and escaped quotes',()=>{
  assert.deepEqual(parseCSV('\uFEFFname,hobbies\r\n"A, B","Music, \"\"Art\"\""\r\n"C\nD",Reading'),[{name:'A, B',hobbies:'Music, "Art"'},{name:'C\nD',hobbies:'Reading'}]);
  assert.throws(()=>parseCSV('name,x\n"A,1'));assert.throws(()=>parseCSV('name,name\na,b'));assert.throws(()=>parseCSV('name,x\na,1,2'));
});
test('template imports, strips unused fields, anonymizes, and uses the explicit scale',()=>{
  const csv=readFileSync(new URL('../site/template.csv',import.meta.url),'utf8');
  const data=importCSV(csv);assert.equal(data.people.length,4);assert.equal(data.people[0].name,'Student 001');assert.equal(data.people[0].cleanliness,.8);
  assert.throws(()=>importCSV(csv,'one'));assert.equal(matchPeople(data.people).pairs.length,2);
});
test('raw survey headers and processed normalized columns are supported',()=>{
  const raw='Full Name,Cleaniliness,Sleep Time, How would you describe your social personality?, How often do you snore?,How sensitive are you to snoring?,Email\nPrivate Name,8,7,5,2,4,private@example.test';
  const result=importCSV(raw);assert.equal(result.people[0].social,.5);assert.equal(result.people[0].name,'Student 001');assert.ok(!JSON.stringify(result).includes('private@example.test'));
  const normalized='name,cleanliness_norm,sleep_time_norm,social_norm,snore_freq_norm,snore_sensitivity_norm,hobby_music\nAlias,0.8,0.7,0.5,0.2,0.4,1';
  assert.deepEqual(importCSV(normalized,'one',false).people[0].hobbies,['Music']);
});
test('missing and out of range values are rejected; repeated names remain distinct and flagged',()=>{
  const header='name,cleanliness,sleep_time,social,snore_freq,snore_sensitivity\n';
  assert.throws(()=>importCSV(header+'A,,5,5,0,5'));assert.throws(()=>importCSV(header+'A,11,5,5,0,5'));
  const duplicate=importCSV(header+'A,5,5,5,0,5\na,5,5,5,0,5');
  assert.equal(duplicate.people.length,2);assert.notEqual(duplicate.people[0].id,duplicate.people[1].id);assert.ok(duplicate.warnings.some(w=>w.startsWith('Repeated names')));
});
test('export includes unmatched people and neutralizes spreadsheet formula cells',()=>{
  const r=matchPeople([p('a',{name:'=HYPERLINK("bad")'})]);const csv=exportMatches(r);
  assert.match(csv,/unmatched/);assert.match(csv,/'=HYPERLINK/);
});
