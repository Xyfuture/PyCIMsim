# 设计思路

## 整体模拟思路

## 组合电路模拟思路
组合电路中首先要求不能有回环,不然会循环调用

本质上模拟就是响应数据的改变,我们设计了读取和写入端口,读取端口需要绑定一个回调函数,表示当新的数据变化后应该如何进行处理.如此每当我们通过写端口将数据更新后,首先插入一个事件,更新端口中的数据,然后在插入一个事件,调用读端口绑定的回调函数,如此就完成一个端口数据更新

在组合电路中,其实是按boolean运算的逻辑来的,只有当输入数据发生改变的时候,输出数据才会发生改变,因此我们没必要关注中间状态,只需要关注输入的改变即可

一个端口输出数据只要输入不改变,就永远保持不改变,虽然这是比较符合逻辑的,但是正常都是配合时序逻辑来的,因此理论上每周期其实都要发生改变,这样会导致模拟器写起来复杂,同时模拟速度慢,因此我们添加了一个偷懒的设计,我们在读端口上设置了一个时间检查功能,如果写与读发生在同一个周期,将新数据返回,如果两个不是在同一个周期那么就返回空,类似invalid的效果

更具体来说,部分写端口的数据只有在寄存器特定值(组合逻辑前面是寄存器)下是有意义的,其他情况下都是默认的,如果是默认的,那么我们这周期就不写了,那么读端口在同一个周期读到的就是空,表示默认情况,也就是无效的情况,可以方便代码的编写



## 时序电路模拟思路
时序逻辑设计了两类,一类是每周期触发,带有一个Enable端口,另一个是,手动更新数据,本周期写,下一个周期才能记录数据,RegNext




## 流水级设计思路

建议开一个大的process函数,里面处理所有与输入输出端口相关的函数,然后把所有读端口的回调都帮到他身上,然后读取到数据的细节处理可以交给其他的函数实现

一定要保证组合逻辑是无状态的,只与输入相关,允许输入为空,但是不要保存什么中间变量,最后在框架中,经过多次的调用,最后一定会输出正确的结果到写端口上
