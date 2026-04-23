"""
生成第9章 数据永久性存储的所有小节知识点
"""
import asyncio
import json
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models import Course, Chapter, Section
from app.models.section_knowledge_point import SectionKnowledgePoint

async def get_or_create_course():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Course).where(Course.name == "C语言程序设计"))
        course = result.scalar_one_or_none()
        if not course:
            course = Course(name="C语言程序设计", description="C语言程序设计课程")
            db.add(course)
            await db.commit()
            await db.refresh(course)
        return course.id

async def get_or_create_chapter(course_id):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Chapter).where(Chapter.course_id == course_id, Chapter.order_index == 9)
        )
        chapter = result.scalar_one_or_none()
        if not chapter:
            chapter = Chapter(
                course_id=course_id,
                title="数据永久性存储",
                description="掌握文件操作的基本方法",
                order_index=9
            )
            db.add(chapter)
            await db.commit()
            await db.refresh(chapter)
        return chapter.id

async def create_section_with_points(chapter_id, order_index, title, summary, points):
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Section).where(Section.chapter_id == chapter_id, Section.order_index == order_index)
        )
        section = result.scalar_one_or_none()
        if not section:
            section = Section(chapter_id=chapter_id, title=title, order_index=order_index)
            db.add(section)
            await db.commit()
            await db.refresh(section)

        for i, pt in enumerate(points):
            kp = SectionKnowledgePoint(
                section_id=section.id,
                name=pt["name"],
                content=pt["content"],
                summary=pt.get("summary", ""),
                code_example=pt.get("code_example", ""),
                code_language="c",
                code_explanation=pt.get("code_explanation", ""),
                difficulty=pt.get("difficulty", "medium"),
                importance=pt.get("importance", 3),
                related_points=",".join(pt.get("related_points", [])),
                tips=",".join(pt.get("tips", [])) if pt.get("tips") else "",
                common_mistakes=",".join(pt.get("common_mistakes", [])) if pt.get("common_mistakes") else "",
                order_index=i
            )
            db.add(kp)
        await db.commit()
        print(f"  [{title}] {len(points)}个知识点")
        return section.id

async def main():
    print("正在生成第9章：数据永久性存储...")

    course_id = await get_or_create_course()
    chapter_id = await get_or_create_chapter(course_id)

    # 9.1 文件概述与基本概念
    await create_section_with_points(chapter_id, 1, "文件概述与基本概念", "理解文件的概念、分类和C语言中的文件操作框架", [
        {
            "name": "文件的基本概念与分类",
            "content": "文件是存储在外部介质上的数据集合，C语言将文件视为有序的字节流。按存储方式分为文本文件（ASCII）和二进制文件；按访问方式分为顺序访问和随机访问。",
            "summary": "文件是外部存储的数据集合，分为文本/二进制、顺序/随机访问",
            "code_example": "/* 文件指针概念 */\n#include <stdio.h>\n\nint main() {\n    FILE *fp;  // 文件指针\n    fp = fopen(\"test.txt\", \"r\");\n    if (fp == NULL) {\n        printf(\"文件打开失败\\n\");\n        return 1;\n    }\n    // 操作文件...\n    fclose(fp);\n    return 0;\n}",
            "code_explanation": "FILE是C语言中定义的文件结构体类型，FILE *是文件指针，用于操作文件。fopen返回NULL表示打开失败。",
            "difficulty": "easy",
            "importance": 4,
            "related_points": ["文件打开关闭", "文件操作流程"],
            "tips": ["始终检查fopen返回值", "操作完毕后及时关闭文件"],
            "common_mistakes": ["打开文件后不检查返回值", "忘记fclose关闭文件"]
        },
        {
            "name": "文件操作的基本流程",
            "content": "文件操作遵循'打开-操作-关闭'的基本流程。首先使用fopen打开文件获得文件指针，然后使用fread/fwrite/fprintf等函数进行读写操作，最后使用fclose关闭文件释放资源。",
            "summary": "文件操作三步曲：打开文件→读写操作→关闭文件",
            "code_example": "#include <stdio.h>\n\nint main() {\n    FILE *fp = fopen(\"data.txt\", \"w\");\n    if (fp != NULL) {\n        fprintf(fp, \"Hello, World!\\n\");\n        fclose(fp);  // 关闭文件\n    }\n    return 0;\n}",
            "code_explanation": "此例展示完整的文件操作流程：先以写入模式打开文件，写入数据后关闭文件。",
            "difficulty": "easy",
            "importance": 5,
            "related_points": ["文件打开模式", "fprintf函数"],
            "tips": ["养成检查文件是否成功打开的习惯", "关闭文件后才能确保数据写入"],
            "common_mistakes": ["忘记关闭文件导致数据未写入", "文件路径错误"]
        }
    ])

    # 9.2 文本文件与二进制文件
    await create_section_with_points(chapter_id, 2, "文本文件与二进制文件", "理解文本文件和二进制文件的区别及适用场景", [
        {
            "name": "文本文件的特点与操作",
            "content": "文本文件以ASCII或Unicode字符存储，数据按行组织，每行以换行符结束。文本模式打开时，系统会对某些字符（如换行符）进行自动转换。适合存储字符数据如配置文件、文档等。",
            "summary": "文本文件以字符存储，换行符自动转换，适合纯文本数据",
            "code_example": "#include <stdio.h>\n\nint main() {\n    FILE *fp = fopen(\"note.txt\", \"w\");\n    fprintf(fp, \"第一行\\n第二行\\n\");\n    fclose(fp);\n\n    fp = fopen(\"note.txt\", \"r\");\n    char buffer[100];\n    while (fgets(buffer, sizeof(buffer), fp) != NULL) {\n        printf(\"%s\", buffer);\n    }\n    fclose(fp);\n    return 0;\n}",
            "code_explanation": "fprintf写入格式化文本，fgets按行读取文本文件内容。文本文件中换行符会被特殊处理。",
            "difficulty": "medium",
            "importance": 4,
            "related_points": ["fprintf函数", "fgets函数", "文本模式打开"],
            "tips": ["文本文件可用记事本直接查看", "换行符在不同系统有差异"],
            "common_mistakes": ["混淆二进制和文本模式", "不处理换行符的差异"]
        },
        {
            "name": "二进制文件的特点与操作",
            "content": "二进制文件以字节为单位存储原始数据，不进行任何字符转换。数据按内存中的实际形式存储，适合存储图像、音频、结构体等非文本数据。二进制文件更紧凑，访问效率更高。",
            "summary": "二进制文件以字节存储原始数据，无字符转换，适合非文本数据",
            "code_example": "#include <stdio.h>\n\nstruct Student {\n    char name[20];\n    int age;\n    float score;\n};\n\nint main() {\n    struct Student s = {\"张三\", 20, 95.5f};\n\n    // 写入二进制文件\n    FILE *fp = fopen(\"student.dat\", \"wb\");\n    fwrite(&s, sizeof(struct Student), 1, fp);\n    fclose(fp);\n\n    // 读取二进制文件\n    fp = fopen(\"student.dat\", \"rb\");\n    struct Student read_s;\n    fread(&read_s, sizeof(struct Student), 1, fp);\n    printf(\"%s %d %.1f\\n\", read_s.name, read_s.age, read_s.score);\n    fclose(fp);\n    return 0;\n}",
            "code_explanation": "fwrite将结构体原样写入文件，fread从文件读取完整结构体，二进制操作不进行任何数据转换。",
            "difficulty": "medium",
            "importance": 5,
            "related_points": ["fwrite函数", "fread函数", "结构体文件操作"],
            "tips": ["二进制文件用'wb'/'rb'模式打开", "结构体中避免使用指针"],
            "common_mistakes": ["文本和二进制模式混淆", "结构体含指针导致写入无效数据"]
        }
    ])

    # 9.3 文件操作函数详解
    await create_section_with_points(chapter_id, 3, "文件操作函数详解", "掌握常用的文件读写和定位函数", [
        {
            "name": "文件打开模式详解",
            "content": "文件打开模式决定后续操作权限。'r'只读（文件需存在），'w'只写（不存在则创建，存在则清空），'a'追加（从文件末尾写），'r+'读写（文件需存在），'w+'读写（创建或清空文件），'a+'读写（从末尾读写）。带b表示二进制模式如'rb'、'wb'。",
            "summary": "文件模式：r/w/a配合+读写，带b表示二进制模式",
            "code_example": "#include <stdio.h>\n\nint main() {\n    // 各种打开模式示例\n    FILE *fp1 = fopen(\"read.txt\", \"r\");    // 只读\n    FILE *fp2 = fopen(\"write.txt\", \"w\");   // 只写\n    FILE *fp3 = fopen(\"append.txt\", \"a\");  // 追加\n    FILE *fp4 = fopen(\"data.bin\", \"rb\");   // 二进制只读\n\n    if (fp1 && fp2 && fp3 && fp4) {\n        printf(\"所有文件打开成功\\n\");\n    }\n\n    // 关闭所有文件\n    fclose(fp1); fclose(fp2); fclose(fp3); fclose(fp4);\n    return 0;\n}",
            "code_explanation": "不同模式用于不同场景：读取用'r'，新建/覆盖用'w'，追加用'a'，二进制文件加'b'后缀。",
            "difficulty": "medium",
            "importance": 5,
            "related_points": ["fopen函数", "fclose函数", "文件指针概念"],
            "tips": ["优先使用'rb'/'wb'处理二进制文件", "'w'模式会覆盖已存在的文件"],
            "common_mistakes": ["对不存在的文件用'r'模式", "'w'模式意外覆盖原有数据"]
        },
        {
            "name": "字符和字符串读写函数",
            "content": "fgetc/fputc读写单个字符，fgets读取一行字符串，fputs写入字符串。feof判断是否到达文件末尾。这些函数是文本文件操作的基础。",
            "summary": "fgetc/fputc字符读写，fgets/fputs字符串读写，feof判断文件结尾",
            "code_example": "#include <stdio.h>\n\nint main() {\n    // 写入字符\n    FILE *fp = fopen(\"char.txt\", \"w\");\n    fputc('A', fp);\n    fputs(\"Hello\\n\", fp);\n    fclose(fp);\n\n    // 读取字符和字符串\n    fp = fopen(\"char.txt\", \"r\");\n    char c = fgetc(fp);\n    printf(\"第一个字符: %c\\n\", c);\n\n    char line[100];\n    while (fgets(line, sizeof(line), fp) != NULL) {\n        printf(\"%s\", line);\n    }\n    fclose(fp);\n    return 0;\n}",
            "code_explanation": "fputc写入单个字符'A'，fputs写入字符串'Hello'，fgetc读取单个字符，fgets按行读取直到换行符或EOF。",
            "difficulty": "easy",
            "importance": 4,
            "related_points": ["fgetc", "fputc", "fgets", "fputs", "feof"],
            "tips": ["fgets保留换行符，fputs不自动添加换行符", "使用feof()判断文件结束"],
            "common_mistakes": ["fgets忘记检查NULL返回值", "缓冲区大小设置过小"]
        },
        {
            "name": "格式化读写与块读写函数",
            "content": "fprintf/fscanf用于格式化读写文本文件，fread/fwrite用于读写二进制数据块。fread的4个参数：数据指针、元素大小、元素数量、文件指针；fwrite格式相同。",
            "summary": "fprintf/fscanf格式化读写文本，fread/fwrite块读写二进制数据",
            "code_example": "#include <stdio.h>\n\nint main() {\n    // 格式化读写\n    FILE *fp = fopen(\"info.txt\", \"w\");\n    fprintf(fp, \"%s %d %.2f\\n\", \"张三\", 20, 95.5);\n    fclose(fp);\n\n    fp = fopen(\"info.txt\", \"r\");\n    char name[20]; int age; float score;\n    fscanf(fp, \"%s %d %f\", name, &age, &score);\n    printf(\"%s %d %.2f\\n\", name, age, score);\n    fclose(fp);\n\n    // 块读写\n    int arr[] = {1, 2, 3, 4, 5};\n    fp = fopen(\"array.bin\", \"wb\");\n    fwrite(arr, sizeof(arr), 1, fp);\n    fclose(fp);\n    return 0;\n}",
            "code_explanation": "fprintf/fscanf像printf/scanf一样格式化读写文件，fread/fwrite一次性读写大量数据。",
            "difficulty": "medium",
            "importance": 5,
            "related_points": ["fprintf", "fscanf", "fread", "fwrite"],
            "tips": ["fread/fwrite适合读写数组和结构体", "格式化读写适合有规律的数据"],
            "common_mistakes": ["fscanf忘记取地址符&", "fread返回值未检查"]
        }
    ])

    # 9.4 文件应用综合实例
    await create_section_with_points(chapter_id, 4, "文件应用综合实例", "综合运用文件操作实现数据持久化管理", [
        {
            "name": "文件数据保存与加载",
            "content": "利用文件实现数据的持久化存储。将程序中的数据结构（如学生信息、配置参数）写入文件保存，下次运行时从文件读取恢复。这是应用程序数据持久化的基本模式。",
            "summary": "通过文件读写实现程序数据的永久保存和加载恢复",
            "code_example": "#include <stdio.h>\n\n#define MAX_STUDENTS 100\n\nstruct Student {\n    char name[20];\n    int id;\n    float score;\n};\n\nvoid save_students(struct Student *students, int count) {\n    FILE *fp = fopen(\"students.dat\", \"wb\");\n    if (fp) {\n        fwrite(&count, sizeof(int), 1, fp);\n        fwrite(students, sizeof(struct Student), count, fp);\n        fclose(fp);\n        printf(\"保存成功！\\n\");\n    }\n}\n\nint load_students(struct Student *students) {\n    FILE *fp = fopen(\"students.dat\", \"rb\");\n    if (!fp) return 0;\n    int count;\n    fread(&count, sizeof(int), 1, fp);\n    fread(students, sizeof(struct Student), count, fp);\n    fclose(fp);\n    return count;\n}\n\nint main() {\n    struct Student stu[3] = {{\"张三\", 1, 90}, {\"李四\", 2, 85}, {\"王五\", 3, 92}};\n    save_students(stu, 3);\n\n    struct Student loaded[10];\n    int n = load_students(loaded);\n    printf(\"加载了 %d 名学生\\n\", n);\n    return 0;\n}",
            "code_explanation": "save_students先写入学生数量，再写入所有学生数据；load_students先读取数量，再读取对应数量的学生记录。",
            "difficulty": "medium",
            "importance": 5,
            "related_points": ["fread/fwrite块操作", "二进制文件存储结构体", "数据持久化概念"],
            "tips": ["先保存数量再保存数据，加载时先读数量", "二进制文件比文本文件更紧凑高效"],
            "common_mistakes": ["保存时未考虑数据格式版本", "加载时未检查文件是否存在"]
        },
        {
            "name": "文件加密与安全存储",
            "content": "基本的文件加密可通过简单变换实现，如XOR加密：将每个字节与密钥进行XOR运算加密，解密时再进行一次XOR即可恢复。实际应用中应使用更安全的加密算法。",
            "summary": "简单XOR加密可用于文件保护，实际应用需更强加密算法",
            "code_example": "#include <stdio.h>\n\nvoid encrypt_file(const char *filename, char key) {\n    FILE *fp = fopen(filename, \"rb+\");\n    if (!fp) return;\n\n    char ch;\n    while (fread(&ch, 1, 1, fp) == 1) {\n        fseek(fp, -1, SEEK_CUR);\n        ch ^= key;  // XOR加密\n        fwrite(&ch, 1, 1, fp);\n    }\n    fclose(fp);\n}\n\nint main() {\n    char key = 'K';\n\n    // 加密文件\n    FILE *fp = fopen(\"secret.txt\", \"w\");\n    fprintf(fp, \"机密信息123\");\n    fclose(fp);\n\n    encrypt_file(\"secret.txt\", key);\n    printf(\"文件已加密\\n\");\n\n    // 解密文件\n    encrypt_file(\"secret.txt\", key);\n\n    fp = fopen(\"secret.txt\", \"r\");\n    char c;\n    while ((c = fgetc(fp)) != EOF) putchar(c);\n    fclose(fp);\n    return 0;\n}",
            "code_explanation": "XOR加密的特性：同一个字节与密钥XOR两次恢复原值。加密和解密使用相同的encrypt_file函数。",
            "difficulty": "hard",
            "importance": 3,
            "related_points": ["位运算XOR", "文件随机访问fseek", "数据安全概念"],
            "tips": ["XOR加密简单但安全性有限", "重要数据应使用专业加密库"],
            "common_mistakes": ["加密后丢失密钥无法恢复", "密钥使用固定值易被破解"]
        }
    ])

    print("\n第9章生成完成，共4个小节，9个知识点")

asyncio.run(main())