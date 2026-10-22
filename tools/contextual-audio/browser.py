"""Focused corrected-requirement regression. Real media/UI, no audio mocks.
Run with a local HTTP preview and preinstalled Playwright/Chromium. Output stays
outside the source checkout. This is not physical listening or sync acceptance.
"""
from pathlib import Path
import json
import os
import re
import traceback
import datetime
from playwright.sync_api import sync_playwright

OUT_BASE=Path(os.environ.get('CONTEXTUAL_AUDIO_OUT','/workspace/scratch/contextual-audio-20261022/browser'))
RUN=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
OUT=OUT_BASE/'runs'/RUN
OUT.mkdir(parents=True,exist_ok=True)
URL=os.environ.get('CARDIO_BASE_URL','http://127.0.0.1:8881/')
result={'url':URL,'run':RUN,'checks':[],'page_errors':[],'http_errors':[],'qualification':'Private local sandboxed Chromium UI and media-element checks. No actual sound output, physical iPad or Cursor qualification.'}
page=None
def check(condition,message):
 result['checks'].append({'name':message,'passed':bool(condition)})
 if not condition:raise AssertionError(message)
def inspect():return page.evaluate('()=>ContextualAudio.inspect()')
def heart():return page.evaluate('()=>({state:HeartV3Study.getState(),camera:HeartV3Study.guided.capture().camera,active:HeartV3Study.inspect().active})')
def lungs():return page.evaluate('()=>({state:CardiorespiratoryStudy.getState(),scene:CardiorespiratoryStudy.inspectBreathing()})')
def audio_play():
 page.locator('[data-context-audio-action=play]').click()
 page.wait_for_function('()=>ContextualAudio.inspect().playing&&!ContextualAudio.inspect().pending')
def pause_audio():
 if inspect()['playing']:page.locator('[data-context-audio-action=play]').click()
def shot(name):
 page.locator('#contextualAudio').scroll_into_view_if_needed()
 page.screenshot(path=str(OUT/(name+'.png')))
def continuous(action,description):
 before=inspect();pauses=page.evaluate('()=>window.contextAudioPauses')
 action()
 page.wait_for_function('t=>ContextualAudio.audio.currentTime>t+.2',arg=before['time'])
 after=inspect()
 check(after['playing'] and after['lessonId']==before['lessonId'],description+': current recording continues')
 check(page.evaluate('()=>window.contextAudioPauses')==pauses,description+': no interaction-driven pause')
 return after

try:
 with sync_playwright() as pw:
  browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True,ignore_default_args=['--enable-unsafe-swiftshader','--unsafely-disable-devtools-self-xss-warnings','--mute-audio'])
  page=browser.new_page(viewport={'width':1366,'height':1100});page.set_default_timeout(30000)
  page.on('pageerror',lambda error:result['page_errors'].append(str(error)))
  page.on('response',lambda response:result['http_errors'].append({'url':response.url,'status':response.status}) if response.status>=400 else None)
  page.goto(URL,wait_until='networkidle')
  check(not page.locator('#contextualAudio').is_visible(),'No disconnected audiobook player on home menu')
  check(page.evaluate('()=>typeof GuidedStudy')=='undefined','No old Guided/Explore session is active')
  check(page.locator('#guidedStudyPlayer').count()==0,'No old takeover/Return-to-Guided UI')
  page.evaluate('()=>localStorage.setItem("contextual-sentinel","preserve")')
  page.locator('#heartV3Launch').click()
  page.wait_for_function('()=>HeartV3Study.inspect().renderer?.sourceReady')
  check(page.locator('#contextualAudio').is_visible(),'Heart explanation automatically available')
  check(inspect()['lessonId']=='M02.01' and not inspect()['playing'],'Relevant chamber explanation loads paused')
  page.evaluate('''()=>{window.contextAudioPauses=0;ContextualAudio.audio.addEventListener('pause',()=>contextAudioPauses++);window.forbiddenAudioAdapterCalls=[];for(const [name,api]of [['heart',HeartV3Study],['lungs',CardiorespiratoryStudy],['lead',LeadPlacementLab]])for(const key of ['prepare','apply','restore','pause']){if(api.guided?.[key])api.guided[key]=()=>{forbiddenAudioAdapterCalls.push(name+'.'+key);throw Error('Audio must not control a simulator');};}}''')
  # A getter-only capture avoids the guarded adapter and records actual camera.
  # Capture is read-only; all preparation/apply/restore/pause methods are guarded.
  page.locator('#contextualAudio').scroll_into_view_if_needed()
  baseline=heart();scroll=page.evaluate('()=>({x:scrollX,y:scrollY})')
  audio_play();page.wait_for_function('()=>ContextualAudio.audio.currentTime>.5')
  check(heart()==baseline,'Playing narration leaves paused heart state and camera exact')
  check(page.evaluate('()=>({x:scrollX,y:scrollY})')==scroll,'Playing narration does not scroll the page')
  pause_audio();page.wait_for_function('()=>ContextualAudio.audio.readyState>=1')
  page.locator('[data-context-audio-seek]').evaluate("el=>{el.value='22';el.dispatchEvent(new Event('input',{bubbles:true}));}")
  page.wait_for_function('()=>Math.abs(ContextualAudio.audio.currentTime-22)<.2')
  check(heart()==baseline,'Seeking across original scene cues does not apply scenes or change model time')
  audio_play();page.wait_for_timeout(700);pause_audio()
  check(heart()==baseline,'Playback after a cue seek still leaves simulator unchanged')
  page.locator('[data-context-audio-action=replay]').click();page.wait_for_function('()=>ContextualAudio.inspect().playing&&ContextualAudio.audio.currentTime<3')
  continuous(lambda:page.locator('[data-h3-chamber=ra]').click(),'Manual heart chamber selection')
  check('M02.02' in inspect()['availableIds'],'Chamber selection refreshes related choices')
  continuous(lambda:page.locator('[data-h3-phase=ejection]').click(),'Manual heart phase selection')
  check('M03.05' in inspect()['availableIds'],'Manually chosen phase offers its explanation')
  check(page.locator('[data-context-audio-continuing]').is_visible(),'Current audio stays clearly identified when context changes')
  continuous(lambda:page.locator('[data-h3-action=play]').click(),'Starting independent heart simulation')
  time=heart()['state']['time'];page.wait_for_timeout(250)
  check(heart()['state']['playing'] and heart()['state']['time']!=time,'Heart clock runs independently while listening')
  pause_audio();time=heart()['state']['time'];page.wait_for_timeout(250)
  check(heart()['state']['playing'] and heart()['state']['time']!=time,'Pausing explanation does not pause heart simulation')
  audio_play();continuous(lambda:page.locator('[data-h3-action=play]').click(),'Pausing independent heart simulation')
  shot('heart-contextual-listening')
  # Explicit page navigation is the sole automatic pause boundary.
  page.get_by_role('button',name=re.compile('All study modes')).click()
  page.locator('#homeMenu').get_by_role('button',name='Respiratory Simulator v2').click()
  page.wait_for_function('()=>ContextualAudio.inspect().context?.page==="sim-respiratory"')
  check(not inspect()['playing'] and inspect()['time']==0,'Manual page navigation loads new related context paused')
  page.wait_for_selector('[data-breath-select]')
  page.locator('[data-breath-select]').select_option('diaphragm')
  page.wait_for_function('()=>ContextualAudio.inspect().availableIds.includes("M05.06")')
  page.select_option('[data-context-audio-lesson]','M05.06')
  before=lungs();audio_play();page.wait_for_function('()=>ContextualAudio.audio.currentTime>.5')
  check(lungs()==before,'Lung narration leaves paused mechanics, anatomy and camera exact')
  continuous(lambda:page.locator('[data-breath-view=side]').click(),'Manual lung camera change')
  continuous(lambda:page.locator('[data-breath-select]').select_option('leftlung'),'Manual lung anatomy selection')
  continuous(lambda:page.locator('[data-breath-play]').click(),'Starting independent breathing simulation')
  before_time=lungs()['state']['time'];page.wait_for_timeout(250)
  check(lungs()['state']['playing'] and lungs()['state']['time']!=before_time,'Breathing clock runs independently while listening')
  continuous(lambda:page.locator('[data-breath-play]').click(),'Pausing independent breathing simulation')
  shot('lung-contextual-listening')
  page.get_by_role('button',name=re.compile('All study modes')).click()
  page.locator('#asptLaunch').click()
  page.wait_for_function('()=>ContextualAudio.inspect().context?.page==="guide"')
  check(inspect()['lessonId']=='M01.01' and not inspect()['playing'],'Study guide orientation offers contextual audio paused')
  page.locator('#asptHome .aspt-lesson-list [data-id=circulation]').click()
  page.wait_for_function('()=>ContextualAudio.inspect().availableIds.includes("M02.08")')
  page.select_option('[data-context-audio-lesson]','M02.08');audio_play()
  continuous(lambda:page.locator('#asptHome .aspt-lesson-list [data-id=disease]').click(),'Manual study-guide topic change')
  check('M14.01' in inspect()['availableIds'],'New study-guide topic offers its own recordings')
  page.select_option('[data-context-audio-lesson]','M14.01')
  check(not inspect()['playing'] and inspect()['time']==0,'Explicit recording selection changes audio paused')
  original=page.evaluate('()=>GuidedStudyLessons.find(l=>l.id==="M14.01").transcript')
  check(page.locator('[data-context-audio-transcript]').text_content()==original,'Transcript access preserves exact original text')
  page.set_viewport_size({'width':390,'height':844});shot('mobile-contextual-guide')
  box=page.locator('#contextualAudio').bounding_box()
  check(box['x']>=0 and box['x']+box['width']<=391,'Contextual controls fit a 390px viewport')
  page.get_by_role('button',name=re.compile('All study modes')).click();page.locator('#leadPlacementLaunch').click()
  page.wait_for_function('()=>ContextualAudio.inspect().context?.page==="lead"')
  check('M07.05' in inspect()['availableIds'] and not inspect()['playing'],'Lead lab offers placement explanation paused')
  page.locator('#leadStudyBack').click()
  page.get_by_role('button',name='⚡ ECG Waves & Intervals',exact=False).click()
  page.wait_for_function('()=>ContextualAudio.inspect().context?.page==="ecg-study"')
  check(any(x.startswith('M08.') for x in inspect()['availableIds']),'ECG study offers wave/interval explanations')
  check(page.evaluate('()=>window.forbiddenAudioAdapterCalls').__len__()==0,'No audio-driven simulator preparation/apply/restore/pause calls')
  check(page.evaluate('()=>localStorage.getItem("contextual-sentinel")')=='preserve','Unrelated storage remains untouched')
  check(not result['page_errors'],'No JavaScript page errors')
  check(not result['http_errors'],'No missing source/media assets')
  result['passed']=True;browser.close()
except Exception as error:
 result.update(passed=False,error=str(error),traceback=traceback.format_exc())
 if page and not page.is_closed():
  try:page.screenshot(path=str(OUT/'failure.png'));result['failure_context']=inspect()
  except Exception:pass
finally:
 (OUT/'result.json').write_text(json.dumps(result,indent=2)+'\n')
 (OUT_BASE/'latest.json').write_text(json.dumps({'run':RUN,'result':str(OUT/'result.json'),'passed':result.get('passed')},indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k!='traceback'},indent=2),flush=True)
