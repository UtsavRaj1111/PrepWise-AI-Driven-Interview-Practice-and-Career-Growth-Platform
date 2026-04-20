import urllib.request
import uuid

latex_code = "\\documentclass{article}\\begin{document}Hello world\\end{document}"
boundary = uuid.uuid4().hex
payload = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="filecontents[]"; filename="resume.tex"\r\n\r\n'
    f"{latex_code}\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="filename[]"\r\n\r\n'
    f"resume.tex\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="engine"\r\n\r\n'
    f"pdflatex\r\n"
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="return"\r\n\r\n'
    f"pdf\r\n"
    f"--{boundary}--\r\n"
).encode('utf-8')

req = urllib.request.Request('https://texlive.net/cgi-bin/latexcgi', data=payload, method='POST')
req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

with urllib.request.urlopen(req, timeout=25) as response:
    pdf_data = response.read()
    print("Length:", len(pdf_data))
    print("Prefix:", pdf_data[:100])
