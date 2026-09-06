import {readFile,writeFile,mkdir,cp,rm} from 'node:fs/promises';
const corpus=JSON.parse(await readFile('data/corpus.json','utf8'));
if(!corpus.articles.length||new Set(corpus.articles.map(a=>a.id)).size!==corpus.articles.length)throw Error('Invalid corpus');
await rm('dist',{recursive:true,force:true});await mkdir('dist');await cp('web','dist',{recursive:true});for(const dir of ['data','reports'])await cp(dir,'dist/'+dir,{recursive:true});await cp('lean/IncomeTax','dist/lean',{recursive:true});
console.log(`Built ${corpus.articles.length} source articles. Semantic review is separate.`);
