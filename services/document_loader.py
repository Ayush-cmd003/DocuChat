import pdfplumber
import docx


def extract_text(file):

    text = ""

    file.seek(0)

    if file.type == "application/pdf":

        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

    else:

        doc = docx.Document(file)

        for para in doc.paragraphs:
            text += para.text + "\n"

    return text