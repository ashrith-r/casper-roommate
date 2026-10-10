export const DEFAULTS = Object.freeze({lambda: .5, threshold: .55, passes: 10});
export const FEATURES = ['cleanliness', 'sleep_time', 'social', 'snore_freq', 'snore_sensitivity'];

export function validatePeople(people) {
  if (!Array.isArray(people) || people.length > 200) throw new Error('Use a cohort of at most 200 students.');
  const ids = new Set();
  for (const p of people) {
    if (!p.id || ids.has(p.id)) throw new Error('Each student needs a unique ID.');
    ids.add(p.id);
    if (typeof p.name !== 'string' || !p.name.trim() || p.name.length > 100) throw new Error('Names must contain 1–100 characters.');
    for (const key of FEATURES) if (!Number.isFinite(p[key]) || p[key] < 0 || p[key] > 1) throw new Error(`${p.name}: ${key} must be between 0 and 1.`);
    if (!Array.isArray(p.hobbies) || p.hobbies.some(h => typeof h !== 'string')) throw new Error('Hobbies must be a list of labels.');
  }
}

export function scorePair(a, b, lambda = .5) {
  const similarity = {
    cleanliness: 1 - Math.abs(a.cleanliness - b.cleanliness),
    sleep_time: 1 - Math.abs(a.sleep_time - b.sleep_time),
    social: 1 - Math.abs(a.social - b.social)
  };
  const ah = new Set(a.hobbies), bh = new Set(b.hobbies);
  const shared = [...ah].filter(h => bh.has(h));
  const union = new Set([...ah, ...bh]).size;
  // Missing interests carry no evidence; redistribute their weight to lifestyle.
  const hobbies = union ? shared.length / union : null;
  const lifestyle = .3 * similarity.cleanliness + .3 * similarity.sleep_time + .2 * similarity.social;
  const compatibility = hobbies === null ? lifestyle / .8 : lifestyle + .2 * hobbies;
  // High snoring AND high sensitivity create risk. Difference is not conflict.
  const conflict = (a.snore_freq * b.snore_sensitivity + b.snore_freq * a.snore_sensitivity) / 2;
  const penalty = lambda * conflict ** 2;
  return {score: compatibility - penalty, compatibility, conflict, penalty, similarity, hobbies, shared};
}

export function matchPeople(people, options = {}) {
  validatePeople(people);
  const config = {...DEFAULTS, ...options};
  if (!Number.isFinite(config.lambda) || config.lambda < 0 || config.lambda > 2 || !Number.isFinite(config.threshold) || config.threshold < 0 || config.threshold > 1 || !Number.isInteger(config.passes) || config.passes < 0 || config.passes > 10) throw new Error('Invalid matching settings.');
  const n = people.length, edges = [], matrix = Array.from({length:n}, () => Array(n).fill(null));
  let pruned = 0;
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
    const metrics = scorePair(people[i], people[j], config.lambda);
    if (metrics.conflict > config.threshold || metrics.score <= 0) { pruned++; continue; }
    const e = {a:i, b:j, ...metrics};
    edges.push(e); matrix[i][j] = matrix[j][i] = e;
  }
  edges.sort((a,b) => b.score - a.score || a.a - b.a || a.b - b.b);
  const used = new Set(), pairs = [];
  for (const e of edges) if (!used.has(e.a) && !used.has(e.b)) {
    pairs.push([e.a,e.b]); used.add(e.a); used.add(e.b);
  }
  const initialTotal = pairs.reduce((s,[a,b]) => s + matrix[a][b].score, 0);
  let swaps = 0, passes = 0, converged = config.passes === 0 ? false : true;
  // Fixed pass budget gives O(P n²) refinement. Every replacement uses valid edges.
  for (let pass = 0; pass < config.passes; pass++) {
    let improved = false; passes++;
    for (let i = 0; i < pairs.length; i++) for (let j = i + 1; j < pairs.length; j++) {
      const [a,b] = pairs[i], [c,d] = pairs[j];
      let best = null, bestScore = matrix[a][b].score + matrix[c][d].score;
      for (const option of [[[a,c],[b,d]], [[a,d],[b,c]]]) {
        const x = matrix[option[0][0]][option[0][1]], y = matrix[option[1][0]][option[1][1]];
        if (x && y && x.score + y.score > bestScore + 1e-10) { best = option; bestScore = x.score + y.score; }
      }
      if (best) { [pairs[i],pairs[j]] = best; swaps++; improved = true; }
    }
    if (!improved) break;
    if (pass === config.passes - 1) converged = false;
  }
  const result = pairs.map(([a,b]) => ({a:people[a], b:people[b], ...scorePair(people[a],people[b],config.lambda)})).sort((a,b) => b.score-a.score);
  return {pairs:result, unmatched:people.filter((_,i) => !used.has(i)), total:result.reduce((s,p) => s+p.score,0), initialTotal, swaps, passes, converged, candidates:edges.length, pruned, possible:n*(n-1)/2, config};
}

export function csvCell(value) {
  let text = String(value ?? '');
  if (/^[\s]*[=+@-]/.test(text)) text = `'${text}`;
  return `"${text.replaceAll('"','""')}"`;
}

export function exportMatches(result) {
  const rows = [['status','student_1','student_2','match_score','compatibility','conflict','penalty']];
  for (const p of result.pairs) rows.push(['matched',p.a.name,p.b.name,p.score.toFixed(4),p.compatibility.toFixed(4),p.conflict.toFixed(4),p.penalty.toFixed(4)]);
  for (const p of result.unmatched) rows.push(['unmatched',p.name,'','','','','']);
  return rows.map(r => r.map(csvCell).join(',')).join('\r\n');
}
