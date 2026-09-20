"""Real engine UI, native snapshots and missing-field migration."""
import os
from pathlib import Path
import subprocess
import pytest
from test_general_save_runtime import make_project, SDK

ROOT = Path(__file__).resolve().parents[1]
HARNESS = r'''
init python:
    def qa_monthly_active():
        state = _monthly_json.loads(_fm_monthly.initial(3))
        state['card'] = next(c for c in monthly_catalog() if c['id'] == 'cold_spell')
        state['experienced'] = True
        store.monthly_condition_state = _fm_monthly.encode(state)

label splashscreen:
    $ qa_intro_setup()
    $ monthly_sync()
    $ qa_intro_check(not monthly_state()['card']['effects'], "New game neutral")
    $ current_month = 4
    $ current_day = 12
    $ qa_monthly_active()
    $ qa_intro_check(monthly_skill(workers[0], 'Service', 'restaurant', 'cook') == calculate_skill_with_traits(workers[0], 'Service') + 5, 'Engine contextual skill uses monthly adjustment')
    $ monthly_open()
    call screen qa_intro_gate
    $ qa_intro_present('monthly_conditions')
    $ qa_intro_close()
    call screen qa_intro_gate
    $ qa_intro_capture('monthly-active')
    $ qa_intro_widget('monthly_card', 'monthly_toggle')
    call screen qa_intro_gate
    $ qa_intro_check(monthly_state()['enabled'] and not monthly_state()['requested'], "Pending toggle leaves effects active")
    $ qa_intro_capture('monthly-pending')
    $ qa_intro_save(97)
    $ qa_intro_widget('monthly_card', 'monthly_close')
    $ renpy.session['monthly_expected'] = monthly_condition_state
    $ monthly_condition_state = ''
    $ CanonicalSnapshotFileLoad(FileLoad(97, confirm=False), 97, confirm=False)()
    $ renpy.quit(status=7)

label qa_general_loaded:
    if renpy.session.get('monthly_phase') == 'legacy':
        $ qa_intro_check(monthly_condition_state == '', 'Old snapshot has neutral default')
        $ monthly_sync()
        $ qa_intro_check(not monthly_state()['card']['effects'], 'Legacy current month remains neutral')
        $ qa_intro_save(99)
        $ renpy.quit(status=0)
    $ qa_intro_check(monthly_condition_state == renpy.session['monthly_expected'], 'Monthly state survives native canonical load')
    $ qa_intro_check(renpy.get_screen('monthly_card') is None, 'Load clears saved card control context')
    $ qa_intro_check(not monthly_state()['requested'] and monthly_state()['enabled'], 'Pending preference survives load')
    $ current_day = 28
    $ advance_date()
    $ qa_intro_check(current_month == 5 and not monthly_state()['enabled'], 'Boundary commits disabling')
    $ monthly_open()
    call screen qa_intro_gate
    $ qa_intro_capture('monthly-disabled')
    $ qa_intro_check(renpy.get_screen('screen_intro_popup') is None, 'Tutorial not repeated')
    $ qa_intro_widget('monthly_card', 'monthly_close')
    $ renpy.set_physical_size((960, 540))
    $ persistent.large_font_mode = True
    $ monthly_open()
    call screen qa_intro_gate
    $ qa_intro_capture('monthly-small-window')
    $ qa_intro_widget('monthly_card', 'monthly_close')
    $ persistent.large_font_mode = False
    $ monthly_toggle()
    $ current_day = 28
    $ advance_date()
    $ qa_intro_check(monthly_state()['enabled'], 'Boundary commits enabling')
    # Preserve an active card even when its catalog entry disappears.
    $ qa_intro_check(_fm_monthly.sync(monthly_condition_state, monthly_period(), [], renpy.random.random) == monthly_condition_state, 'Removed catalog card retained')
    # True legacy snapshot fixture: absent optional state in both sidecar and native.
    $ monthly_condition_state = ''
    $ qa_intro_save(98)
    python:
        name = _get_current_slot_name(98)
        snap = _read_snapshot_file(_get_snapshot_file_path(name))
        snap.pop('monthly_condition_state', None)
        for path in (_get_snapshot_file_path(name), _get_backup_file_path(name)):
            with open(path, 'w', encoding='utf-8') as handle:
                json.dump(snap, handle)
    $ renpy.session['monthly_phase'] = 'legacy'
    $ qa_monthly_active()
    $ CanonicalSnapshotFileLoad(FileLoad(98, confirm=False), 98, confirm=False)()
    $ renpy.quit(status=8)
'''


def test_monthly_ui_and_canonical_save_load(tmp_path):
    if not SDK.is_file():
        if os.environ.get('RENPY_RUNTIME_REQUIRED') == '1':
            pytest.fail('RenPy required')
        pytest.skip('RenPy unavailable')
    project = tmp_path / 'project'
    make_project(project)
    helpers = (ROOT/'tools/qa_location_tutorials.rpy').read_text(encoding='utf-8').split('\nlabel splashscreen:',1)[0]
    (project/'game/qa_general_audit.rpy').write_text(helpers+HARNESS,encoding='utf-8')
    env=os.environ.copy()
    env.update(APPDATA=str(tmp_path/'env/appdata'),LOCALAPPDATA=str(tmp_path/'env/localappdata'),
               RENPY_SIMPLE_EXCEPTIONS='1',RENPY_RENDERER='gl2')
    startup=None
    if os.name=='nt':
        startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=subprocess.SW_HIDE
    result=subprocess.run([str(SDK),str(project),'run','--savedir',str(tmp_path/'saves')],env=env,
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,startupinfo=startup,timeout=90)
    output=result.stdout.decode('utf-8','replace')
    (tmp_path/'engine-output.txt').write_text(output,encoding='utf-8')
    assert result.returncode==0,output[-6000:]
    report=(tmp_path/'saves/location-qa.txt').read_text(encoding='utf-8')
    assert 'FAIL:' not in report and 'Native save committed: 99' in report
