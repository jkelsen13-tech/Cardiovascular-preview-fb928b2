'use strict';
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm'),crypto=require('node:crypto'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../..'),read=p=>fs.readFileSync(path.join(root,p)),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const contexts=require('../../guided-study/contextual-contexts.js'),html=read('index.html').toString();
const sandbox={};sandbox.window=sandbox;vm.createContext(sandbox);
for(const match of html.matchAll(/src="(guided-study\/lessons[^\"]*\.js)"/g))vm.runInContext(read(match[1]).toString(),sandbox,{filename:match[1]});
const lessons=sandbox.GuidedStudyLessons,inventory=JSON.parse(read('guided-study/assets/course-audio-inventory.json'));
assert.equal(lessons.length,111);assert.equal(new Set(lessons.map(l=>l.id)).size,111);
const ids=new Set(lessons.map(l=>l.id)),mapped=new Set(Object.values(contexts.guide).flat());
assert.deepEqual([...mapped].sort(),[...ids].sort(),'Every original recording has a real study-path topic; no invented ID');
for(const [topic,items] of Object.entries(contexts.guide)){assert(items.length>0,topic);assert.equal(new Set(items).size,items.length,topic);}
for(const clip of inventory.clips){
 const lesson=lessons.find(l=>l.id===clip.id);
 assert.equal(sha(read('guided-study/assets/'+clip.audio_file)),clip.audio_sha256,'Original MP3: '+clip.id);
 assert.equal(sha(Buffer.from(lesson.transcript)),clip.text_sha256,'Exact original transcript: '+clip.id);
}
assert.deepEqual(read('index.html'),read('cmt-quiz.html'),'Both entry pages use the same contextual experience');
for(const old of ['session.js','player.js','boot.js','explanation.js'])assert(!html.includes('src="guided-study/'+old+'"'),'Old tour engine not loaded: '+old);
const player=read('guided-study/contextual-player.js').toString();
assert(!/scrollIntoView|scrollTo|\.focus\(|requestAnimationFrame|setInterval|localStorage|GuidedStudySession|\.guided\b/.test(player),'No view ownership, simulator adapters, persistent loop or storage migration');
for(const match of player.matchAll(/(?:host\.)?(HeartV3Study|CardiorespiratoryStudy|LeadPlacementLab|EcgStudy)\.(\w+)\(/g))assert(['getState','inspectBreathing'].includes(match[2]),'Only read-only model calls: '+match[0]);
for(const [method,input] of [['heart',{selected:'lv',route:null}],['lungs',{selected:'diaphragm',view:'whole'}],['lead',{selected:'v1',tab:'guided'}]]){
 const before=JSON.stringify(input),output=contexts[method](input);assert(output.length);assert.equal(JSON.stringify(input),before,'Context lookup is read-only');for(const id of output)assert(ids.has(id));
}
assert(contexts.heart({selected:'ra'}).includes('M02.02'));
assert(contexts.heart({selected:'lv'},'ejection').includes('M03.05'));
assert(contexts.heart({route:'routeA',stage:'routeA.leaflets',selected:'mitral'}).includes('M02.06'));
assert(!contexts.heart({route:'routeA',stage:'routeA.leaflets',selected:'mitral'}).includes('M04.06'));
for(const [stage,first]of [['routeB.tissue','M03.02'],['routeB.cell','M04.08'],['routeB.myofibril','M04.09'],['routeC.ventricular','M04.06'],['routeD.capillary','M02.09']])assert.equal(contexts.heart({route:stage.split('.')[0],stage,selected:'lv'})[0],first,stage);
for(const stage of ['smaller','bronchioles','terminal','respiratory','ducts','sacs'])assert(!contexts.lungs({selected:'diaphragm'},stage).includes('M05.06'),stage+' must follow the actual airway section');
assert(contexts.lungs({selected:'diaphragm'}).includes('M05.06'));
assert(contexts.lungs({selected:'rightlung'},'membrane').includes('M05.08'));
assert(contexts.lead({selected:'ics4'}).includes('M07.04'));
assert(contexts.ecg('qrs').includes('M08.03'));
console.log(JSON.stringify({passed:true,recordings:111,originalAudioHashes:111,exactOriginalTranscripts:111,studyPathTopics:Object.keys(contexts.guide).length,allRecordingsMapped:true,tourEngineNotLoaded:true,modelAPIReadOnly:true}));
