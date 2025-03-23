from PyPDF2 import PdfReader
from pdf2image import convert_from_path
import pandas as pd
import pdfplumber
import re


def pdf_to_text(path):
    with pdfplumber.open(path) as pdf:
        text = ""
        for page in pdf.pages:
            text += page.extract_text()
        return text
    
def get_essay(text):
    # 取出申論題文本
    match = re.search(r"國文字作答。(.+)", text, re.DOTALL).group(1)
    
    # 用中文大寫數字分隔題目
    questions = re.split("\n[一|二|三|四|五|六|七|八|九|十]、", match)

    # 清除題目分數、頁數、考試代號等雜訊
    questions = [re.sub(r"（\d+ 分）", "", q_, re.DOTALL) for q_ in questions]
    questions = [re.sub(r"代號[\s\S]*?頁次\s*：\s*\d+－\d+\n?", "", q_, re.DOTALL) for q_ in questions]

    # 清除各題中的換行符號
    questions = [re.sub(r"[\r\n\u2028\u2029\u0085]+", "", q_, re.DOTALL) for q_ in questions]

    # 清除空的元素
    questions = [q_ for q_ in questions if q_ != "" ]

    # 將申論題中的怪異字元用 - 取代
    questions = [re.sub("||", "\n- ", q_) for q_ in questions]

    return questions

def get_mcq(text):
    # 取出多選題文本
    match = re.search(r"禁止使用電子計算器。(.+)", text, re.DOTALL).group(1)

    # 用題號的阿拉伯數字 + 換行符號 + 空格來進行拆解
    questions = re.split("\n\d+ ", match)

    # 清除題目分數、代號與頁次等雜訊
    questions = [re.sub(r"（\d+ 分）", "", q_, re.DOTALL) for q_ in questions]
    questions = [re.sub(r"代號[\s\S]*?頁次\s*：\s*\d+－\d+\n?", "", q_, re.DOTALL) for q_ in questions]

    # 清除各題內部之換行符號
    questions = [re.sub(r"[\r\n\u2028\u2029\u0085]+", "", q_, re.DOTALL) for q_ in questions]

    # 清除空值
    questions = [q_ for q_ in questions if q_ != "" ]

    # 將各題目的字串拆成 Q + A + B + C + D -> questions: [[], [], []]
    questions = [re.split(r"|||", q_, re.DOTALL) for q_ in questions]
    return questions

def get_mixed(text):
    """
    某些考題內有申論題也有選擇題。觀察考題結構，發現申論題的注意事項必有
    「本科目除專門名詞或數理公式外，應使用本國文字作答。」
    這個句子放在考題前方，並以「乙、測驗題部分」作為申論題步驟的結尾。
    因此可以使用「式外，應使用本(.+)乙、測驗題部分」這個 pattern 將申論題的結構取出，存入 essay_part 變數。
    保留某些開頭文字是因為 essay_part 這個字串可以直接丟給 get_essay() 這個函數進行處理。

    而多選題的部分也用一樣邏輯，將多選題部分字串存入 mcq_part

    return: 
    - essay_part: 之後再用 get_essay() 函數處理
    - mcq_part: 之後再用 get_mcq() 函數處理
    """
    essay_part = re.search(r"式外，應使用本(.+)乙、測驗題部分", text, re.DOTALL).group(1)
    mcq_part = "禁止使用電子計算器。" + re.search(r"於本試題或申論試卷上作答者，不予計分。(.+)", text, re.DOTALL).group(1)

    return essay_part, mcq_part

def get_answers(text):

    try:
        answer_str = re.search(r"其更正內容詳見備註。\n(.+)", text, re.DOTALL).group(1)
    except:
        answer_str = re.search(r"標準答案：\n(.+)", text, re.DOTALL).group(1)
    answer_lst = [ _.split('\n答案') for _ in answer_str.split("題號")]
    answer_lst = [ [_.strip() for _ in ls] for ls in answer_lst]
    # print(answer_str)
    answers = {}
    for row in answer_lst:
        if len(row) != 2:
            pass
        elif ("A" not in row[1]) & ("B" not in row[1]) & ("C" not in row[1]) & ("D" not in row[1]):
            pass
        else:
            for q_idx, ans in zip(row[0].split(' '), row[1].split(' ')):
                answers.update({re.search("(\d+)", q_idx).group(1): ans})

    answers = [value for key, value in answers.items()]
    return answers
    