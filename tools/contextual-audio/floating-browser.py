"""Floating control regression using real UI and original MP3s.
Requires an existing preview and preinstalled sandboxed Chromium/Playwright.
CARDIO_BASE_URL selects local or hosted preview; output remains outside source.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
import datetime, json, os, re, traceback

BASE=Path(os.environ.get('CONTEXTUAL_AUDIO_OUT','/workspace/scratch/floating-audio-20261022/browser'))
OUT=BASE/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('CARDIO_BASE_URL','http://127.0.0.1:8882/')
result={'url':URL,'checks':[],'page_errors':[],'http_errors':[],'output':str(OUT),'qualification':'Sandboxed cloud browser UI/media checks with original recordings; no physical iPad, speaker output or hardware synchronization claim.'}
def check(value,name):
 result['checks'].append({'name':name,'passed':bool(value)})
 if not value:raise AssertionError(name)
try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True,ignore_default_args=['--enable-unsafe-swiftshader','--unsafely-disable-devtools-self-xss-warnings','--mute-audio'])
  page=browser.new_page(viewport={'width':1366,'height':1000});page.set_default_timeout(45000)
  page.on('pageerror',lambda error:result['page_errors'].append(str(error)))
  page.on('response',lambda response:result['http_errors'].append({'url':response.url,'status':response.status}) if response.status>=400 else None)
  page.goto(URL,wait_until='networkidle')
  state=lambda:page.evaluate('()=>ContextualAudio.inspect()')
  model=lambda:page.evaluate('()=>({state:HeartV3Study.getState(),camera:HeartV3Study.guided.capture().camera})')
  scroll=lambda:page.evaluate('()=>[scrollX,scrollY]')
  floating=page.locator('[data-audio-dock-play]');toggle=page.locator('[data-audio-dock-toggle]');panel=page.locator('#contextAudioDockPanel')
  def play():
   floating.click();page.wait_for_function('()=>ContextualAudio.inspect().playing&&!ContextualAudio.inspect().pending')
  def pause():
   floating.click();page.wait_for_function('()=>!ContextualAudio.inspect().playing')
  def stable_box():
   box=floating.bounding_box();return {key:round(box[key],1) for key in ['x','y','width','height']}
  def no_pause(action,name):
   before=state();pauses=page.evaluate('()=>window.floatAudioPauses');action()
   page.wait_for_function('t=>ContextualAudio.audio.currentTime>t+.2',arg=before['time'])
   check(state()['playing'] and state()['lessonId']==before['lessonId'] and page.evaluate('()=>window.floatAudioPauses')==pauses,name)
  check(not page.locator('#contextualAudioDock').is_visible(),'Dock hidden on unsupported home menu')
  check(page.evaluate('()=>typeof GuidedStudy')=='undefined','No obsolete tour runtime')
  page.locator('#heartV3Launch').click();page.wait_for_function('()=>HeartV3Study.inspect().renderer?.sourceReady')
  page.wait_for_function('()=>!ContextualAudio.inspect().loading')
  check(page.locator('#contextualAudioDock').is_visible() and not state()['playing'],'Dock available on heart page without autoplay')
  check(page.locator('#contextualAudio audio').count()==1 and page.locator('#contextualAudioDock audio').count()==0,'Dock shares the original single audio element')
  check(floating.get_attribute('aria-label').startswith('Play explanation') and 'M02.01' in floating.get_attribute('aria-label'),'Circular control announces action and current recording')
  page.evaluate('''()=>{window.floatAudioPauses=0;ContextualAudio.audio.addEventListener('pause',()=>floatAudioPauses++);window.floatForbidden=[];for(const [name,api]of [['heart',HeartV3Study],['lung',CardiorespiratoryStudy]])for(const key of ['prepare','apply','restore','pause'])if(api.guided?.[key])api.guided[key]=()=>{floatForbidden.push(name+'.'+key);throw Error('Audio must not control model');};}''')
  box=stable_box();page.evaluate('()=>window.scrollBy(0,650)')
  check(scroll()[1]>0 and stable_box()==box,'Circular control remains at exact viewport position while scrolling')
  before=model();position=scroll();play();page.wait_for_function('()=>ContextualAudio.audio.currentTime>.5')
  check(model()==before and scroll()==position,'Floating Play changes neither model/camera nor page position')
  check(page.locator('[data-context-audio-action=play]').text_content()=='Pause explanation' and 'Playing' in page.locator('[data-audio-dock-state]').text_content(),'Inline and floating playing state synchronize')
  no_pause(lambda:toggle.click(),'Opening selector preserves current recording and continuous playback')
  check(panel.is_visible() and toggle.get_attribute('aria-expanded')=='true' and page.locator('[data-audio-dock-lesson]').evaluate('el=>el===document.activeElement'),'Disclosure exposes selector and keyboard focus')
  check(scroll()==position,'Opening selector never scrolls page')
  no_pause(lambda:page.locator('[data-audio-dock-close]').click(),'Closing selector preserves current recording and playback position')
  check(toggle.evaluate('el=>el===document.activeElement') and toggle.get_attribute('aria-expanded')=='false','Close returns focus to disclosure without scrolling')
  no_pause(lambda:page.locator('[data-h3-chamber=ra]').click(),'Normal chamber selection does not pause audio')
  no_pause(lambda:page.locator('[data-h3-phase=ejection]').click(),'Normal phase selection does not pause audio')
  toggle.click();page.wait_for_function('()=>document.querySelector("[data-audio-dock-lesson]").options.length>1')
  selected=page.locator('[data-audio-dock-lesson]').input_value()
  new_id=page.locator('[data-audio-dock-lesson] option').evaluate_all('(els,current)=>els.map(e=>e.value).find(v=>v!==current)',selected)
  before=model();position=scroll();url=page.url;scene_y=page.locator('[data-h3-stage]').bounding_box()['y'];page.select_option('[data-audio-dock-lesson]',new_id)
  page.wait_for_function('()=>!ContextualAudio.inspect().loading')
  check(state()['lessonId']==new_id and not state()['playing'] and state()['time']==0,'Floating lesson selection loads new audio paused')
  after=model();after_scroll=scroll()
  after_y=page.locator('[data-h3-stage]').bounding_box()['y']
  result['lesson_switch_evidence']={'model_unchanged':after==before,'url_unchanged':page.url==url,'scroll_before':position,'scroll_after':after_scroll,'scene_viewport_y_before':scene_y,'scene_viewport_y_after':after_y}
  # Browser scroll anchoring compensates for changed inline transcript/warning
  # height above the viewport. Check the actual scene stays put, not scrollY.
  check(after==before and page.url==url,'Floating lesson switch does not navigate or change anatomy/phase/time/camera')
  check(abs(after_y-scene_y)<1,'Lesson switch preserves visible scene position through browser scroll anchoring')
  check(page.locator('[data-context-audio-lesson]').input_value()==new_id,'Floating lesson selector synchronizes inline selector')
  page.locator('[data-audio-dock-close]').click()
  page.locator('[data-context-audio-seek]').evaluate("el=>{el.value='7';el.dispatchEvent(new Event('input',{bubbles:true}));}")
  page.wait_for_function('()=>Math.abs(ContextualAudio.audio.currentTime-7)<.2')
  time=state()['time'];toggle.press('Enter');page.keyboard.press('Escape')
  check(abs(state()['time']-time)<.05 and not state()['playing'] and not panel.is_visible(),'Keyboard opening/Escape preserves exact paused audio position')
  check(toggle.evaluate('el=>el===document.activeElement'),'Escape restores disclosure focus')
  toggle.press('Space');check(panel.is_visible(),'Space activates native disclosure button')
  page.keyboard.press('Escape');floating.press('Space');page.wait_for_function('()=>ContextualAudio.inspect().playing&&!ContextualAudio.inspect().pending')
  check(page.locator('[data-context-audio-action=play]').text_content()=='Pause explanation','Keyboard floating Play synchronizes inline control')
  page.locator('[data-context-audio-action=play]').click();page.wait_for_function('()=>!ContextualAudio.inspect().playing')
  check(floating.get_attribute('aria-label').startswith('Play explanation') and 'Paused' in page.locator('[data-audio-dock-state]').text_content(),'Inline Pause synchronizes floating control')
  page.select_option('[data-context-audio-lesson]','M03.05');page.wait_for_function('()=>!ContextualAudio.inspect().loading')
  check(page.locator('[data-audio-dock-lesson]').input_value()=='M03.05' and 'M03.05' in page.locator('[data-audio-dock-state]').text_content(),'Inline lesson selection synchronizes dock title and selector')
  play();page.wait_for_function('()=>ContextualAudio.audio.currentTime>.3')
  no_pause(lambda:page.locator('[data-h3-action=play]').click(),'Starting independent heart simulation preserves narration')
  t=model()['state']['time'];page.wait_for_timeout(200)
  check(model()['state']['playing'] and model()['state']['time']!=t,'Simulation runs independently with floating controls')
  no_pause(lambda:page.locator('[data-h3-action=play]').click(),'Pausing independent simulation preserves narration')
  pause()
  page.locator('[data-h3-action=fullscreen]').click()
  page.wait_for_function('()=>!!document.fullscreenElement||!!document.querySelector(".h3-expanded")')
  check(floating.is_visible(),'Floating controls remain accessible in native expanded view')
  exit_box=page.locator('[data-h3-action=fullscreen]').bounding_box();dock_box=floating.bounding_box()
  check(dock_box['y']+dock_box['height']<=exit_box['y'] or dock_box['x']>=exit_box['x']+exit_box['width'] or dock_box['x']+dock_box['width']<=exit_box['x'],'Floating control clears native expanded-view exit')
  page.locator('[data-h3-action=fullscreen]').click();page.wait_for_function('()=>!document.fullscreenElement&&!document.querySelector(".h3-expanded")')
  # fullscreenchange can follow the fullscreenElement property update.
  page.wait_for_function('()=>document.getElementById("contextualAudioDock").parentElement===document.body')
  check(page.locator('#contextualAudioDock').evaluate('el=>el.parentElement===document.body'),'Dock returns from native fullscreen without moving audio element')
  for width,height in [(320,640),(390,844),(768,1024),(1024,768),(568,320)]:
   page.set_viewport_size({'width':width,'height':height});page.evaluate('()=>window.scrollTo(0,document.body.scrollHeight)')
   box=floating.bounding_box();check(box['width']>=56 and box['height']>=56 and box['x']>=0 and box['y']>=0 and box['x']+box['width']<=width and box['y']+box['height']<=height,f'{width}x{height}: circular touch control stays inside viewport')
   toggle.click();pbox=panel.bounding_box();check(pbox['x']>=0 and pbox['y']>=0 and pbox['x']+pbox['width']<=width and pbox['y']+pbox['height']<=height,f'{width}x{height}: expanded selector fits viewport')
   check(page.locator('[data-audio-dock-close]').bounding_box()['height']>=44 and page.locator('[data-audio-dock-lesson]').bounding_box()['height']>=44,f'{width}x{height}: selector/close touch targets at least44px')
   page.screenshot(path=str(OUT/f'floating-{width}x{height}.png'));page.locator('[data-audio-dock-close]').click()
  check(page.evaluate('()=>parseFloat(getComputedStyle(document.body,"::after").height)')>=88,'Bottom spacer keeps final page controls scrollable above dock')
  page.set_viewport_size({'width':1024,'height':768});page.get_by_role('button',name=re.compile('All study modes')).click()
  check(not page.locator('#contextualAudioDock').is_visible() and not state()['playing'],'Leaving supported page hides dock and stops its audio')
  page.locator('#asptLaunch').click();page.wait_for_function('()=>!ContextualAudio.inspect().loading')
  check(not state()['playing'] and page.locator('#contextAudioDockPanel').is_hidden(),'New page starts paused with selector closed')
  play();toggle.click();no_pause(lambda:page.locator('#asptHome .aspt-lesson-list [data-id=disease]').click(),'Manual topic change closes disclosure without interrupting narration')
  check('M14.01' in state()['availableIds'] and page.locator('[data-audio-dock-lesson] option[value="M14.01"]').count()==1,'Both selectors follow actual study-guide topic')
  check(page.locator('audio').evaluate_all('els=>els.filter(a=>!a.paused).length')==1,'Exactly one audio element plays with both control surfaces')
  check(not page.evaluate('()=>window.floatForbidden'),'No floating control called model takeover adapters')
  page.evaluate('()=>{window.floatDisposedAudio=ContextualAudio.audio;ContextualAudio.dispose();}')
  check(page.evaluate('()=>floatDisposedAudio.paused&&!document.getElementById("contextualAudioDock")&&!document.body.classList.contains("contextual-audio-present")'),'Disposal removes dock and spacer while stopping own audio')
  check(not result['page_errors'],'No JavaScript errors');check(not result['http_errors'],'No missing requested assets')
  result['passed']=True;browser.close()
except Exception as error:
 result.update(passed=False,error=str(error),traceback=traceback.format_exc())
finally:
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n');(BASE/'latest.json').write_text(json.dumps({'result':str(OUT/'result.json'),'passed':result.get('passed')},indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='traceback'},indent=2),flush=True)
