#### 数字货币对冲套利

利用各平台之间同一数字货币（例：eth）的差价，进行对冲套利，俗称搬砖。

#### 结构

* `carrybrick`: 主要的套利策略目录，也包含了一些日志和保存交易记录。
  * `hedging.py`: 主要的的搬砖过程，里面也可以对一些参数的调整。
* `client`: 各个平台的行情及交易api的封装。
* `matrix`: 获取指定平台之间的差价，本意是用来获取价差最高的两个平台，获取最大利润，取名矩阵。
* `tests`: 一些测试接口的脚本

#### 运行

* `pip/pip3 install -r requirements.txt`
* 在`client`目录里各个平台的api key 填上
* `python3 app.py`

> 默认搬运`ltc`, 在`app.py`里将`ltc`改为`eth`即可搬运`eth`。其他币种未测试。
