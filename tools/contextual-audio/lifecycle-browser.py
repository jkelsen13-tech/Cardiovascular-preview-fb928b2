"""Cold route and stale source-load regressions for contextual explanations."""
from pathlib import Path
import datetime
import json
import os
import re
import traceback
from playwright.sync_api import sync_playwright

OUT=Path('/workspace/scratch/contextual-audio-20261022/lifecycle')/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
OUT.mkdir(parents=True,exist_ok=True)
result={'checks':[],'page_errors':[],'output':str(OUT),'qualification':'Internal cloud browser regression; actual original media, controlled network delay only. No listening/hardware timing qualification.'}
def check(condition,message):
 result['checks'].append({'name':message,'passed':bool(condition)})
 if not condition:raise AssertionError(message)
try:
 with sync_playwright() as pw:
  b=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True,ignore_default_args=['--enable-unsafe-swiftshader','--unsafely-disable-devtools-self-xss-warnings','--mute-audio'])
  p=b.new_page(viewport={'width':1366,'height':1100});p.set_default_timeout(30000)
  p.on('pageerror',lambda error:result['page_errors'].append(str(error)))
  held=[]
  p.route('**/heart-study-v3/explorer.js',lambda route:held.append(route))
  p.goto(os.environ.get('CARDIO_BASE_URL','http://127.0.0.1:8881/'),wait_until='networkidle')
  p.locator('#heartV3Launch').click();p.wait_for_function('()=>HeartV3Study.inspect().renderer?.sourceReady')
  p.locator('[data-context-audio-action=play]').click();p.wait_for_function('()=>ContextualAudio.audio.currentTime>.3')
  p.locator('[data-h3-action=inspector]').click();p.locator('[data-h3-route=routeB]').click()
  p.wait_for_timeout(100)
  check(len(held)==1,'Cold explorer request is held before route completion')
  before=p.evaluate('()=>ContextualAudio.audio.currentTime')
  p.wait_for_timeout(650)
  check(p.evaluate('()=>ContextualAudio.inspect().playing&&ContextualAudio.audio.currentTime')>before+.4,'Narration continues during cold route preparation')
  held.pop().continue_()
  p.wait_for_function('()=>HeartV3Study.getState().stage==="routeB.wall"')
  p.wait_for_function('()=>ContextualAudio.inspect().context.key.includes("routeB.wall")')
  check(p.evaluate('()=>ContextualAudio.inspect().availableIds[0]')=='M03.01','Late route completion updates related choices without another user action')
  for stage in ['routeB.pericardium','routeB.tissue','routeB.cell']:
   p.locator('[data-h3-near-next]').click();p.wait_for_function('s=>HeartV3Study.getState().stage===s',arg=stage)
  p.wait_for_function('()=>ContextualAudio.inspect().availableIds[0]==="M04.08"')
  check(p.evaluate('()=>ContextualAudio.inspect().playing&&ContextualAudio.inspect().lessonId==="M02.01"'),'Manual microscopic route changes preserve current recording')
  p.locator('#contextualAudio').scroll_into_view_if_needed();p.screenshot(path=str(OUT/'cold-route-context.png'))
  p.close()

  p=b.new_page();p.set_default_timeout(30000);p.on('pageerror',lambda error:result['page_errors'].append(str(error)))
  p.add_init_script('''window.contextObjectUrls=[];const create=URL.createObjectURL.bind(URL),revoke=URL.revokeObjectURL.bind(URL);URL.createObjectURL=b=>{const u=create(b);contextObjectUrls.push({kind:'create',url:u});return u;};URL.revokeObjectURL=u=>{contextObjectUrls.push({kind:'revoke',url:u});return revoke(u);};''')
  held=[];p.route('**/M02_01_adam_multilingual_v2.mp3',lambda route:held.append(route))
  p.goto(os.environ.get('CARDIO_BASE_URL','http://127.0.0.1:8881/'),wait_until='networkidle')
  p.locator('#heartV3Launch').click();p.wait_for_function('()=>ContextualAudio.inspect().loading')
  p.wait_for_timeout(100);check(len(held)==1,'Initial media fetch is held')
  p.get_by_role('button',name=re.compile('All study modes')).click();p.locator('#asptLaunch').click()
  p.wait_for_function('()=>ContextualAudio.inspect().lessonId==="M01.01"&&!ContextualAudio.inspect().loading')
  try:held.pop().continue_()
  except Exception as error:result['aborted_request_release']=str(error)
  p.wait_for_timeout(300)
  check(p.evaluate('()=>ContextualAudio.inspect().lessonId==="M01.01"&&!ContextualAudio.inspect().playing&&!ContextualAudio.inspect().error'),'Delayed old media cannot replace or start the new page recording')
  p.locator('[data-context-audio-action=play]').click();p.wait_for_function('()=>ContextualAudio.inspect().playing')
  p.evaluate('()=>{window.disposedContextAudio=ContextualAudio.audio;ContextualAudio.dispose();}')
  check(p.evaluate('()=>disposedContextAudio.paused&&!document.getElementById("contextualAudio")'),'Disposal stops only its own audio and removes controls')
  urls=p.evaluate('()=>contextObjectUrls')
  check(sorted(x['url'] for x in urls if x['kind']=='create')==sorted(x['url'] for x in urls if x['kind']=='revoke'),'All prepared object URLs are revoked on replacement/disposal')
  check(not result['page_errors'],'No JavaScript errors in lifecycle cases')
  result['passed']=True;b.close()
except Exception as error:
 result.update(passed=False,error=str(error),traceback=traceback.format_exc())
finally:
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 (OUT.parent/'latest.json').write_text(json.dumps({'result':str(OUT/'result.json'),'passed':result.get('passed')},indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='traceback'},indent=2),flush=True)
