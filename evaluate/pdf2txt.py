import slate
import pathlib
from tqdm import tqdm


def pdf2txt(pdf_path, txt_path):
    with open(pdf_path, 'rb') as f:
        doc = slate.PDF(f)
    with open(txt_path, 'w') as f:
        f.write('\n'.join(doc))


if __name__ == '__main__':
    pathlib.Path('./Samples of electronic invoices TXT/Dataset with valid information/').mkdir(parents=True, exist_ok=True)
    path_list = pathlib.Path('./Samples of electronic invoices/Dataset with valid information/').glob('*')
    for path in tqdm(path_list):
        write_path = str(path).replace('Samples of electronic invoices', 'Samples of electronic invoices TXT').replace('pdf', 'txt')
        pdf2txt(pdf_path=path, txt_path=write_path)
