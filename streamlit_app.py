# streamlit_app.py
# Pika hyrëse për Streamlit Cloud. Më parë ky skedar ishte një kopje e plotë
# e client_app.py (110 KB kod i dyfishtë). Tani thjesht ekzekuton client_app.py,
# kështu që çdo ndryshim bëhet vetëm në një vend.
import os
import runpy

runpy.run_path(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "client_app.py"),
    run_name="__main__",
)
