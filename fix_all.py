import os
import glob
import re

files = glob.glob('tests/api/test_*.py')
for f in files:
    with open(f, 'r') as fp:
        content = fp.read()
    
    # 1. Replace the parameterized ones
    content = content.replace(
        "SELECT set_config('app.current_user_id', :uid, true)",
        "SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"
    )
    content = content.replace(
        "SELECT set_config('app.current_user_id', '', true)",
        "SELECT set_config('civix.current_user_id', '', true), set_config('app.current_user_id', '', true)"
    )
    
    # 2. Replace the f-string/format ones
    # Match: set_config('app.current_user_id', '{...}', true)
    # Match: set_config('app.current_user_id', 'some-uuid', true)
    content = re.sub(
        r"set_config\('app\.current_user_id',\s*'([^']+)',\s*true\)",
        r"set_config('civix.current_user_id', '\1', true), set_config('app.current_user_id', '\1', true)",
        content
    )

    with open(f, 'w') as fp:
        fp.write(content)
