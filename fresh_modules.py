# fresh_modules.py
# Problemi: në Streamlit Cloud, pas një `git push`, skedari kryesor ekzekutohet i ri, por modulet
# që ishin ngarkuar më parë (p.sh. catalog.py) mbeten në memorie në versionin e VJETËR.
# Kjo shkakton gabime si "AttributeError: module 'catalog' has no attribute ...".
# Zgjidhja: kur ndryshon ndonjë skedar .py i projektit, i heqim modulet e projektit nga memoria,
# që Python t'i lexojë sërish nga disku.
import glob
import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def _project_files() -> list:
    return sorted(glob.glob(os.path.join(BASE_DIR, "*.py")) + glob.glob(os.path.join(BASE_DIR, "views", "*.py")))


def _module_name(path: str) -> str:
    relative = os.path.relpath(path, BASE_DIR)[:-3].replace(os.sep, ".")
    return relative[:-9] if relative.endswith(".__init__") else relative


def reload_if_changed() -> bool:
    """Kthen True nëse modulet u rifreskuan (pra kodi ishte ndryshuar që nga hera e fundit)."""
    files = _project_files()
    stamp = tuple((path, os.path.getmtime(path)) for path in files)
    if getattr(sys, "_kpb_code_stamp", None) == stamp:
        return False
    names = {_module_name(path) for path in files} - {"fresh_modules", "client_app", "app", "streamlit_app"}
    for name in names:
        sys.modules.pop(name, None)
    sys._kpb_code_stamp = stamp
    return True
