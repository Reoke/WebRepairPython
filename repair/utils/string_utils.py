__stop_words__ = {"", "!", "\"", "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", ":", ";", "<", "=", ">", "?", "@", "[", "\\", "]", "^", "_", "`", "{", "|", "}", "~"}

def is_stop_word(word):
    return word.strip() in __stop_words__

def occur_times(string, char):
    cnt = 0
    for c in string:
        if c == char:
            cnt += 1
    return cnt

def is_blank(string):
    return string is None or string.strip() == ''