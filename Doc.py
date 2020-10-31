from flask import Flask
from flask_classy import FlaskView
from flask import Response, request
from functools import wraps
from datetime import datetime
import getpass
import json
import datetime
import random

import pandas as pd
import tika
import os
import re
from tika import parser
from pprint import pprint
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktTrainer
from flask_cors import CORS
from flask import jsonify

import doc_utils.customlogger as customlogger
import diff as diff
import merge as merge
from Parser import *

app = Flask(__name__)
CORS(app)

config = json.load(open('config.json', 'r'))
tikaUrl = config['TIKA_URL']
MSSQL_SERVER = config['MSSQL_SERVER']
MSSQL_PORT = config['MSSQL_PORT']
MSSQL_DB = config['MSSQL_DB']
MSSQL_USER = config['MSSQL_USER']
MSSQL_PASSWD = config['MSSQL_PASSWD']

# Initialization
logger = customlogger.customlogger().get_logger()


def as_json(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        res = f(*args, **kwargs)
        res = json.dumps(res, ensure_ascii=False).encode('utf8')
        return Response(res, content_type='application/json; charset=utf-8')

    return decorated_function


def loginfo(str):
    logger.info("[" + request.remote_addr + "]" + str)


@app.route('/gettext', methods=['POST'])
def GetText():
    PS = Parser()
    full_path = request.json['document_path']
    ocr = request.json["is_ocr"]
    save_path = config['FILE_SAVE_PATH']
    ran_num = str(random.random()).replace('0.', '')
    excelname, dirname = PS.naming(full_path)
    ocr_dir = save_path + dirname + '/' + 'OCR'

    if not os.path.isdir(save_path + dirname):
        os.mkdir(save_path + dirname)
    if not os.path.isdir(ocr_dir):
        os.mkdir(ocr_dir)
    image_save = ocr_dir + '/' + 'img' + ran_num
    pdf_save = ocr_dir + '/' + 'pdf' + ran_num
    path = config['FILE_SAVE_ROOT'] = request.json['document_path']
    document_idx = request.json['document_idx']
    xml, convert_cor_path = PS.get_xml(ocr, tikaUrl, path, image_save, save_path, full_path, pdf_save)
    text = PS.get_text(xml)

    res = {
        "return_code": "0000",
        "document_idx": document_idx,
        "return_value": text,
        "return_file_ocr_path": convert_cor_path
    }
    jsonRtn = jsonify(res)


    return jsonRtn


@app.route('/getparsing', methods=['POST'])
def GetParsing():
    abs_path = config['FILE_SAVE_ROOT'] + request.json['document_path']
    document_idx = request.json['document_idx']
    file_name = request.json['org_file_name']
    document_path = request.json['document_path']
    is_ocr = request.json["is_ocr"]
    save_path = config['FILE_SAVE_PATH']
    PS = Parser()
    abbrevWordList, spentSplitList = PS.get_parsing_rule(MSSQL_SERVER, MSSQL_PORT, MSSQL_DB, MSSQL_USER, MSSQL_PASSWD)

    # parsing_rule = PS.get_parsing_rule();
    ran_num = str(random.random()).replace('0.', '')
    excel_name, dir_name = PS.naming(document_path)
    excel_file_path = save_path + excel_name
    ocr_dir = save_path + dir_name + '/' + 'OCR'
    if not os.path.isdir(save_path + dir_name):
        os.mkdir(save_path + dir_name)
    if not os.path.isdir(ocr_dir):
        os.mkdir(ocr_dir)
    image_save = ocr_dir + '/' + 'img' + ran_num
    pdf_save = ocr_dir + '/' + 'pdf' + ran_num
    xml, convert_ocr_path = PS.get_xml(is_ocr, tikaUrl, abs_path, image_save, save_path, document_path, pdf_save)
    tokenizer = PS.get_tokenizer(xml, abbrevWordList, spentSplitList)
    toc = PS.get_toc(xml)
    tok_sentance = PS.sentence_tokenize(xml, tokenizer)
    sent_page, sentence, page = PS.get_sen_page(tok_sentance, toc, spentSplitList)

    text_df, sen_list, cate_list, df_sen_pg = PS.frame(sent_page, toc, sentence, page, file_name)
    text_df, sen_class_list = PS.mapping(text_df, df_sen_pg, xml, sen_list, cate_List)
    text_df.to_excel(excel_file_path)

    rel_execl_file_path = excel_file_path.replace(config['FILE_SAVE_ROOT'], '')
    rel_ocr_path = convert_ocr_path.replace(config['FILE_SAVE_ROOT'], '')

    res = {
        'return_code': '0000',
        'document_idx': document_idx,
        'return_value': sen_class_list,
        'return_file_path': rel_execl_file_path,
        # 'return_parsing_rule': parsing_rule,
        "return_file_ocr_path": rel_ocr_path
    }
    jsonRtn = jsonify(res)

    return jsonRtn


@app.route('/getcompare', methods=['POST'])
def GetCompare():
    orgin_path = request.json['document_org_path']
    compare_path = request.json['document_compare_path']
    abs_orgin_path = config['FILE_SAVE_ROOT'] + orgin_path
    abs_compare_path = config['FILE_SAVE_ROOT'] + compare_path
    file_name = request.json['org_file_name']
    compare_file_name = request.json['compare_file_name']
    is_ocr = request.json["is_ocr"]
    save_path = config['FILE_SAVE_PATH']
    PS = Parser()

    ran_num = str(random.random()).replace('0.', '')
    org_excel_name, org_dir_name = PS.naming(orgin_path)
    org_ocr_dir = save_path + org_dir_name + '/' + 'OCR'
    if not os.path.isdir(save_path + org_dir_name):
        os.mkdir(save_path + org_dir_name)
    if not os.path.isdir(org_ocr_dir):
        os.mkdir(org_ocr_dir)
    org_image_save = org_ocr_dir + '/' + 'img' + ran_num
    org_pdf_save = org_ocr_dir + '/' + 'pdf' + ran_num

    cmp_excel_name, cmp_dir_name = PS.naming(compare_path)
    cmp_ocr_dir = save_path + cmp_dir_name + '/' + 'OCR'
    if not os.path.isdir(save_path + cmp_dir_name):
        os.mkdir(save_path + cmp_dir_name)
    if not os.path.isdir(cmp_ocr_dir):
        os.mkdir(cmp_ocr_dir)
    cmp_image_save = cmp_ocr_dir + '/' + 'img'+ ran_num
    cmp_pdf_save = cmp_ocr_dir + '/' + 'pdf'+ ran_num

    orgDic = PS.get_sent_list(PS, tikaUrl, is_ocr, abs_orgin_path, org_image_save, org_pdf_save, save_path, org_path, file_name)
    compareDic = PS.get_sent_list(PS, tikaUrl, is_ocr, abs_compare_path, cmp_image_save, cmp_pdf_save,
                                  save_path, compare_path, compare_file_name)

    splitOrginSentList = diff.GetSplitSentence(orgDic)
    splitCompareSentList = diff.GetSplitSentence(compareDic)
    insertByPage, deleteByPage, replaceByPage = diff.GetDiffByKind(orgDic, compareDic, splitOrginSentList,
                                                                   splitCompareSentList)

    res = {
        'return_code': '0000',
        'return_value': {"insertByPage": insertByPage, "deleteByPage": deleteBypage, "replaceByPage": replaceByPage}
    }

    jsonRtn = jsonify(res)
    return jsonRtn


@app.route('/getmerge', methods=['POST'])
def GetMerge():
    merge_file_path = config['FILE_SAVE_ROOT'] + request.json['merge_file_path'] + "/" + "merge.pdf"
    rtn_merge_file_path = request.json['merge_file_path'] + "/" + "merge.pdf"
    file_path_list = request.json['file_path_list']
    file_full_path = []
    for file_path in file_path_list:
        file_full_path.append(config['FILE_SAVE_ROOT'] + file_path)
                
    merge.merger(file_full_path, merge_file_path)

    res = {
        'return_code': '0000',
        'return_value': {"mergeFilePath": rtn_merge_file_path}
     }

    jsonRtn = jsontify(res)
    return jsonRtn


class GetOcrView(FlaskView):
    @as_json
    def post(self):
        res = {
            'return_code': '0000',
            'document_idx': 'documet_idx',
            'return_value': "\\60.100.110.40\\share$\\eni\\itt_doc_OCR.pdf"
        }
        
        return res


# GetTextView.register(app)
# GetExportExcelview.register(app)
# GetsenTocView.register(app)
# GetOcrView.register(app)
#
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8011)
