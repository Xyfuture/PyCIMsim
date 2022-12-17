class PayloadBase:
    def __init__(self, **kwargs):
        for k in self.__class__.__annotations__:
            if k in kwargs:
                self.__setattr__(k, kwargs[k])
            else:
                self.__setattr__(k, getattr(self.__class__, k))

    def __getitem__(self, item):
        # 历史因素,可以无缝衔接功能
        return getattr(self, item)

    def __setitem__(self, key, value):
        setattr(self,key,value)

    @classmethod
    def load_dict(cls, data):
        return cls(**data)


    # 没有进行严格的check,但是有类型注解了,还算够用吧
