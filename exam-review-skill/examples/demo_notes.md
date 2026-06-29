# Python 程序设计 - 期末复习笔记

## 第一章：基础语法

### 1.1 变量与数据类型

Python 是动态类型语言，变量不需要声明类型。

**重点**：Python 中一切皆对象，变量是对象的引用。

常见数据类型：
- int（整数）
- float（浮点数） 
- str（字符串）
- bool（布尔值）
- list（列表）
- tuple（元组）
- dict（字典）
- set（集合）

**注意**：list 和 dict 是可变类型，tuple 和 str 是不可变类型。

### 1.2 运算符

算术运算符：`+ - * / // % **`

比较运算符：`== != > < >= <=`

逻辑运算符：`and or not`

**易混淆**：`==`（值相等）vs `is`（同一对象）

### 1.3 控制流

**条件语句：**
if-elif-else 结构。Python 使用缩进表示代码块。

**循环语句：**
- for 循环：遍历可迭代对象
- while 循环：条件为真时执行

**重点**：break 终止循环，continue 跳过本次迭代。

## 第二章：函数与模块

### 2.1 函数定义

```
def function_name(param1, param2=default):
    """文档字符串"""
    return result
```

参数类型：
- 位置参数
- 默认参数
- 关键字参数
- 可变参数 *args
- 关键字可变参数 **kwargs

**易错点**：默认参数只在函数定义时计算一次，可变默认参数（如 list）会导致意外行为。

### 2.2 作用域

LEGB 规则：Local → Enclosing → Global → Built-in

**注意**：在函数内修改全局变量需要使用 global 关键字。

### 2.3 模块与包

- import module
- from module import name
- import module as alias

**重点**：`if __name__ == "__main__"` 用于判断模块是被导入还是直接运行。

## 第三章：面向对象编程

### 3.1 类与对象

```
class MyClass(ParentClass):
    class_var = 0  # 类变量
    
    def __init__(self, name):
        self.name = name  # 实例变量
    
    def method(self):
        pass
```

**核心概念**：
- 封装：将数据和方法绑定在一起
- 继承：子类继承父类的属性和方法
- 多态：不同类可以实现同名方法

### 3.2 魔术方法

- `__init__`：构造方法
- `__str__`：字符串表示
- `__repr__`：官方字符串表示
- `__len__`：长度
- `__eq__`：相等比较

**易混淆**：`__str__`（给用户看）vs `__repr__`（给开发者看）

### 3.3 装饰器

```
@staticmethod
def static_method():
    pass

@classmethod
def class_method(cls):
    pass

@property
def name(self):
    return self._name
```

**注意**：@property 将方法变为属性访问，但不应包含复杂计算。

## 常见错误与陷阱

**误区1**：修改列表时遍历列表 —— 应遍历副本
**误区2**：可变类型作为默认参数
**误区3**：在 except 块中不指定异常类型
**误区4**：混淆浅拷贝与深拷贝

## 考试重点总结

**必考题型**：
1. 列表/字典推导式
2. 装饰器实现
3. 类的继承与多态
4. 文件操作（with 语句）
5. 异常处理（try-except-finally）
