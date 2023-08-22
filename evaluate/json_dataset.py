import re
import json
import pathlib
from tqdm import tqdm
from datasets import load_dataset


def extract_tax_dataset(partition):
    dataset = load_dataset("singhsays/fake-w2-us-tax-form-dataset")
    for row in tqdm(dataset[partition]['ground_truth']):
        data = json.loads(row)['gt_parse']
        file_name = './fake-w2-us-tax-form-dataset/' + data['box_b_employer_identification_number'] + '.txt'
        with open(file_name, 'w') as f:
            for k, v in data.items():
                delete_part = re.search('box_.{1,3}_[0-9]{0,1}_{0,1}', k)[0]
                new_k = k.replace(delete_part, '').replace('_', ' ')
                new_row = new_k + ': ' + str(v) + '\n'
                f.writelines(new_row)


def extract_legal_dataset(partition):
    dataset = load_dataset("cuad", split=partition)
    for row in tqdm(dataset):
        file_name = './cuad_process/' + row['id'].replace('/', ' ') + '.txt'
        with open(file_name, 'w') as f:
            f.writelines(row['title'] + '\n' + row['context'] + '\n')


def extract_resume_dataset(partition):
    dataset = load_dataset("Sachinkelenjaguri/Resume_dataset", split=partition)
    i = 0
    for row in tqdm(dataset):
        file_name = './resume_process/' + str(i) + '.txt'
        with open(file_name, 'w') as f:
            f.writelines(row['Category'] + '\n' + row['Resume'] + '\n')
        i += 1


if __name__ == '__main__':
    # extract_tax_dataset(partition='test')
    # extract_legal_dataset(partition='test')
    extract_resume_dataset(partition='train')
