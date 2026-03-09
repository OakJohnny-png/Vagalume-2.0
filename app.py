File "/mount/src/vagalume-2.0/app.py", line 353, in <module>
    # Gerência vê a Navbar completa com todas as abas
File "/mount/src/vagalume-2.0/app.py", line 172, in render_cidadao
    "obs_tecnico": "",
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 532, in wrapped_func
    result = non_optional_func(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/state/session_state_proxy.py", line 136, in __setattr__
    self[key] = value
    ~~~~^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/metrics_util.py", line 532, in wrapped_func
    result = non_optional_func(*args, **kwargs)
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/state/session_state_proxy.py", line 114, in __setitem__
    get_session_state()[key] = value
    ~~~~~~~~~~~~~~~~~~~^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/state/safe_session_state.py", line 109, in __setitem__
    self._state[key] = value
    ~~~~~~~~~~~^^^^^
File "/home/adminuser/venv/lib/python3.14/site-packages/streamlit/runtime/state/session_state.py", line 591, in __setitem__
    raise StreamlitAPIException(
    ...<2 lines>...
    )