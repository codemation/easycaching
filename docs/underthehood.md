## Under the Hood
easycaching utilizes the smart caching of [aiopyql](https://github.com/codemation/aiopyql) to provide cache acesss, cache storage, and perhaps most importantly updates and invalidation.

Data access sharing is made possible via proxy methods using [easyrpc](https://github.com/codemation/easyrpc). A cache background task is created & managed by gunicorn which main application workers access via proxies. 

![](images/easycaching-arch.png
)