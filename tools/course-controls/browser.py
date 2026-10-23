"""Course-focused controls acceptance using native UI and sandboxed Chromium.
No audio-output, physical iPad, or learning-outcome qualification is implied.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import os,json,traceback,datetime,re
OUT=Path(os.environ.get('COURSE_CONTROLS_OUT','/tmp/course-controls'));OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('CARDIO_BASE_URL','http://127.0.0.1:8890/')
result={'url':URL,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'checks':[],'errors':[],'http_errors':[],'screenshots':[],'inventories':{}}
def check(value,name):
 result['checks'].append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
 if len(result['checks'])%20==0:
  (OUT/'progress.json').write_text(json.dumps({'checks':len(result['checks']),'latest':name})+'\n');print(json.dumps({'checks':len(result['checks']),'latest':name}),flush=True)
def heart():return page.evaluate('()=>HeartV3Study.inspect()')
def audio():return page.evaluate('()=>ContextualAudio.inspect()')
def reveal(selector):
 page.locator(selector).evaluate("e=>{for(let p=e.parentElement;p;p=p.parentElement)if(p.tagName==='DETAILS')p.open=true;}")
def click(selector):
 reveal(selector);page.locator(selector).click()
def shot(name,selector):
 page.locator(selector).scroll_into_view_if_needed();page.screenshot(path=str(OUT/(name+'.png')));result['screenshots'].append(name+'.png')
def inventory(name,selector):
 result['inventories'][name]=page.locator(selector).evaluate('''root=>({controls:[...root.querySelectorAll('button,input,select,textarea,summary')].map(e=>({tag:e.tagName,type:e.type||'',data:{...e.dataset},label:e.getAttribute('aria-label')||e.labels?.[0]?.textContent||e.textContent,painted:e.checkVisibility(),options:e.options?[...e.options].map(o=>({value:o.value,label:o.textContent})):null})),graphs:[...root.querySelectorAll('svg,canvas')].map(e=>({tag:e.tagName,label:e.getAttribute('aria-label'),painted:e.checkVisibility()}))})''')
def overflow(name):check(page.evaluate('()=>document.documentElement.scrollWidth<=innerWidth'),name+': no horizontal page overflow')
def continues(action,name):
 t=audio()['time'];pauses=page.evaluate('()=>coursePauses');action();page.wait_for_function('t=>ContextualAudio.audio.currentTime>t+.15',arg=t)
 check(audio()['playing'] and page.evaluate('()=>coursePauses')==pauses,name+': narration continues without a pause')
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True,ignore_default_args=['--enable-unsafe-swiftshader','--unsafely-disable-devtools-self-xss-warnings','--mute-audio'])
  page=browser.new_page(viewport={'width':1440,'height':1000});page.set_default_timeout(45000)
  page.on('pageerror',lambda e:result['errors'].append(str(e)))
  page.on('response',lambda r:result['http_errors'].append({'url':r.url,'status':r.status}) if r.status>=400 else None)
  page.goto(URL,wait_until='networkidle');page.locator('#heartV3Launch').click();page.wait_for_function('()=>HeartV3Study.inspect().renderer?.sourceReady')
  page.wait_for_function('()=>!ContextualAudio.inspect().loading');page.wait_for_timeout(150)
  check(not audio()['playing'],'Initial heart explanation is user initiated')
  check(page.locator('[data-h3-course-view] option').count()==8,'All eight anatomical views remain available')
  check(page.locator('[data-h3-phase]').count()==5,'All five physiological phase controls remain')
  forbidden='[data-h3-blood-view],[data-h3-conduction-view],[data-h3-teaching-trace],[data-h3-label-size],[data-h3-leader],[data-h3-wall-highlight],[data-h3-parameters],.h3-analysis,.h3-metrics,[data-h3-pathway-display],[data-h3-cycle-group]'
  check(page.locator(forbidden).count()==0,'Removed technical tuners and six-plot dashboard are absent from DOM, including closed panels')
  check(not page.locator('.h3-live-trace').is_visible(),'No unrelated persistent waveform in ordinary heart view')
  inventory('heart-default','#heartV3Study');shot('heart-desktop-default','.h3-stage')
  modes=page.locator('[data-h3-course-view] option').evaluate_all('els=>els.map(e=>e.value)')
  for mode in modes:
   page.select_option('[data-h3-course-view]',mode)
   check(heart()['state']['mode']==mode and not heart()['state']['fallback'],'Native view selection retains functional '+mode)
  page.select_option('[data-h3-course-view]','outflow')
  for phase in ['passive-filling','atrial-contraction','isovolumetric-contraction','ejection','isovolumetric-relaxation']:
   click('[data-h3-phase="'+phase+'"]');r=heart()['renderer'];routes=r['outflow']['routes']
   check(len(routes)==2 and all(x['visible']==(x['open'] and x['flow']>0) for x in routes),'Outflow remains valve-correct at '+phase)
   check(all(x['depthTest'] for x in routes) and all(not x['visible'] for x in r['flowPaths']),'Outflow retains source routes/depth and no legacy floating arrows at '+phase)
  click('[data-h3-phase=ejection]');shot('heart-outflow-ejection','.h3-stage')
  click('[data-h3-action=conduction-focus]');check(heart()['state']['conductionView']=='pulse' and heart()['state']['conductionDisplay']=='full-pulse','Single conduction control selects timed full-path pulse')
  check(page.locator('.h3-live-trace').is_visible() and page.locator('.h3-teaching-figure svg').count()==1,'Conduction exposes one linked surface ECG')
  check(page.locator('[data-h3-electrical-select]').count()==4,'SA, AV, His and Purkinje inspection retained')
  for target in ['sa','avnode','his','purkinje']:
   click('[data-h3-electrical-select="'+target+'"]');check(heart()['state']['selected']==target and not heart()['state']['fallback'],'Electrical source inspection '+target)
  shot('heart-conduction','.h3-stage')
  click('[data-h3-action=conduction-focus]');reveal('[data-h3-select]');page.select_option('[data-h3-select]','sa');check(heart()['state']['conductionView']=='pulse','Direct node selection uses the same timed conduction default')
  click('[data-h3-action=trace-blood]');check(heart()['state']['bloodView']=='filled' and heart()['state']['conductionView']=='off','Explicit blood tracing restores a blood context after conduction')
  for _ in range(6):click('[data-h3-action=flow-next]')
  click('[data-h3-action=flow-isolate]');t=heart()['state']['time'];click('[data-h3-action=reset-view]')
  check(not heart()['state']['flowTracing'] and not heart()['state']['flowIsolate'] and heart()['state']['time']==t,'Reset view exits isolated trace coherently without advancing physiology')
  reveal('[data-h3-action=route][data-h3-route=routeA]')
  route_contract=page.evaluate('()=>HeartV3Content.routes.map(r=>({id:r.id,stages:r.stages.map(s=>s.id)}))')
  result['route_contract']=route_contract
  for route in route_contract:
   click('[data-h3-action=route][data-h3-route="'+route['id']+'"]')
   for stage in route['stages']:
    click('[data-h3-stage="'+stage+'"]');key=route['id']+'.'+stage
    page.wait_for_function('key=>HeartV3Study.getState().stage===key&&HeartV3Study.inspect().detail?.stage===key',arg=key)
    check(not heart()['state']['fallback'],'Retained heart simulation '+key)
   if route['id']=='routeC':
    check(page.locator('[data-h3-traces] svg').count()>=2,'Nodal and ventricular action potentials remain in their conduction lesson')
    check('refractor' in page.locator('[data-h3-traces]').inner_text().lower(),'Refractory-period teaching retained')
    shot('cell-action-potentials','[data-h3-traces]')
   click('[data-h3-return]')
  page.locator('[data-audio-dock-play]').click();page.wait_for_function('()=>ContextualAudio.audio.currentTime>.4')
  page.evaluate('()=>{window.coursePauses=0;ContextualAudio.audio.addEventListener("pause",()=>coursePauses++);}');camera=heart()['camera']
  continues(lambda:page.select_option('[data-h3-course-view]','four-chamber'),'Manual anatomical view')
  continues(lambda:click('[data-h3-phase=ejection]'),'Manual physiological phase')
  for width,height in [(320,640),(390,844),(768,1024),(844,390),(1024,768),(1440,1000)]:
   before=heart()['state'];continues(lambda:page.set_viewport_size({'width':width,'height':height}),f'Heart resize {width}x{height}')
   check(heart()['state']==before,f'Heart {width}x{height}: layout preserves paused model state')
   overflow(f'Heart {width}x{height}')
   check(page.locator('[data-h3-action=play]').bounding_box()['height']>=44,f'Heart {width}x{height}: primary touch target >=44px')
   shot(f'heart-{width}x{height}','.h3-stage')
  page.locator('[data-audio-dock-play]').click();page.set_viewport_size({'width':390,'height':844})
  reveal('[data-h3-text-size]');page.select_option('[data-h3-text-size]','2');overflow('Heart 200% text');page.select_option('[data-h3-text-size]','1')
  page.set_viewport_size({'width':1440,'height':1000});click('[data-h3-action=home]');page.locator('#respiratorySimulatorLaunch').click()
  page.wait_for_function('()=>!!CardiorespiratoryStudy.inspectBreathing()?.vertices');page.wait_for_function('()=>!ContextualAudio.inspect().loading')
  check(not audio()['playing'],'Lung page transition loads explanation paused')
  lung_forbidden='[data-breath-rate],[data-breath-depth],[data-breath-context],[data-breath-leader],[data-layer3d],[data-resp-rate],[data-resp-depth],[data-mechanics-form],[data-mechanics-curves] svg,[data-mechanics-curves] .sim-mechanics-figure'
  check(page.locator(lung_forbidden).count()==0,'Lung tuners and four mechanics curves are removed from DOM')
  check(page.locator('.course-capnogram').count()==1,'Course capnogram retained')
  check(not page.locator('[data-breath-play]').is_visible() and page.locator('[data-play]').is_visible(),'One ordinary breathing transport; fullscreen transport retained')
  inventory('lung-default','#cardiorespiratoryStudy');shot('lung-desktop-default','.sim-breath-canvas')
  before=page.evaluate('()=>CardiorespiratoryStudy.inspectBreathing().vertices');click('[data-play]');page.wait_for_function('()=>CardiorespiratoryStudy.getState().time>.4');click('[data-play]')
  check(page.evaluate('()=>CardiorespiratoryStudy.inspectBreathing().vertices')!=before,'Original lung deformation still responds to independent breathing clock')
  for phase in range(5):
   click('[data-resp-phase="'+str(phase)+'"]');check(bool(page.locator('[data-cap-marker]').get_attribute('cx')),'Capnogram phase/clock marker retained '+str(phase))
  reveal('[data-ventilation]');page.select_option('[data-ventilation]','positive');check(page.evaluate('()=>CardiorespiratoryStudy.getState().ventilation')=='positive','Positive-pressure teaching comparison retained');page.select_option('[data-ventilation]','spontaneous')
  for i in range(13):
   click('[data-explorer-quick-next]' if i else '[data-breath-reset]') if i else None
   page.wait_for_function('i=>CardiorespiratoryStudy.inspectBreathing().explorer.index===i',arg=i)
   check(page.evaluate('()=>CardiorespiratoryStudy.inspectBreathing().explorer.index')==i,'Retained airway simulation stage '+str(i+1))
  shot('alveolar-capillary-lesson','.sim-breath-canvas');click('[data-breath-reset]')
  page.select_option('[data-breath-mode]','alveolar');check(page.evaluate('()=>CardiorespiratoryStudy.inspectBreathing().mode')=='alveolar','Magnified gas-exchange simulation retained');page.select_option('[data-breath-mode]','whole')
  page.locator('[data-audio-dock-play]').click();page.wait_for_function('()=>ContextualAudio.inspect().playing');page.evaluate('()=>{window.coursePauses=0;ContextualAudio.audio.addEventListener("pause",()=>coursePauses++);}');
  continues(lambda:page.select_option('[data-breath-select]','diaphragm'),'Manual lung anatomy selection')
  continues(lambda:click('[data-play]'),'Independent breathing Play');continues(lambda:click('[data-play]'),'Independent breathing Pause')
  for width,height in [(320,640),(390,844),(768,1024),(844,390),(1024,768)]:
   continues(lambda:page.set_viewport_size({'width':width,'height':height}),f'Lung resize {width}x{height}');overflow(f'Lung {width}x{height}')
   if width<=850:check(page.locator('[data-organ-host]').evaluate('e=>!!e.nextElementSibling.querySelector("[data-mechanics-values]")'),f'Lung {width}x{height}: single cycle control stays beside model')
   shot(f'lung-{width}x{height}','.sim-breath-canvas')
  page.locator('[data-audio-dock-play]').click();reveal('[data-unload-anatomy]');click('[data-unload-anatomy]');check(page.locator('[data-mechanics-values]').is_visible(),'3D unload keeps breathing cycle controls');click('[data-load-breathing]');page.wait_for_function('()=>!!CardiorespiratoryStudy.inspectBreathing()?.vertices');click('[data-play]');click('[data-play]')
  reveal('[data-breath-fullscreen]');click('[data-breath-fullscreen]');page.wait_for_function('()=>!!document.fullscreenElement');check(page.locator('[data-breath-play]').is_visible(),'Native fullscreen exposes core play/scrub');click('[data-breath-play]');click('[data-breath-play]');page.evaluate('()=>document.exitFullscreen()')
  page.set_viewport_size({'width':1440,'height':1000});click('[data-home]');page.locator('#leadPlacementLaunch').click();page.wait_for_function('()=>document.querySelector("#lead3DStatus")?.textContent.includes("3D torso ready")')
  check(page.locator('.lead-layer-controls,.lead-concept-bar').count()==0,'Lead lab removes body/layer tuning and duplicate display switches')
  check(page.locator('#leadColorLegend').is_visible() and page.locator('#leadTypesLegend').is_visible(),'AHA colors and bipolar/unipolar teaching remain')
  check(page.locator('[data-view-preset]').count()==1,'One Reset view replaces duplicate camera presets')
  inventory('lead-default','#leadPlacementHome');shot('lead-desktop-default','.lead-view-shell')
  for tab in ['explore','cards','quiz','guided']:
   click('#leadPlacementHome [data-tab="'+tab+'"]');check(page.evaluate('()=>LeadPlacementLab.getState().tab')==tab,'Lead '+tab+' lesson retained')
  for width,height in [(320,640),(390,844),(768,1024),(844,390),(1024,768)]:
   page.set_viewport_size({'width':width,'height':height});overflow(f'Lead {width}x{height}');shot(f'lead-{width}x{height}','.lead-view-shell')
  page.set_viewport_size({'width':1024,'height':768});click('#leadStudyBack');page.locator('#homeMenu').get_by_role('button',name=re.compile('ECG Waves & Intervals')).click()
  check(page.locator('#ecgStudyHome').is_visible(),'ECG waves and intervals remain available');inventory('ecg-waves','#ecgStudyHome');shot('ecg-measurement','#ecgStudyHome')
  check(not result['errors'],'No browser JavaScript errors');check(not result['http_errors'],'No missing requested assets');result['passed']=True;browser.close()
except Exception as e:result.update(passed=False,error=str(e),traceback=traceback.format_exc())
finally:
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'passed':result.get('passed'),'checks':len(result['checks']),'error':result.get('error'),'output':str(OUT)}))
