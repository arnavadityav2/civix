import os

files = ['tests/api/test_leads.py', 'tests/api/test_search.py', 'tests/api/test_rls.py']
for f in files:
    if os.path.exists(f):
        with open(f, 'r') as fp:
            content = fp.read()
        
        # Replace the manual set_config strings
        content = content.replace(
            "SELECT set_config('app.current_user_id', :uid, true)",
            "SELECT set_config('civix.current_user_id', :uid, true), set_config('app.current_user_id', :uid, true)"
        )
        content = content.replace(
            "SELECT set_config('app.current_user_id', '', true)",
            "SELECT set_config('civix.current_user_id', '', true), set_config('app.current_user_id', '', true)"
        )
        
        with open(f, 'w') as fp:
            fp.write(content)
