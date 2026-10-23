"""Native UI + actual WebGL evidence. No physical display/audio timing claim."""
from pathlib import Path
from playwright.sync_api import sync_playwright
import datetime, hashlib, json, os

OUT=Path(os.environ.get('OUTFLOW_BROWSER_OUT','/tmp/outflow-browser'))
OUT.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parents[2]
URL=os.environ.get('CARDIO_BASE_URL','http://127.0.0.1:8883/')
report={'url':URL,'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'localSourceSHA256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['heart-study-v3/sourced-anatomy.js','heart-study-v3/renderer.js']},
        'checks':[],'captures':[],'errors':[],
        'limits':['Browser media events and screenshots do not capture speaker output or physical display presentation.','Illustrative source-bound proximal routes and inferred root connectors, not clinical CFD.']}

def check(value,label):
    assert value,label
    report['checks'].append(label)

with sync_playwright() as pw:
    browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,chromium_sandbox=True,
      ignore_default_args=['--enable-unsafe-swiftshader','--unsafely-disable-devtools-self-xss-warnings','--mute-audio'])
    page=browser.new_page(viewport={'width':1440,'height':1100})
    page.set_default_timeout(45000)
    page.on('pageerror',lambda e:report['errors'].append(str(e)))
    # Only expose the existing renderer getter for read-only rendered-object evidence.
    def observe(route):
        response=route.fetch()
        report.setdefault('loadedSourceSHA256',{})['heart-study-v3/renderer.js']=hashlib.sha256(response.body()).hexdigest()
        check(report['loadedSourceSHA256']['heart-study-v3/renderer.js']==report['localSourceSHA256']['heart-study-v3/renderer.js'],'Loaded renderer matches tested source')
        route.fulfill(response=response,body=response.text()+'\n{const mount=HeartV3Renderer.mount;HeartV3Renderer.mount=(...a)=>window.__outflowRenderer=mount(...a);}')
    page.route('**/heart-study-v3/renderer.js',observe)
    def verify_source(route):
        response=route.fetch()
        report.setdefault('loadedSourceSHA256',{})['heart-study-v3/sourced-anatomy.js']=hashlib.sha256(response.body()).hexdigest()
        check(report['loadedSourceSHA256']['heart-study-v3/sourced-anatomy.js']==report['localSourceSHA256']['heart-study-v3/sourced-anatomy.js'],'Loaded anatomy matches tested source')
        route.fulfill(response=response)
    page.route('**/heart-study-v3/sourced-anatomy.js',verify_source)
    page.goto(URL,wait_until='networkidle')
    check(page.evaluate('()=>[...document.querySelectorAll("audio")].every(a=>a.paused)'),'No audio autoplay on load')
    page.locator('#heartV3Launch').click()
    page.wait_for_function('()=>HeartV3Study.inspect().renderer?.sourceReady')

    def capture(label):
        page.locator('[data-h3-stage]').scroll_into_view_if_needed()
        page.wait_for_timeout(120)
        data=page.evaluate('()=>{const s=HeartV3Study.inspect();return {state:s.state,renderer:s.renderer,camera:s.camera};}')
        filename=label+'.png'
        page.locator('[data-h3-stage]').screenshot(path=str(OUT/filename))
        data.update(label=label,screenshot=filename,sha256=hashlib.sha256((OUT/filename).read_bytes()).hexdigest())
        report['captures'].append(data)
        return data

    page.locator('[data-h3-mode="outflow"]').click()
    for phase in ['passive-filling','atrial-contraction','isovolumetric-contraction','ejection','isovolumetric-relaxation']:
        page.locator('[data-h3-phase="'+phase+'"]').click()
        data=capture('outflow-'+phase)
        check(len(data['renderer']['outflow']['routes'])==2,'Two source-bound routes: '+phase)
        check(all(not p['visible'] for p in data['renderer']['flowPaths']),'No hidden-host legacy arrows: '+phase)
        check(all(r['depthTest'] and r['clippingPlanes']==0 for r in data['renderer']['outflow']['routes']),'Ordinary depth, complete roots: '+phase)
        check(all(r['visible']==(r['open'] and r['flow']>0) for r in data['renderer']['outflow']['routes']),'Valve-correct flow gating: '+phase)

    # Native camera controls rotate only at user request; ordinary occlusion remains.
    if page.locator('[data-h3-inspector]').get_attribute('open') is None:page.locator('[data-h3-inspector] > summary').click()
    page.locator('[data-h3-phase="ejection"]').click()
    for preset in ['front','left','right','back']:
        page.locator('[data-h3-preset="'+preset+'"]').click()
        capture('outflow-rotation-'+preset)
    for width,height,label in [(820,1180,'tablet-portrait'),(1024,768,'tablet-landscape'),(390,844,'phone-portrait')]:
        page.set_viewport_size({'width':width,'height':height})
        page.locator('[data-h3-mode="outflow"]').click()
        data=capture(label+'-ejection')
        check(data['renderer']['sourceReady'] and data['renderer']['activeRendererCount']==1,'One live source renderer: '+label)
    page.set_viewport_size({'width':1440,'height':1100})

    # Actual explicit valve cards/opening controls, preserving inspection affordances.
    for valve in ['aortic','pulmonary','mitral','tricuspid']:
        page.locator('[data-h3-inspect-valve="'+valve+'"]').click()
        if page.locator('[data-h3-inspector]').get_attribute('open') is None:page.locator('[data-h3-inspector] > summary').click()
        page.locator('[data-h3-preset="opening"]').click()
        data=capture('inspection-'+valve)
        check(data['renderer']['inspectionValve']==valve,'Native explicit inspection: '+valve)
        check(data['renderer']['drawCalls']>0,'Inspection draws actual source/rig: '+valve)

    # Walk the real flow trace and isolate both valves and arteries.
    page.locator('[data-h3-mode="outflow"]').click()
    page.locator('[data-h3-action="trace-blood"]').click()
    for step in range(14):
        if step in [5,6,12,13]:
            page.locator('[data-h3-action="flow-isolate"]').click()
            data=capture('isolated-trace-'+str(step))
            if step in [6,13]:
                route=next(r for r in data['renderer']['outflow']['routes'] if r['vesselOnly'])
                check(not route['collarVisible'] and not any(p['visible'] for p in data['renderer']['flowPaths']),'Artery-only trace has bounded source flow: '+str(step))
            page.locator('[data-h3-action="flow-isolate"]').click()
        if step<13:page.locator('[data-h3-action="flow-next"]').click()
    page.locator('[data-h3-action="trace-blood"]').click()

    # Sound remains manual and independent while changing views/time and rotating.
    page.locator('[data-h3-mode="outflow"]').click()
    page.locator('[data-h3-phase="ejection"]').click()
    check(page.evaluate('()=>[...document.querySelectorAll("audio")].every(a=>a.paused)'),'Simulator controls never autoplay audio')
    before=page.evaluate('()=>({state:HeartV3Study.getState(),camera:HeartV3Study.inspect().camera})')
    page.locator('[data-audio-dock-play]').click()
    page.wait_for_function('()=>[...document.querySelectorAll("audio")].some(a=>!a.paused&&a.currentTime>0)')
    after=page.evaluate('()=>({state:HeartV3Study.getState(),camera:HeartV3Study.inspect().camera})')
    check(before==after,'User audio play leaves simulator state and camera unchanged')
    initial=page.evaluate('()=>[...document.querySelectorAll("audio")].find(a=>!a.paused).currentTime')
    page.locator('[data-h3-phase="passive-filling"]').click()
    page.locator('[data-h3-preset="left"]').click()
    page.locator('[data-audio-dock-toggle]').click()
    page.locator('[data-audio-dock-close]').click()
    page.wait_for_timeout(300)
    media=page.evaluate('()=>[...document.querySelectorAll("audio")].filter(a=>!a.paused).map(a=>({time:a.currentTime,src:a.currentSrc}))')
    check(len(media)==1 and media[0]['time']>initial,'Manual phase/camera and dock interactions keep one narration playing')
    page.locator('[data-audio-dock-play]').click()
    check(page.evaluate('()=>[...document.querySelectorAll("audio")].every(a=>a.paused)'),'Manual narration pause works')
    check(not report['errors'],'No browser script errors')
    browser.close()

report['passed']=True
(OUT/'result.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'passed':True,'checks':len(report['checks']),'captures':len(report['captures']),'output':str(OUT)}))
