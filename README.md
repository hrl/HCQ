HCQ
===

华科自习室查询

教务处网站改版了，新版还算好用，所以此项目暂时不会更新了

之后有时间的话也许会改成查电费的（

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
