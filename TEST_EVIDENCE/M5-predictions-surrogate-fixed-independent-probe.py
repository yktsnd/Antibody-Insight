"""Bounded synthetic HTTP probe, never edits application or stored project."""

import contextlib
import copy
import hashlib
import http.client
import io
import json
import pathlib
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from http.cookiejar import CookieJar

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from workspace_app.fixtures import STAMP, example_bundle
from workspace_app.predictions import CANONICAL
from workspace_app.server import make_server


def main():
    evidence = ROOT / 'TEST_EVIDENCE'
    traces = io.StringIO()
    results = []
    with tempfile.TemporaryDirectory(prefix='antibody-independent-surrogate-') as temporary:
        server = make_server(pathlib.Path(temporary) / 'probe.sqlite3', 0)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        with contextlib.redirect_stderr(traces):
            worker.start()
            try:
                browser = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))
                browser.open(server.origin + '/').close()
                with browser.open(server.origin + '/api/bootstrap') as response:
                    boot = json.load(response)
                bundle = example_bundle(1)
                server.store.import_bundle(bundle)
                subject = next(e['id'] for e in bundle['entities'] if e['type'] == 'molecule')
                good_row = {'kind': 'computed', 'subject_ref': subject, 'metric': 'SYNTHETIC scalar; no model run',
                            'value': 0.5, 'unit': '1', 'source': {'name': 'SYNTHETIC probe', 'version': None},
                            'timestamp': STAMP, 'conditions': None}
                base = {'schema_version': CANONICAL, 'records': [good_row]}
                high, low = chr(0xd800), chr(0xdc00)
                cases = []
                for label, surrogate in [('high', high), ('low', low)]:
                    cases.append(('unknown_root_' + label, json.dumps({**base, surrogate: 1}, ensure_ascii=True)))
                    encoded_key = json.dumps(surrogate, ensure_ascii=True)
                    cases.append(('duplicate_root_' + label,
                                  json.dumps(base)[:-1] + ',' + encoded_key + ':1,' + encoded_key + ':2}'))
                for field in ['subject_ref', 'metric', 'description']:
                    row = {**good_row, field: high}
                    cases.append(('known_row_' + field, json.dumps({**base, 'records': [row]}, ensure_ascii=True)))
                for label, context in [('key', {high: 'value'}), ('value', {'key': high})]:
                    row = {**good_row, 'conditions': context}
                    cases.append(('known_row_context_' + label, json.dumps({**base, 'records': [row]}, ensure_ascii=True)))
                paired = {**good_row, 'metric': 'valid scalar ' + chr(0x1f600)}
                cases.append(('valid_surrogate_pair_control', json.dumps({**base, 'records': [paired]}, ensure_ascii=True)))
                headers = {'Content-Type': 'application/json', 'Origin': server.origin, 'X-CSRF-Token': boot['csrf']}
                for name, raw in cases:
                    request_data = {'project_id': bundle['project']['id'], 'text': raw, 'filename': 'SYNTHETIC-escaped-source.json',
                                    'file_format': CANONICAL, 'bindings': {}, 'options': {}, 'bindings_text_sha256': None}
                    encoded = json.dumps(request_data, ensure_ascii=True).encode('ascii')
                    result = {'case': name, 'request_is_ascii_valid_utf8': True,
                              'expected_status': 200 if name.endswith('_control') else 422}
                    request = urllib.request.Request(server.origin + '/api/prediction-preview', data=encoded, headers=headers)
                    try:
                        with browser.open(request, timeout=5) as response:
                            result['status'] = response.status
                            result['payload'] = json.load(response)
                    except urllib.error.HTTPError as exc:
                        result['status'] = exc.code
                        result['payload'] = json.load(exc)
                    except (http.client.RemoteDisconnected, urllib.error.URLError, ConnectionError) as exc:
                        result['status'] = 'connection_closed'
                        result['exception_type'] = type(exc).__name__
                        result['exception_message'] = str(exc)
                    result['database_unchanged'] = server.store.bundle(bundle['project']['id']) == bundle
                    result['pass'] = result['status'] == result['expected_status'] and result['database_unchanged']
                    # Keep the valid preview payload out of this bounded result file.
                    if name.endswith('_control'):
                        result['valid_rows'] = result.pop('payload')['report']['valid_rows']
                    results.append(result)
            finally:
                server.shutdown()
                worker.join(timeout=5)
                server.server_close()
    data = {'reviewer': '/root/prediction_design_review', 'synthetic_only': True,
            'files': {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
                      for p in ['workspace_app/server.py', 'workspace_app/predictions.py', 'workspace_app/adapters.py']},
            'results': results, 'all_pass': all(r['pass'] for r in results)}
    (evidence / 'M5-predictions-surrogate-fixed-independent-results.json').write_text(json.dumps(data, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')
    (evidence / 'M5-predictions-surrogate-fixed-independent-server-errors.log').write_bytes(traces.getvalue().encode('utf-8', errors='backslashreplace'))
    for result in results:
        print(result['case'], result['status'], 'unchanged=' + str(result['database_unchanged']))
    print('Overall expected-rejection result:', data['all_pass'])


if __name__ == '__main__':
    main()
