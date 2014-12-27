HCQ
===

华科自习室查询

之前查询自习室的网站已停止维护，于是自己爬了爬教务处网站写了这么一个东西

只是自己用的话，只需要demo.py

安装依赖
-------
### 本地使用
#### Debian / Ubuntu:
    # apt-get install python3 python3-pip libxml2-dev libxslt1-dev zlib1g-dev
    # pip3 install pyquery python-dateutil lunardate

### 服务端
#### Debian / Ubuntu:
    # apt-get install python3 python3-pip libxml2-dev libxslt1-dev zlib1g-dev redis
    # pip3 install pyquery python-dateutil lunardate redis tornado

使用
-------
### 本地使用
    python3 ./demo.py

### 服务端
#### 修改配置文件
    mv ./settings.py.sample ./settings.py
并根据情况修改相应设置
#### 开启服务端
    python3 ./main.py
#### 使用
    http://localhost:9000/

协议
-------
GNU GPL v2.0
