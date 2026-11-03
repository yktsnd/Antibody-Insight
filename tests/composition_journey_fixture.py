"""Synthetic paired/single-chain source declarations for the complete J05 UI."""

from workspace_app.fixtures import composition_bundle


def composition_journey_bundle():
    bundle=composition_bundle()
    bundle['project']['title']='[SYNTHETIC FIXTURE] J05 explicit composition and source usage'
    units=[e for e in bundle['entities'] if e['type']=='binding_unit']
    units[0]['name']='Synthetic paired source A'
    units[0]['topology']='paired'
    units[0]['chains'].append({'id':'partner-fragment','role':'declared paired partner fragment','sequence':'GHIK','origin':None})
    units[0]['source']={'name':'SYNTHETIC J05 paired-source declaration; no pairing experiment','version':'1'}
    units[1]['name']='Synthetic single-chain source B'
    return bundle
