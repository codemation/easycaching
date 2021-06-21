from fastapi import FastAPI
from easycaching.proxy import db_proxy_setup

server = FastAPI()
db_proxy_setup(server)