'''

cd info_segugio

poetry install

eval $(poetry env activate)

chainlit run src/info_segugio/__init__.py -w

poetry run chainlit run src/info_segugio/__init__.py -w

'''