#!/bin/bash
# Arranca los dos procesos que conviven durante la migración de
# Streamlit a la API nueva (ver plan de migración): Streamlit en 8501
# (la app de siempre, sin tocar) y FastAPI+React en 8000. Si cualquiera
# de los dos muere, el contenedor entero se para (así Docker lo
# reinicia según la política de restart, en vez de quedarse a medias).
#
# Al terminar la migración (último paso del plan), este script y el
# segundo proceso desaparecen — solo main.py (ya apuntando a la API).
set -e

python main.py &
STREAMLIT_PID=$!

python main_api.py &
API_PID=$!

trap 'kill $STREAMLIT_PID $API_PID 2>/dev/null' TERM INT

wait -n "$STREAMLIT_PID" "$API_PID"
EXIT_CODE=$?
kill "$STREAMLIT_PID" "$API_PID" 2>/dev/null
exit $EXIT_CODE
