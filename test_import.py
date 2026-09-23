import importlib, traceback
try:
    app = importlib.import_module('app')
    print('IMPORT_OK')
    for r in sorted(str(rule) for rule in app.app.url_map.iter_rules()):
        print(r)
except Exception:
    traceback.print_exc()
