import sys

collect_ignore = []
if sys.version_info[:2] < (3, 5):
    collect_ignore.append("threadpool/test_text_35.py")
    collect_ignore.append("threadpool/test_binary_35.py")
