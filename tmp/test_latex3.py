import urllib.request
import urllib.parse
latex_code = "\\documentclass{article}\\begin{document}Hello world\\end{document}"
url = 'https://latex.ytotech.com/build'
data_encoded = urllib.parse.urlencode({'code': latex_code}).encode('utf-8')
req = urllib.request.Request(url, data=data_encoded, method='POST')
try:
    with urllib.request.urlopen(req, timeout=15) as response:
        pdf_data = response.read()
        print("Success, length:", len(pdf_data))
except Exception as e:
    print(e)
