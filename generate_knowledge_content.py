"""
批量生成知识点内容文件
根据course_data.json中的知识点配置，生成完整的知识点内容JSON文件
"""

import json
import os
import time


def load_course_data(course_name):
    """加载课程数据"""
    with open(f"{course_name}/course_data.json", 'r', encoding='utf-8') as f:
        return json.load(f)


def generate_knowledge_point_content(kp_name, chapter_context="", section_context="", course_code="Python"):
    """根据知识点名称生成完整的内容"""

    # Python课程知识点内容映射
    python_content_map = {
        # ============ Python 第1章 程序设计基础知识 ============
        "Python简介与特点": {
            "content": "Python是一种高级、解释型、面向对象的编程语言，由Guido van Rossum于1991年创建。其设计哲学强调代码的可读性和简洁性，采用缩进表示代码块结构。Python拥有丰富的标准库和第三方生态，广泛应用于Web开发、数据科学、人工智能、自动化运维、网络爬虫、游戏开发等领域。Python的核心理念是'There should be one—and preferably only one—obvious way to do it'。",
            "summary": "Python是一种高级解释型面向对象语言，以简洁易读著称，应用领域广泛",
            "code_example": "# Python的第一个程序\nprint(\"Hello, World!\")\n\n# 简洁的代码风格\nname = \"Python\"\nversion = 3.11\nprint(f\"学习{name} {version}\")",
            "code_language": "python",
            "code_explanation": "print函数用于输出信息，f-string是Python3.6+引入的字符串格式化方式，简洁直观。",
            "tips": ["适合作为编程入门语言", "应用领域广泛就业前景好", "语法简洁但功能强大", "社区活跃资源丰富"],
            "common_mistakes": ["把Python当成简单的脚本语言忽视其面向对象特性", "混淆解释型语言和编译型语言的区别", "忽视Python的哲学理念"]
        },
        "Python编程环境设置": {
            "content": "Python环境配置包括安装Python解释器、使用pip包管理工具、创建虚拟环境等步骤。Python支持Windows、Linux、macOS等主流操作系统。pip是Python官方的包管理工具，用于安装、升级、卸载第三方库。虚拟环境可以隔离不同项目的依赖，避免版本冲突。国内常用镜像源包括清华大学、阿里云等，可显著提升下载速度。",
            "summary": "Python环境配置包括解释器、pip包管理、虚拟环境",
            "code_example": "# 检查Python版本\npython --version\npip --version\n\n# 安装第三方库\npip install requests\npip install numpy pandas\n\n# 配置国内镜像\npip install requests -i https://pypi.tuna.tsinghua.edu.cn/simple\n\n# 创建虚拟环境\npython -m venv myenv\n\n# 激活虚拟环境(Windows)\nmyenv\\Scripts\\activate",
            "code_language": "bash",
            "code_explanation": "python --version验证安装，pip install安装库，venv模块创建隔离的Python环境避免依赖冲突。",
            "tips": ["安装时勾选Add Python to PATH", "学会使用pip管理第三方库", "项目开发建议使用虚拟环境", "配置国内镜像加速下载"],
            "common_mistakes": ["安装时忘记添加环境变量", "pip安装源速度慢未配置国内镜像", "不同项目混用同一环境导致依赖冲突", "忽视虚拟环境的作用"]
        },
        "原生环境使用": {
            "content": "Python原生开发环境包括命令行交互模式(REPL)和脚本文件执行两种方式。交互模式适合测试代码片段和调试，脚本文件适合编写完整的程序。IDLE是Python自带的集成开发环境，提供基本的代码编辑和运行功能。Python解释器逐行读取代码并立即执行，这种模式称为REPL(Read-Eval-Print Loop)。",
            "summary": "Python原生环境包括交互模式和脚本文件执行方式",
            "code_example": "# 交互模式示例\n>>> print(\"Hello\")\nHello\n>>> 2 + 3\n5\n>>> name = \"Python\"\n>>> len(name)\n6\n>>> exit()\n\n# 脚本文件 hello.py\n# -*- coding: utf-8 -*-\nprint(\"Hello, World!\")\n\n# 运行脚本\npython hello.py",
            "code_language": "python",
            "code_explanation": "交互模式下可直接输入代码执行，exit()或quit()退出。脚本文件首行指定UTF-8编码以支持中文。",
            "tips": ["交互模式适合测试简单代码和调试", "脚本文件保存时注意编码为UTF-8", "IDLE适合初学者入门使用", "学会使用help()查看函数帮助"],
            "common_mistakes": ["在交互模式下写复杂程序难以调试", "脚本编码问题导致中文乱码", "忘记文件后缀.py", "混淆交互模式和脚本模式的区别"]
        },
        "第三方IDE开发环境": {
            "content": "常用的Python IDE包括PyCharm、VS Code、Jupyter Notebook等。PyCharm是JetBrains公司开发的专业Python IDE，具有强大的代码补全、重构、调试功能，适合大型项目开发。VS Code是轻量级编辑器，通过Python插件支持开发，配置灵活。Jupyter Notebook是交互式编程环境，支持代码、文档、可视化混合展示，广泛用于数据科学和机器学习领域。",
            "summary": "常用Python IDE有PyCharm、VS Code、Jupyter Notebook",
            "code_example": "# PyCharm特点\n# - 强大的代码补全和重构功能\n# - 内置调试器和版本控制\n# - 支持远程开发和数据库工具\n# - 适合大型项目和企业开发\n\n# VS Code + Python插件\n# - 轻量级，启动快速\n# - 丰富的插件市场\n# - 可配置调试\n\n# Jupyter Notebook\n# - 交互式编程环境\n# - 代码单元格执行\n# - 支持Markdown文档\n# - 适合数据分析和可视化",
            "code_language": "python",
            "code_explanation": "不同IDE有不同的适用场景，PyCharm适合大型项目，Jupyter适合数据分析，VS Code灵活可配置。",
            "tips": ["大型项目开发推荐PyCharm专业版", "数据分析推荐Jupyter Notebook", "轻量级开发可选VS Code", "学会配置IDE的Python解释器"],
            "common_mistakes": ["IDE选择不当影响开发效率", "不熟悉IDE快捷键操作", "不会配置IDE的Python解释器", "忽视IDE的调试功能"]
        },
        "Python基本语法": {
            "content": "Python基本语法包括变量与赋值、数据类型、运算符、控制结构、函数定义等。Python使用缩进表示代码块，不使用大括号，这是Python与其他语言的重要区别。变量无需声明类型，解释器会根据赋值自动推断类型。注释使用#开头，多行注释使用三引号。语句结尾不需分号（也可加分号但不推荐）。",
            "summary": "Python基本语法包括变量、数据类型、运算符、控制结构、函数",
            "code_example": "# 变量与数据类型\nname = \"张三\"      # 字符串\nage = 20           # 整数\nheight = 1.75      # 浮点数\nis_student = True  # 布尔值\n\n# 基本运算符\nresult = 10 / 3    # 浮点除法: 3.333...\nresult = 10 // 3   # 整数除法: 3\nresult = 10 % 3    # 取余: 1\nresult = 2 ** 10   # 幂运算: 1024\n\n# 条件语句\nif age >= 18:\n    print(\"成年人\")\nelif age >= 6:\n    print(\"未成年人\")\nelse:\n    print(\"儿童\")",
            "code_language": "python",
            "code_explanation": "Python用缩进表示代码块结构，if/for/while/def等语句后需加冒号。range(n)生成0到n-1的序列。",
            "tips": ["Python用缩进表示代码块", "变量无需声明类型", "if/for/def后必须加冒号", "/是浮点除，//是整数除"],
            "common_mistakes": ["缩进不一致导致IndentationError", "忘记在语句后加冒号", "混用中英文符号", "整数除法忘记用//"]
        },
        "类与对象的基本概念": {
            "content": "面向对象编程(OOP)是一种程序设计思想，将现实世界的事物抽象为程序中的对象。类是对一类事物的抽象描述，是创建对象的模板；对象是类的实例，具有属性和方法。Python中一切皆对象，包括数值、字符串、函数等。定义类使用class关键字，__init__方法用于初始化对象，self参数指向对象本身。封装、继承、多态是面向对象的三大特性。",
            "summary": "类是对象的模板，对象是类的实例，Python中一切皆对象",
            "code_example": "# 定义类\nclass Student:\n    school = \"清华大学\"  # 类属性\n    \n    def __init__(self, name, age):\n        self.name = name    # 实例属性\n        self.age = age\n    \n    def show_info(self):    # 实例方法\n        print(f\"姓名：{self.name}，年龄：{self.age}\")",
            "code_language": "python",
            "code_explanation": "类属性所有对象共享，实例属性每个对象独立。self表示对象本身，类方法用@classmethod装饰器。",
            "tips": ["类是模板，对象是实例", "类的方法第一个参数是self", "Python中所有数据都是对象", "类属性vs实例属性要分清"],
            "common_mistakes": ["忘记在方法中写self参数", "混淆类属性和实例属性", "不理解__init__构造方法的作用", "忘记类名后加冒号"]
        },
        "系统定义类的简单使用": {
            "content": "Python内置大量系统类可直接使用。字符串str类提供split、upper、lower、replace、strip等方法。列表list类提供append、remove、insert、sort、reverse等方法。字典dict类提供keys、values、items、get、update等方法。文件操作使用open函数返回文件对象。熟练使用内置类可以高效处理日常编程任务。",
            "summary": "Python内置类如str、list、dict、file等可直接使用",
            "code_example": "# 字符串操作\ns = \"  Hello, World!  \"\nprint(s.strip())          # 去首尾空格\nprint(s.upper())           # HELLO, WORLD!\nprint(s.replace(\"World\", \"Python\"))\n\n# 列表操作\nlst = [3, 1, 4, 1, 5, 9, 2, 6]\nlst.append(9)\nlst.sort()\n\n# 字典操作\nd = {\"name\": \"张三\", \"age\": 20}\nprint(d.get(\"name\"))",
            "code_language": "python",
            "code_explanation": "with语句自动关闭文件，encoding参数指定UTF-8编码避免中文乱码。字典的get方法安全获取值。",
            "tips": ["善用dir()查看对象可用方法", "官方文档是最好的学习资源", "字符串是不可变对象", "列表的sort()直接修改原列表"],
            "common_mistakes": ["不查阅文档不知道有哪些方法可用", "方法参数传递错误", "修改字符串未接收返回值", "忘记文件操作后关闭文件"]
        },
        # ============ Python 第1章 数据类型及操作 ============
        "变量与常量": {
            "content": "变量是存储数据的容器，在程序运行过程中其值可以发生变化。Python是动态类型语言，变量无需预先声明类型，解释器会根据赋值自动推断。常量是固定不变的值，Python没有真正的常量，通常用全大写变量名约定为常量。变量命名必须以字母或下划线开头，后续字符可以是字母、数字或下划线，且不能使用Python关键字。",
            "summary": "变量是存储数据的容器，Python动态类型无需声明，常量约定用全大写",
            "code_example": "# 变量赋值\nname = \"张三\"\nage = 20\n\n# 多个变量同时赋值\na = b = c = 0\nx, y = 1, 2\n\n# 交换变量\nx, y = y, x\n\n# 常量约定\nMAX_SIZE = 100\n\nprint(type(name))",
            "code_language": "python",
            "code_explanation": "Python使用=赋值，type()函数查看变量类型。元组解包可以方便地交换两个变量的值。",
            "tips": ["变量名要有意义", "遵循命名规范", "可以使用下划线分隔单词如user_name"],
            "common_mistakes": ["使用Python关键字作为变量名", "变量名以数字开头", "混淆变量赋值与数学等号"]
        },
        "数字类型及操作": {
            "content": "Python数字类型包括整数(int)、浮点数(float)、复数(complex)和布尔(bool)。整数没有大小限制，浮点数采用IEEE 754双精度标准。Python支持加、减、乘、除、整除、取余、幂运算等算术运算符，以及比较运算符和逻辑运算符。整数和浮点数混合运算时，整数会自动转换为浮点数。",
            "summary": "Python数字类型包括int、float、complex、bool，支持丰富运算符",
            "code_example": "a = 10\nb = 3\nprint(a + b)     # 13\nprint(a / b)     # 3.333...\nprint(a // b)    # 3  整数除法\nprint(a % b)     # 1  取余\nprint(a ** b)    # 1000 幂运算",
            "code_language": "python",
            "code_explanation": "浮点数除法用/，整数除法用//。布尔值本质是整数，True=1，False=0。round()是四舍五入。",
            "tips": ["浮点数比较用误差范围", "大整数运算无溢出", "bool是int的子类"],
            "common_mistakes": ["浮点数直接比较直接用==", "整数除法忘记用//", "float和int混合运算结果类型"]
        },
        "字符串及其类库": {
            "content": "字符串是Python中最常用的数据类型之一，用单引号、双引号或三引号表示。字符串是不可变序列，支持索引和切片操作。str类提供了大量方法用于字符串处理，包括大小写转换、查找替换、分割合并、格式化和编码转换等。Python3默认字符串编码为Unicode。",
            "summary": "字符串是不可变序列，str类提供丰富方法进行大小写、查找、替换、分割等操作",
            "code_example": "s = \"Hello, World!\"\nprint(s[0])           # H\nprint(s[0:5])         # Hello\nprint(s.upper())      # HELLO, WORLD!\nprint(s.replace(\"World\", \"Python\"))\nprint(s.split(\",\"))   # ['Hello', ' World!']\n\n# f-string格式化\nname = \"张三\"\nage = 20\nprint(f\"姓名：{name}，年龄：{age}\")",
            "code_language": "python",
            "code_explanation": "字符串是不可变的，所有修改操作都返回新字符串。索引从0开始，-1表示最后一个字符。f-string是Python3.6+推荐的格式化方式。",
            "tips": ["字符串是不可变对象", "善用切片操作", "f-string简洁高效"],
            "common_mistakes": ["修改字符串某字符", "忘记切片范围左闭右开", "编码问题导致乱码"]
        },
        "数据类型使用技巧": {
            "content": "Python数据类型的合理选择和转换是编写高效代码的基础。整数适用于计数和精确计算，浮点数适用于科学计算。要注意避免类型转换带来的精度损失和意外行为。序列类型之间可以相互转换。datetime模块提供了日期和时间处理功能。",
            "summary": "数据类型选择和转换技巧，避免精度损失和意外行为",
            "code_example": "# 类型判断\nx = 10\nprint(isinstance(x, int))\n\n# 类型转换\nnum_str = \"123\"\nnum = int(num_str)\n\n# decimal解决浮点精度\nfrom decimal import Decimal\nresult = Decimal('0.1') + Decimal('0.2')\nprint(result)",
            "code_language": "python",
            "code_explanation": "isinstance()比type()更推荐用于类型检查。decimal模块解决浮点数精度问题。set()可以去重但会改变顺序。",
            "tips": ["金额计算用decimal", "isinstance()优于type()", "合理选择数据类型提高效率"],
            "common_mistakes": ["浮点数直接比较相等", "int()转换非数字字符串报错", "忽视类型转换的副作用"]
        },
        "类库的基本概念": {
            "content": "Python类库分为标准库和第三方库。标准库是Python安装时自带的库，包括os、sys、datetime、json、re等常用模块。第三方库需要通过pip安装，如requests、numpy、pandas等。import语句用于导入模块，from...import用于从模块导入特定成员。合理使用类库可以大大提高开发效率。",
            "summary": "Python类库分标准库和第三方库，import语句导入使用",
            "code_example": "# 导入整个模块\nimport os\nprint(os.getcwd())\n\n# 导入特定成员\nfrom datetime import datetime, timedelta\n\n# 给模块起别名\nimport numpy as np\nimport pandas as pd",
            "code_language": "python",
            "code_explanation": "import后用module.function()调用函数。as给模块起别名方便书写。dir()列出模块所有成员。",
            "tips": ["养成阅读文档的习惯", "善用dir()探索模块", "优先使用标准库"],
            "common_mistakes": ["导入不存在的方法", "模块名拼写错误", "忘记安装第三方库"]
        },
        "类库的使用方法": {
            "content": "使用类库前需要先了解其功能和使用方式。查看文档是学习的最佳途径。常用技巧包括：导入时起别名方便使用、使用help()查看函数帮助、使用dir()列出模块成员。第三方库通常有官方文档和社区支持。",
            "summary": "类库使用包括导入、查看文档、调用方法，help()和dir()是常用辅助工具",
            "code_example": "# 使用help查看帮助\nhelp(print)\n\n# 探索模块\nimport math\nprint([x for x in dir(math) if not x.startswith('_')])\n\n# 常用类库使用\nimport os\nos.mkdir('test_dir')\n\nimport json\ndata = {'name': '张三'}\njson_str = json.dumps(data)",
            "code_language": "python",
            "code_explanation": "help()是交互式学习的好工具。os.path.join()是跨平台路径拼接的正确方式。json.dumps()和json.loads()用于数据序列化。",
            "tips": ["官方文档是最好的教程", "学会查看docstring", "关注库的版本兼容性"],
            "common_mistakes": ["不看文档瞎试", "版本不兼容问题", "路径拼接用字符串拼接而非os.path.join"]
        },
        # ============ Python 第2章 控制结构 ============
        "顺序结构": {
            "content": "顺序结构是最基本的程序结构，按照代码书写顺序从上到下依次执行。每一条语句执行完毕后，自动执行下一条语句。在顺序结构中，不需要额外的控制语句，程序的执行流程就是语句的书写顺序。",
            "summary": "顺序结构按书写顺序从上到下依次执行",
            "code_example": "# 顺序结构示例\na = 10\nb = 20\nc = a + b\nprint(f\"{a} + {b} = {c}\")\n\n# 更多示例\nname = \"Python\"\nprint(\"学习\")\nprint(name)\nmessage = \"Hello\"\nmessage = message + \" World\"\nprint(message)",
            "code_language": "python",
            "code_explanation": "顺序结构中语句按先后顺序执行，前一条语句的执行结果会影响后续语句。",
            "tips": ["顺序结构是最简单的结构", "注重语句执行的逻辑顺序"],
            "common_mistakes": ["误以为后面的语句会影响前面", "忽视语句执行顺序导致的错误"]
        },
        "条件分支控制结构": {
            "content": "条件分支结构根据条件的真假选择执行不同的代码路径。Python使用if、elif、else关键字实现条件分支。条件表达式会产生布尔值True或False。每个分支后跟冒号，代码块通过缩进来表示。elif是else if的缩写，可以有多个。",
            "summary": "条件分支用if-elif-else实现，根据条件真假选择执行路径",
            "code_example": "# 基本条件分支\nage = 18\nif age >= 18:\n    print(\"成年人\")\nelif age >= 6:\n    print(\"未成年人\")\nelse:\n    print(\"儿童\")\n\n# 多条件\nscore = 85\nif score >= 90:\n    grade = \"A\"\nelif score >= 80:\n    grade = \"B\"\nelif score >= 70:\n    grade = \"C\"\nelif score >= 60:\n    grade = \"D\"\nelse:\n    grade = \"F\"\nprint(f\"成绩等级：{grade}\")",
            "code_language": "python",
            "code_explanation": "if后面是条件表达式，elif可以有多个，else可选。条件为True时执行对应代码块。",
            "tips": ["条件表达式返回布尔值", "elif可多个，else可选", "注意缩进一致性"],
            "common_mistakes": ["忘记在if后加冒号", "elif拼写错误写成else if", "条件表达式写成赋值语句"]
        },
        "for循环程序设计基本语法": {
            "content": "for循环用于遍历序列或可迭代对象。语法为for 变量 in 可迭代对象。循环变量依次获得序列中的每个元素。range()函数生成整数序列，常用于指定循环次数。for循环结合列表推导式可以高效处理数据。",
            "summary": "for循环遍历序列，range()生成整数序列，循环变量依次获得每个元素",
            "code_example": "# 基本for循环\nfor i in range(5):\n    print(i, end=\" \")  # 0 1 2 3 4\n\n# 遍历列表\nfruits = [\"苹果\", \"香蕉\", \"橙子\"]\nfor fruit in fruits:\n    print(fruit)\n\n# 遍历字符串\nfor char in \"Python\":\n    print(char)\n\n# 遍历字典\nd = {\"a\": 1, \"b\": 2}\nfor key in d:\n    print(f\"{key}: {d[key]}\")",
            "code_language": "python",
            "code_explanation": "range(5)生成0-4的序列。for循环变量依次获得每个元素，不需要手动更新。",
            "tips": ["range()左闭右开", "循环变量命名要有意义", "善用enumerate()同时获取索引"],
            "common_mistakes": ["range()范围写成range(1,n+1)忘记减1", "在循环内修改循环变量", "忘记循环后的冒号"]
        },
        "for循环设计技巧": {
            "content": "for循环的高级用法包括使用enumerate()获取索引、使用zip()同时遍历多个序列、使用列表推导式进行数据转换和过滤。break和continue控制循环流程。else子句在循环正常结束时执行。",
            "summary": "enumerate、zip、列表推导式等高级用法，break、continue、else控制循环",
            "code_example": "# enumerate获取索引\nfruits = [\"苹果\", \"香蕉\", \"橙子\"]\nfor i, fruit in enumerate(fruits):\n    print(f\"{i}: {fruit}\")\n\n# zip同时遍历\nnames = [\"张三\", \"李四\"]\nscores = [85, 92]\nfor name, score in zip(names, scores):\n    print(f\"{name}: {score}\")\n\n# 列表推导式\nsquares = [x**2 for x in range(10)]\neven_squares = [x**2 for x in range(10) if x % 2 == 0]\n\n# break和continue\nfor i in range(10):\n    if i == 5:\n        break    # 跳出循环\n    if i == 3:\n        continue  # 跳过本次迭代\n    print(i, end=\" \")",
            "code_language": "python",
            "code_explanation": "enumerate同时返回索引和值，zip合并多个序列。break跳出整个循环，continue跳过本次迭代。列表推导式是Python特色。",
            "tips": ["enumerate()替代手动计数", "列表推导式简洁高效", "else在循环正常结束时执行"],
            "common_mistakes": ["break/continue位置错误", "列表推导式过于复杂", "在生成器表达式中修改外层变量"]
        },
        "while循环控制结构": {
            "content": "while循环在条件为True时重复执行代码块。循环变量需要在循环体内更新，否则可能导致死循环。while循环适合在循环次数不确定时使用。要注意设置正确的循环终止条件，避免死循环。",
            "summary": "while循环在条件为True时重复执行，需正确设置终止条件避免死循环",
            "code_example": "# 基本while循环\ncount = 0\nwhile count < 5:\n    print(count, end=\" \")\n    count += 1\n\n# 猜数字游戏\nimport random\ntarget = random.randint(1, 100)\nwhile True:\n    guess = int(input(\"请猜一个数字：\"))\n    if guess == target:\n        print(\"恭喜猜对！\")\n        break\n    elif guess < target:\n        print(\"太小了\")\n    else:\n        print(\"太大了\")",
            "code_language": "python",
            "code_explanation": "while后跟条件表达式，条件为True时重复执行循环体。注意更新循环变量或使用break跳出。",
            "tips": ["确保循环条件会变为False", "善用break提前退出", "设置合理的循环终止条件"],
            "common_mistakes": ["忘记在循环体内更新循环变量导致死循环", "循环条件写成死循环", "混淆break和continue"]
        },
        "while循环设计技巧": {
            "content": "while循环可以结合else子句、标志变量、输入验证等技巧。while True配合break是常见的循环模式。可以用while循环实现do-while语义（先执行后判断）。循环嵌套时注意缩进和break的作用范围。",
            "summary": "while True配合break、else子句、标志变量等高级用法",
            "code_example": "# while-else结构\ncount = 0\nwhile count < 3:\n    password = input(\"请输入密码：\")\n    if password == \"123456\":\n        print(\"登录成功\")\n        break\n    count += 1\nelse:\n    print(\"三次错误，账号锁定\")\n\n# 标志变量\nis_running = True\nwhile is_running:\n    choice = input(\"输入q退出：\")\n    if choice == 'q':\n        is_running = False\n    else:\n        print(f\"你输入了：{choice}\")\n\n# 计算阶乘\nn = 5\nfactorial = 1\nwhile n > 0:\n    factorial *= n\n    n -= 1\nprint(f\"5! = {factorial}\")",
            "code_language": "python",
            "code_explanation": "while-else中，else在循环非正常结束（break）时不执行。标志变量控制循环状态。",
            "tips": ["while-else的else在break时不执行", "标志变量使代码更清晰", "先执行后判断用while True"],
            "common_mistakes": ["死循环", "break范围错误", "忽视else的执行时机"]
        },
        "函数的基本格式": {
            "content": "函数是组织代码的基本单位，用于实现代码复用。Python使用def关键字定义函数，语法为def 函数名(参数):。函数参数可以有默认值。return语句返回值，没有return则返回None。函数定义后不会自动执行，需要调用才能运行。",
            "summary": "def定义函数，参数可有默认值，return返回值，调用执行",
            "code_example": "# 基本函数定义\ndef greet():\n    print(\"Hello!\")\n\ngreet()  # 调用函数\n\n# 带参数和返回值\ndef add(a, b):\n    return a + b\n\nresult = add(3, 5)\nprint(result)  # 8\n\n# 默认参数\ndef greet(name, greeting=\"Hello\"):\n    return f\"{greeting}, {name}!\"\n\nprint(greet(\"张三\"))\nprint(greet(\"李四\", \"Hi\"))",
            "code_language": "python",
            "code_explanation": "def定义函数，参数可以有默认值（默认参数必须放在最后）。return返回结果，没有return返回None。",
            "tips": ["函数名要有意义", "保持函数功能单一", "善用默认参数"],
            "common_mistakes": ["忘记函数后的冒号", "默认参数放在必选参数前", "混淆参数和返回值"]
        },
        "函数设计技巧": {
            "content": "函数设计应遵循单一职责原则。参数不宜过多，过多时应使用字典或类封装。善用参数默认值和可变默认参数（注意默认值只计算一次）。使用*args和**kwargs处理可变数量的参数。",
            "summary": "单一职责、参数封装、默认参数、*args/**kwargs可变参数",
            "code_example": "# 可变参数 *args\ndef sum_all(*numbers):\n    total = 0\n    for n in numbers:\n        total += n\n    return total\n\nprint(sum_all(1, 2, 3))      # 6\nprint(sum_all(1, 2, 3, 4, 5))  # 15\n\n# 关键字参数 **kwargs\ndef print_info(**info):\n    for key, value in info.items():\n        print(f\"{key}: {value}\")\n\nprint_info(name=\"张三\", age=20, city=\"北京\")\n\n# 参数类型检查\ndef add(a: int, b: int) -> int:\n    return a + b",
            "code_language": "python",
            "code_explanation": "*args接收可变位置参数为元组，**kwargs接收可变关键字参数为字典。类型注解不强制执行但有助于文档。",
            "tips": ["*args/**kwargs放在最后", "注意可变默认参数的坑", "类型注解利于代码阅读"],
            "common_mistakes": ["可变默认参数使用列表", "忘记*args/**kwargs如何解包", "参数类型注解不强制"]
        },
        "递归原理分析": {
            "content": "递归是函数调用自身的编程技术。递归有两个关键要素：基本结束条件（递归出口）和递归调用（将问题分解为更小的子问题）。每次递归调用都会在栈上创建新的作用域，递归深度过大会导致栈溢出。递归适合处理自相似性问题。",
            "summary": "递归函数调用自身，需有结束条件和递归调用，逐步分解问题",
            "code_example": "# 递归计算阶乘\ndef factorial(n):\n    if n <= 1:          # 递归出口\n        return 1\n    return n * factorial(n - 1)  # 递归调用\n\nprint(factorial(5))  # 120\n\n# 递归计算斐波那契数列\ndef fib(n):\n    if n <= 1:\n        return n\n    return fib(n-1) + fib(n-2)\n\n# 递归遍历目录\nimport os\ndef list_dir(path, level=0):\n    for item in os.listdir(path):\n        print(\"  \" * level + item)\n        item_path = os.path.join(path, item)\n        if os.path.isdir(item_path):\n            list_dir(item_path, level + 1)",
            "code_language": "python",
            "code_explanation": "递归函数必须有结束条件，否则会无限递归。每次调用栈会保存当前状态，递归深度受限于栈空间。",
            "tips": ["必须要有递归出口", "递归深度不宜过深", "考虑用循环替代递归"],
            "common_mistakes": ["忘记递归出口导致死递归", "递归深度过大栈溢出", "重复计算效率低"]
        },
        "递归的设计方法": {
            "content": "递归设计的一般步骤：1)确定问题的基本情况；2)确定递归关系（如何将问题缩小）；3)确定递归出口。常见的递归模式包括：分治策略（将问题分成子问题分别求解后合并）、减治策略（每次缩小问题规模）、动态规划（记忆化递归）。",
            "summary": "递归设计：确定基本问题、递归关系、递归出口，常用分治减治策略",
            "code_example": "# 分治策略：归并排序\ndef merge_sort(lst):\n    if len(lst) <= 1:\n        return lst\n    mid = len(lst) // 2\n    left = merge_sort(lst[:mid])\n    right = merge_sort(lst[mid:])\n    return merge(left, right)\n\ndef merge(left, right):\n    result = []\n    i = j = 0\n    while i < len(left) and j < len(right):\n        if left[i] <= right[j]:\n            result.append(left[i])\n            i += 1\n        else:\n            result.append(right[j])\n            j += 1\n    result.extend(left[i:])\n    result.extend(right[j:])\n    return result\n\n# 减治策略：快速幂\ndef power(base, exp):\n    if exp == 0:\n        return 1\n    if exp % 2 == 0:\n        return power(base*base, exp//2)\n    return base * power(base, exp-1)",
            "code_language": "python",
            "code_explanation": "分治将问题分成子问题分别求解后合并。减治每次缩小问题规模。记忆化可避免重复计算。",
            "tips": ["画递归树帮助理解", "记忆化避免重复计算", "尾递归优化"],
            "common_mistakes": ["子问题划分不正确", "合并操作出错", "忽视边界条件"]
        },
        "递归的使用场景": {
            "content": "递归适合处理具有自相似结构的问题。典型应用包括：树和图的遍历（如二叉树遍历、文件夹遍历）、分治算法（如归并排序、快速排序）、数学计算（如阶乘、幂运算、斐波那契数列）、搜索问题（如八皇后、迷宫问题）。",
            "summary": "递归适合自相似结构问题：树图遍历、分治算法、数学计算、搜索问题",
            "code_example": "# 二叉树遍历\nclass TreeNode:\n    def __init__(self, val):\n        self.val = val\n        self.left = None\n        self.right = None\n\ndef inorder(root):\n    if root:\n        inorder(root.left)\n        print(root.val, end=\" \")\n        inorder(root.right)\n\n# 汉诺塔\ndef hanoi(n, from_rod, to_rod, aux_rod):\n    if n == 1:\n        print(f\"Move disk 1 from {from_rod} to {to_rod}\")\n        return\n    hanoi(n-1, from_rod, aux_rod, to_rod)\n    print(f\"Move disk {n} from {from_rod} to {to_rod}\")\n    hanoi(n-1, aux_rod, to_rod, from_rod)\n\nhanoi(3, 'A', 'C', 'B')",
            "code_language": "python",
            "code_explanation": "树递归天然适合递归因为树本身是递归结构。汉诺塔是经典的递归问题。",
            "tips": ["树结构天然适合递归", "汉诺塔是经典递归问题", "递归让代码更简洁"],
            "common_mistakes": ["树节点为空时未处理", "递归终止条件错误", "移动步骤错误"]
        },
        "异常处理概念": {
            "content": "异常是程序运行过程中发生的错误，会中断程序正常执行流程。Python使用try-except捕获异常。异常包括系统异常（如除零、越界）和自定义异常。异常处理可以提高程序的健壮性，避免程序因错误而崩溃。",
            "summary": "异常是运行时错误，try-except捕获处理，避免程序崩溃",
            "code_example": "# 基本异常处理\ntry:\n    result = 10 / 0\nexcept ZeroDivisionError:\n    print(\"不能除零\")\n\n# 捕获多个异常\ntry:\n    int(\"abc\")\nexcept ValueError:\n    print(\"值错误\")\nexcept ZeroDivisionError:\n    print(\"除零错误\")\n\n# 捕获所有异常\ntry:\n    result = 10 / 0\nexcept Exception as e:\n    print(f\"发生错误：{e}\")\n\n# try-except-else-finally\ntry:\n    f = open(\"test.txt\", \"r\")\nexcept FileNotFoundError:\n    print(\"文件不存在\")\nelse:\n    content = f.read()\n    f.close()\nfinally:\n    print(\"无论是否出错都会执行\")",
            "code_language": "python",
            "code_explanation": "try中代码出错跳到except。else在try未出错时执行。finally无论是否出错都执行。",
            "tips": ["具体异常放在前面", "避免过于宽泛的except", "finally用于清理资源"],
            "common_mistakes": ["except后不指定异常类型", "except顺序错误", "异常被静默处理"]
        },
        "异常处理在程序设计中的应用": {
            "content": "异常处理的应用场景包括：输入验证（检查用户输入合法性）、文件操作（处理文件不存在等错误）、网络请求（处理连接超时等）、API调用（处理返回错误）。应创建自定义异常类表示特定业务错误，使用异常传递错误信息。",
            "summary": "异常处理用于输入验证、文件网络操作、API调用等场景，可自定义异常",
            "code_example": "# 输入验证\ndef get_positive_number():\n    while True:\n        try:\n            num = int(input(\"请输入正数：\"))\n            if num <= 0:\n                raise ValueError(\"必须输入正数\")\n            return num\n        except ValueError as e:\n            print(f\"输入错误：{e}\")\n\n# 自定义异常\nclass ValidationError(Exception):\n    def __init__(self, message, field):\n        self.message = message\n        self.field = field\n\ndef validate_user(username, age):\n    if not username:\n        raise ValidationError(\"用户名不能为空\", \"username\")\n    if age < 0:\n        raise ValidationError(\"年龄不能为负\", \"age\")\n\n# 异常链\ntry:\n    try:\n        int(\"abc\")\n    except ValueError as e:\n        raise RuntimeError(\"转换失败\") from e\nexcept RuntimeError as e:\n    print(f\"异常：{e}\")\n    print(f\"原因：{e.__cause__}\")",
            "code_language": "python",
            "code_explanation": "自定义异常继承Exception。raise主动抛出异常。异常链用from保留原始异常。",
            "tips": ["异常用于正常控制流之外", "自定义异常利于问题定位", "避免try-except滥用"],
            "common_mistakes": ["用异常代替条件判断", "异常信息不明确", "捕获后不处理"]
        }
    }

    return content_map.get(kp_name, generate_default_content(kp_name))


def generate_default_content(kp_name):
    """为未知知识点生成默认内容"""
    return {
        "content": f"{kp_name}是本章节的重要知识点，需要深入理解其概念和用法。",
        "summary": f"{kp_name}相关知识点总结",
        "code_example": f"# {kp_name}示例\n# 代码示例待补充",
        "code_language": "python",
        "code_explanation": "该知识点需要通过实际代码练习来加深理解。",
        "tips": ["理解基本概念", "多动手实践", "查阅相关文档"],
        "common_mistakes": ["概念理解不清晰", "缺乏实际应用经验", "忽视细节"]
    }


def generate_section_content(chapter_id, chapter_title, section_id, section_title, knowledge_points):
    """生成小节完整内容"""
    kp_list = []
    for idx, kp in enumerate(knowledge_points):
        kp_content = generate_knowledge_point_content(kp["name"], chapter_title, section_title)
        kp_list.append({
            "id": idx + 1,
            "name": kp["name"],
            "content": kp_content["content"],
            "summary": kp_content["summary"],
            "code_example": kp_content["code_example"],
            "code_language": kp_content["code_language"],
            "code_explanation": kp_content["code_explanation"],
            "difficulty": kp.get("difficulty", 1),
            "importance": kp.get("importance", 4),
            "related_points": kp_content.get("related_points", []),
            "tips": kp_content.get("tips", []),
            "common_mistakes": kp_content.get("common_mistakes", [])
        })

    return {
        "chapter_id": chapter_id,
        "chapter_title": chapter_title,
        "section_id": section_id,
        "section_title": section_title,
        "total_knowledge_points": len(knowledge_points),
        "knowledge_points": kp_list
    }


def main():
    """主函数"""
    base_dir = r"C:\Users\17445\Desktop\AIcodiingT eachdemo"

    courses = [
        ("Python程序设计习题配置", "Python程序设计"),
        ("C++程序设计习题配置", "C++程序设计")
    ]

    max_retries = 3

    for course_dir, course_name in courses:
        course_data_path = os.path.join(base_dir, course_dir, "course_data.json")
        output_dir = os.path.join(base_dir, course_dir)

        print(f"\n{'='*60}")
        print(f"处理课程: {course_name}")
        print(f"{'='*60}")

        # 加载课程数据
        retry_count = 0
        while retry_count < max_retries:
            try:
                with open(course_data_path, 'r', encoding='utf-8') as f:
                    course_data = json.load(f)
                break
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    print(f"读取失败，重试 {retry_count}/{max_retries}...")
                    time.sleep(1)
                else:
                    print(f"读取失败：{e}")
                    continue

        # 生成每个小节的内容
        for chapter in course_data["chapters"]:
            chapter_id = chapter["order_index"]
            chapter_title = chapter["title"]

            for section in chapter["sections"]:
                section_id = section["order_index"]
                section_title = section["title"]
                kps = section["knowledge_points"]

                # 生成内容
                section_content = generate_section_content(
                    chapter_id, chapter_title,
                    section_id, section_title,
                    kps
                )

                # 保存文件
                filename = f"第{chapter_id}章第{section_id}节_{section_title}_content.json"
                filepath = os.path.join(output_dir, filename)

                retry_count = 0
                while retry_count < max_retries:
                    try:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            json.dump(section_content, f, ensure_ascii=False, indent=2)
                        print(f"生成: {filename} - {len(kps)}个知识点")
                        break
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"写入失败，重试 {retry_count}/{max_retries}...")
                            time.sleep(0.5)
                        else:
                            print(f"写入失败：{e}")

        print(f"\n{course_name} 完成!")

    print(f"\n{'='*60}")
    print("所有课程知识点内容生成完成!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()