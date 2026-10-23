"""Final narrow-screen text bounds and independent audio regression."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os,json,traceback,hashlib,datetime
OUT=Path(os.environ.get('COURSE_CONTROLS_OUT','/tmp/course-narrow'));OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('CARDIO_BASE_URL','http://127.0.0.1:8890/')
result={'url':URL,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[],'errors':[],'http_errors':[],'screenshots':[],'metrics':[]}
def check(value,name):
 result['checks'].append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
def reveal(selector):page.locator(selector).evaluate("e=>{for(let p=e.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}")
def shot(name,selector):
 page.locator(selector).scroll_into_view_if_needed();page.evaluate('()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))');page.wait_for_timeout(150);page.screenshot(path=str(OUT/(name+'.png')));result['screenshots'].append(name+'.png')
def no_pause(action,name):
 t=page.evaluate('()=>ContextualAudio.audio.currentTime');n=page.evaluate('()=>narrowPauses');action();page.wait_for_function('t=>ContextualAudio.audio.currentTime>t+.15',arg=t)
 check(page.evaluate('n=>ContextualAudio.inspect().playing&&narrowPauses===n',n),name)
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True,ignore_default_args=['--enable-unsafe-swiftshader','--unsafely-disable-devtools-self-xss-warnings','--mute-audio'])
  page=b.new_page(viewport={'width':320,'height':640});page.set_default_timeout(45000)
  page.on('pageerror',lambda e:result['errors'].append(str(e)));page.on('response',lambda r:result['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  page.goto(URL,wait_until='networkidle');page.locator('#respiratorySimulatorLaunch').click();page.wait_for_function('()=>!!CardiorespiratoryStudy.inspectBreathing()?.vertices');page.wait_for_function('()=>!ContextualAudio.inspect().loading')
  check(not page.evaluate('()=>ContextualAudio.inspect().playing'),'No autoplay on lung entry')
  page.locator('[data-audio-dock-play]').click();page.wait_for_function('()=>ContextualAudio.audio.currentTime>.3');page.evaluate('()=>{window.narrowPauses=0;ContextualAudio.audio.addEventListener("pause",()=>narrowPauses++);}')
  for w,h in [(320,640),(360,740),(390,844),(768,1024),(844,390),(1024,768)]:
   before=page.evaluate('()=>({state:CardiorespiratoryStudy.getState(),camera:CardiorespiratoryStudy.inspectBreathing().camera})')
   no_pause(lambda:page.set_viewport_size({'width':w,'height':h}),f'Lung{w}: continuous original audio across layout')
   check(before==page.evaluate('()=>({state:CardiorespiratoryStudy.getState(),camera:CardiorespiratoryStudy.inspectBreathing().camera})'),f'Lung{w}: no model or camera takeover')
   check(page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),f'Lung{w}: no page overflow')
   info=page.locator('[data-explorer-quick-stage]').evaluate('e=>{const r=e.getBoundingClientRect();return {width:r.width,height:r.height,lineHeight:parseFloat(getComputedStyle(e).lineHeight),text:e.textContent}}');result['metrics'].append({'width':w,'stage_title':info})
   check(info['width']>=100 and info['height']<=info['lineHeight']*4,f'Lung{w}: stage title has readable width and at most four lines')
   shot(f'lung-{w}x{h}','.sim-breath-journey-toolbar')
  page.locator('[data-audio-dock-play]').click();page.locator('[data-home]').click();page.locator('#leadPlacementLaunch').click();page.wait_for_function('()=>document.querySelector("#lead3DStatus")?.textContent.includes("3D torso ready")')
  check(not page.evaluate('()=>ContextualAudio.inspect().playing'),'Lead navigation loads audio paused')
  for w,h in [(320,640),(360,740),(390,844),(768,1024),(844,390),(1024,768),(1440,1000)]:
   page.set_viewport_size({'width':w,'height':h});page.wait_for_timeout(150)
   tags=page.locator('.lead-3d-viewport').evaluate('''e=>{const r=e.getBoundingClientRect();return [...e.querySelectorAll('.lead-3d-dot-label')].filter(t=>!t.hidden).map(t=>{const b=t.getBoundingClientRect();return {id:t.dataset.marker,x:b.left-r.left,y:b.top-r.top,width:b.width,height:b.height,viewportWidth:r.width,viewportHeight:r.height}})}''');result['metrics'].append({'width':w,'lead_tags':tags})
   check(len(tags)==6,f'Lead{w}: all six chest-lead tags remain present')
   check(all(t['x']>=0 and t['y']>=0 and t['x']+t['width']<=t['viewportWidth'] and t['y']+t['height']<=t['viewportHeight'] for t in tags),f'Lead{w}: every chest-lead tag stays inside viewer')
   overlaps=any(a['x']<c['x']+c['width'] and a['x']+a['width']>c['x'] and a['y']<c['y']+c['height'] and a['y']+a['height']>c['y'] for i,a in enumerate(tags) for c in tags[i+1:])
   check(not overlaps,f'Lead{w}: chest-lead text tags do not overlap')
   check(page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),f'Lead{w}: no page overflow');shot(f'lead-{w}x{h}','.lead-3d-viewport')
  check(not result['errors'],'No browser JavaScript errors');check(not result['http_errors'],'No missing requested files');result['passed']=True;b.close()
except Exception as e:result.update(passed=False,error=str(e),traceback=traceback.format_exc())
finally:
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result.get('passed'),'checks':len(result['checks']),'error':result.get('error'),'output':str(OUT)}))
