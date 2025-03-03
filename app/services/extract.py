from spacy.lang.vi import Vietnamese
from word2number import w2n  # Chuyển đổi chữ số thành số

nlp = Vietnamese()


def text_to_number(text: str):
    """Chuyển đổi số dạng chữ sang số nguyên (nếu có thể)."""
    try:
        return w2n.word_to_num(text)
    except ValueError:
        return None  # Nếu không phải số hợp lệ thì bỏ qua


def extract_price_nlp(query: str):
    """
    Sử dụng NLP để tìm khoảng giá trong câu, hỗ trợ cả số và chữ.
    """
    doc = nlp(query)

    numbers = []
    for token in doc:
        if token.like_num:
            numbers.append(int(token.text))  # Nếu là số, thêm vào danh sách
        else:
            num = text_to_number(token.text)  # Kiểm tra nếu là số dạng chữ
            if num is not None:
                numbers.append(num)

    # Xác định khoảng giá
    if len(numbers) == 2:
        return numbers[0], numbers[1]
    elif "dưới" in query:
        return None, numbers[0] if numbers else None
    elif "trên" in query:
        return numbers[0] if numbers else None, None
    return None, None
