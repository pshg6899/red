from functools import wraps
from datetime import datetime
import getpass
import json
import datetime
import pandas as pd
import shutil
import random
from PIL import Image
import pytesseract
import sys
from pdf2image import convert_from_path
from PyPDF2 import PdfFileMerger

pd.set_option('mode.chained_assignment', None)
import tika
import os
import re
import requests
import pymssql

from tika import parser
from pprint import pprint
from nltk.tokenize.punkt import PunktSentenceTokenizer, PunktTrainer, PunktLanguageVars

# DB관련 rule
rule = {}
rule['REPLACE'] = [['&amp;', '&'], ['&lt;', '<'], ['&gt;', '>']]
#rule['ABBREV_WORDS'] = ['sdn', 'bhd', 'prov', 'approx', 'prov', 'pr', 'ex', 'arch', 'no', 'incl', 'i.e', 'etc', 'rev',
#                        'ref', 'e.g', 'art', 'app', 'inj']
rule['ABBREV_WORDS'] = []



# 기타 rule
for i in range(100):
    order1 = '' + str(i) + ''
    rule['ABBREV_WORDS'].append(order1)
order2 = 'i,ii,iii,iv,v,vi,vii,viii,ix,x,xi,xii,xiii,xiv,xv,I,II,III,IV,V,VI,VII,VIII,IX,X,XI'
order2 = order2.split(',')
for i in order2:
    rule['ABBREV_WORDS'].append(i)
order3 = 'aa,bb,cc,dd,ee,ff,gg,hh,jj,kk,'
order3 = order3.split(',')
for i in order3:
    rule['ABBREV_WORDS'].append(i)


class Parser:

    def get_parsing_rule(self, MSSQL_SERVER, MSSQL_PORT, MSSQL_DB, MSSQL_USER, MSSQL_PASSWD):
        conn = pymssql.connect(host=MSSQL_SERVER, port=MSSQL_PORT, database=MSSQL_DB, user=MSSQL_USER,
                               password=MSSQL_PASSWD, charset='utf8')
        cur = conn.cursor()
        sql = "SELECT RuleName, RuleContent FROM TB_DAP_ParsingRule WHERE UseYN = 'Y' ORDER BY ParsingRuleId desc;"
        cur.execute(sql)
        resultList = cur.fetchall()

        abbrevWordList = []
        spentSplitList = []

        for i in range(len(resultList)):
            if (resultList[i][0] == "DIVISION"):
                spentSplitList.append(resultList[i][1])
            elif (resultList[i][0] == "EXCEPTION"):
                abbrevWordList.append(resultList[i][1])
        conn.close()
        return abbrevWordList, spentSplitList


    def get_sent_list(self, PS, tikaUrl, is_ocr, mountpath, image_path, pdf_path, save_path, document_path, file_name):
        xml, convert_ocr_path = PS.get_xml(is_ocr, tikaUrl, mountpath, image_path, save_path,
                                           document_path, pdf_path)
        nullList = []
        tokenizer = PS.get_tokenizer(xml, nullList, nullList)
        toc = PS.get_toc(xml)
        tok_sentance = PS.sentence_tokenize(xml, tokenizer)
        sent_page, sentence, page = PS.get_sen_page(tok_sentance, toc, nullList)

        text_df, sen_list, cate_list, df_sen_pg = PS.frame(sent_page, toc, sentence, page, file_name)
        text_df, sen_class_list = PS.mapping(text_df, df_sen_pg, xml, sen_list, cate_list)

        return sen_class_list

    def get_xml(self, ocr, tikaUrl, path, image_save, save_path, fullname, pdf_save):
        tika.initVM()
        tika.TikaClientOnly = True
        os.environ['no_proxy'] = '*'

        name1 = fullname.split('/')
        name2 = name1[-1].replace('.pdf', '')
        name2 = name2 + "_ocr" + ".pdf"
        name3 = name1[-2] + '/' + name2
        parsed = parser.from_file(path, tikaUrl, xmlContent=True)
        xml2 = parsed["content"]
        xml2 = xml2.split('<div class="page">')
        convert_ocr_path = ""
        xml = ""

        if ocr == "true":

            #if not os.path.exists(save_path + name3):
            pages = convert_from_path(path, 450)
            image_counter = 1


            os.mkdir(image_save)
            os.mkdir(pdf_save)
            for page in pages:
                filename = "page_" + str(image_counter) + ".jpg"

                page.save(image_save+"/" + filename, 'JPEG')

                image_counter = image_counter + 1
            filelimit = image_counter - 1
            pageList = []
            for i in range(1, filelimit + 1):
                filename = "page_" + str(i) + ".jpg"
                filepdfname = "page_" + str(i) + ".pdf"

                pdf = pytesseract.image_to_pdf_or_hocr(image_save +"/" + filename, extension='pdf', config='-psm 6')
                with open(pdf_save+"/" + filepdfname, 'a+b') as f:
                    f.write(pdf)
            shutil.rmtree(image_save)

            merger = PdfFileMerger()
            path = pdf_save

            for i in range(1, filelimit + 1):
                filepdfname = "page_" + str(i) + ".pdf"
                merger.append(pdf_save +"/" + filepdfname)

            shutil.rmtree(pdf_save)

            merger.write(save_path + name3)
            merger.close()
            parsed = parser.from_file(save_path + name3, tikaUrl, xmlContent=True)
            convert_ocr_path=save_path + name3
            xml = parsed["content"]


        else:

            if xml2[2] == "<p />\n</div>\n":

                if not os.path.exists(save_path + name3):

                    pages = convert_from_path(path, 450)
                    image_counter = 1

                    os.mkdir(image_save)
                    os.mkdir(pdf_save)
                    for page in pages:
                        filename = "page_" + str(image_counter) + ".jpg"
                        page.save(image_save+'/' + filename, 'JPEG')
                        image_counter = image_counter + 1
                    filelimit = image_counter - 1
                    pageList = []
                    for i in range(1, filelimit + 1):
                        filename = "page_" + str(i) + ".jpg"
                        filepdfname = "page_" + str(i) + ".pdf"
                        pdf = pytesseract.image_to_pdf_or_hocr(image_save +'/'+ filename, extension='pdf', config='-psm 6' )
                        with open(pdf_save +"/" + filepdfname, 'a+b') as f:
                            f.write(pdf)
                    shutil.rmtree(image_save)

                    merger = PdfFileMerger()
                    path = pdf_save

                    for i in range(1, filelimit + 1):
                        filepdfname = "page_" + str(i) + ".pdf"
                        merger.append(pdf_save +"/" + filepdfname)

                    shutil.rmtree(pdf_save)

                    merger.write(save_path + name3)
                    merger.close()
                    parsed = parser.from_file(save_path + name3, tikaUrl, xmlContent=True)
                    convert_ocr_path = save_path + name3
                    xml = parsed["content"]
                else:
                    parsed = parser.from_file(save_path + name3, tikaUrl, xmlContent=True)
                    xml = parsed["content"]
            else:
                xml = parsed["content"]
        for i in rule['REPLACE']:
            xml = xml.replace(i[0], i[1])

        return xml, convert_ocr_path


    def get_text(self, xml):
        text = []

        page_splited = xml.split('<div class="page">')
        for page in page_splited:
            clean = re.compile('<.*?>')
            xml_cleaned = re.sub(clean, '', page)
            xml_cleaned = xml_cleaned.replace('\n', '')
            xml_cleaned = xml_cleaned.replace('\n\n', '')
            if "....." not in xml_cleaned:
                text.append(xml_cleaned)
        del text[0]
        return text

    def get_tokenizer(self, xml, abbrevWordList, spentSplitList):
        #class BulletPointLangVars(PunktLanguageVars):
            #sent_end_chars = ('?', '!')
            #for i in range(len(spentSplitList)):
            #    sent_end_chars = sent_end_chars + tuple(spentSplitList[i])

        trainer = PunktTrainer()
        trainer.INCLUDE_ALL_COLLOCS = True
        train_data = 'sss'
        trainer.train(train_data)
        tokenizer = PunktSentenceTokenizer(trainer.get_params())
        #tokenizer = PunktSentenceTokenizer(trainer.get_params(), lang_vars = BulletPointLangVars())

        #문장분리 예외추가
        rule['ABBREV_WORDS'].extend(abbrevWordList)

        for i in rule['ABBREV_WORDS']:
            tokenizer._params.abbrev_types.add(i)
        tokenizer = PunktSentenceTokenizer(trainer.get_params())
        return tokenizer

    def get_toc(self, xml):
        toc = []
        for i in rule['REPLACE']:
            xml = xml.replace(i[0], i[1])
        toc_xml = xml.split('\n</p>\n<p>')

        for i in toc_xml:
            if '.....' in i:
                clean = re.compile('<.*?>')
                i_cleaned = re.sub(clean, '', i)
                no_num_cleaned1 = i_cleaned.split(' .')[0]

                if '.....' in no_num_cleaned1:
                    no_num_cleaned2 = no_num_cleaned1.split('..')
                    if '\n\n' not in no_num_cleaned2[0] and '' != no_num_cleaned2[0]:
                        toc.append(no_num_cleaned2[0])

                else:
                    if '\n\n' not in no_num_cleaned1 and '' != no_num_cleaned1:
                        toc.append(no_num_cleaned1)
        toc1 = toc
        # toc
        sum1 = 0
        for i in range(len(toc1)):
            sum1 += int(len(toc1[i]))

        toc4 = []
        toc_xml4 = xml.split('\n')

        for i in toc_xml4:
            if '.....' in i and bool(re.match('[0-9]', i)) and '\n</p>\n<p>' not in i and '0.0' not in i:
                clean = re.compile('<.*?>')
                i_cleaned = re.sub(clean, '', i)
                no_num_cleaned1 = i_cleaned.split(' ..')[0]

                if '.....' in no_num_cleaned1 and bool(re.match('[A-Z]', no_num_cleaned1)):
                    no_num_cleaned2 = no_num_cleaned1.split('..')
                    if "%" not in no_num_cleaned2[0] and ".." not in no_num_cleaned2[0]:
                        toc4.append(no_num_cleaned2[0])
                else:
                    if "%" not in no_num_cleaned1 and ".." not in no_num_cleaned1:
                        toc4.append(no_num_cleaned1)


        sum4 = 0
        for i in range(len(toc4)):
            sum4 += int(len(toc4[i]))


        toc_xml = xml.split('\n</p>\n<p>')
        toc_new = []
        dxlist = []
        dxlist2 = []
        for i in toc_xml:
            dx = toc_xml.index(i)
            if bool(re.match('[1][.]?\s\D', i)):
                dxlist.append(dx)
                if '.....' not in toc_xml[dx] and toc_xml[dx + 1] and toc_xml[dx + 2]:
                    dxlist2.append(dx)
        if dxlist2:

            toc_new = toc_xml[dxlist[0]:dxlist2[0] - 5]
        else:
            toc = []



        toc_new = [item for item in toc_new if bool(re.match('^\w', item))]
        toc_new = [item for item in toc_new if not bool(re.match('[D][a].*\d', item))]

        # 2. .... 숫자를 #로 변환
        toc_new = [re.sub('\.\.+\s?\d+', '#', item) for item in toc_new]
        # toc_new=[item.split("#") for item in toc_new]
        toc_new2 = []
        for item in toc_new:
            tmp = item.split("#")
            toc_new2.extend(tmp)

        toc_new = toc_new2
        toc_new = [item.strip() for item in toc_new]

        toc_new = [item for item in toc_new if item != '']



        df = pd.DataFrame(toc_new, columns=['title'])

        tmp = pd.value_counts(df.title, sort=False)
        tmp = tmp[tmp > 1].keys()
        header = list(tmp)
        toc = [x for x in toc_new if x not in set(header)]  # 순서 보존됨
        toc = [item for item in toc if not bool(re.match('[\D]+\s\d+', item))]

        def istitle(sent):
            res = bool(re.match('([0-9|.]+)|Annex', sent))
            return (res)

        newtitle = []
        for title in toc:
            if istitle(title):
                newtitle.append(title)
            else:
                newtitle[-1] = newtitle[-1] + ' ' + title
        toc=[]
        for i in newtitle:
            if '.....' in i:
                no_num_cleaned2 = i.split('..')
                if '\n\n' not in no_num_cleaned2[0] and '' != no_num_cleaned2[0]:
                    no_num_cleaned2[0]=no_num_cleaned2[0].rstrip()
                    toc.append(no_num_cleaned2[0])
            else:
                if '\n\n' not in i and '' != i:
                    i=i.rstrip()
                    toc.append(i)

        toc2 = toc
        sum2 = 0
        for i in range(len(toc2)):
            sum2 += int(len(toc2[i]))

        toc = []

        toc_xml = xml.split('\n</p>\n<p>')
        toc_new = []
        dxlist = []
        dxlist2 = []
        for i in toc_xml:
            dx = toc_xml.index(i)
            if bool(re.match('[1-6][.][0]\s\D', i)):
                dxlist.append(dx)
                if '.....' not in toc_xml[dx] and toc_xml[dx + 1] and toc_xml[dx + 2]:
                    dxlist2.append(dx)

        if dxlist2:

            toc_new = toc_xml[dxlist[0]:dxlist2[0]]
        else:
            toc = []

        toc_new = [item for item in toc_new if bool(re.match('^\w', item))]
        toc_new = [item for item in toc_new if not bool(re.match('[D][a].*\d', item))]

        toc_new = [re.sub('\.\.+\s?\d+', '#', item) for item in toc_new]
        toc_new2 = []
        for item in toc_new:
            tmp = item.split("#")
            toc_new2.extend(tmp)

        toc_new = toc_new2
        toc_new = [item.strip() for item in toc_new]

        toc_new = [item for item in toc_new if item != '']


        df = pd.DataFrame(toc_new, columns=['title'])

        tmp = pd.value_counts(df.title, sort=False)
        tmp = tmp[tmp > 1].keys()
        header = list(tmp)
        toc = [x for x in toc_new if x not in set(header)]  # 순서 보존됨
        toc = [item for item in toc if not bool(re.match('[\D]+\s\d+', item))]


        def istitle(sent):
            res = bool(re.match('([0-9|.]+)|Annex', sent))
            return (res)

        newtitle = []
        newtitle2 = []

        for title in toc:
            if istitle(title):
                newtitle.append(title)
            else:
                newtitle[-1] = newtitle[-1] + ' ' + title

        for i in newtitle:
            if 'Date:' not in i:
                k = i.replace('\n', '')
                newtitle2.append(k)
        toc3 = newtitle2

        for i in toc3:
            if '<p>' in i:
                toc3 = []

        sum3 = 0
        for i in range(len(toc3)):
            sum3 += int(len(toc3[i]))


        toc = []

        toc_xml = xml.split('\n</p>\n<p>')
        toc_new = []
        dxlist = []
        dxlist2 = []
        for i in toc_xml:
            dx = toc_xml.index(i)
            if bool(re.match('[1-6][.][0]\s\D', i)):
                dxlist.append(dx)
                if '.....' not in toc_xml[dx] and toc_xml[dx + 1] and toc_xml[dx + 2]:
                    dxlist2.append(dx)

        if dxlist2:
            if not dxlist:
                toc_new = toc_xml[dxlist[0]:dxlist2[0]]
            else:
                toc_new = toc_xml[0:dxlist2[0]]

        else:
            toc = []

        b_toc = []
        toc_xml = xml.split('\n</p>\n<p>')
        toc_new = []
        dxlist = []
        dxlist2 = []
        for i in toc_xml:
            dx = toc_xml.index(i)
            if bool(re.match('[T][A][B][L][E]\s[O][F]', i)):
                dxlist.append(dx)
            if bool(re.match('[L][I][S][T]\s[O][F]', i)) or bool(re.match('[A][N][N][E][X]\s[7][:]', i)):
                dxlist2.append(dx)

        b_toc = []
        toc_xml = xml.split('\n</p>\n<p>')
        toc_new = []
        dxlist = []
        dxlist2 = []
        for i in toc_xml:
            dx = toc_xml.index(i)
            if bool(re.match('[T][A][B][L][E]\s[O][F]', i)):
                dxlist.append(dx)
            if bool(re.match('[L][I][S][T]\s[O][F]', i)):
                dxlist2.append(dx)

        #dxlist null 처리
        if dxlist2:
            if not dxlist:
                toc_new = toc_xml[0:dxlist2[0] - 1]
            else:
                toc_new = toc_xml[dxlist[0]:dxlist2[0] - 1]
        else:
            toc = []


        toc_new = [re.sub('\n[0-9][.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?\s[A-Z]', '#\g<0>', item) for item
                   in toc_new]
        toc_new2 = []
        for item in toc_new:
            tmp = item.split("#")
            toc_new2.extend(tmp)
        toc_new = toc_new2
        toc_new = [item.strip() for item in toc_new]
        toc_new = [item for item in toc_new if item != '']

        toc_d = []
        for i in toc_new:
            if '....' in i:
                j = i.split('....')
                toc_d.append(j[0])
            else:
                toc_d.append(i)

        for i in toc_d:
            if '</p>' not in i:
                if 'iii' != i and 'iv' != i and 'v' != i and 'vi' != i and 'viii' != i and '' != i and 'ITT2' not in i:
                    b_toc.append(i)

        for i in range(len(b_toc)):
            if not bool(re.match('[0-9][.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?\s[A-Z]', b_toc[i])):
                b_toc[i - 1] = b_toc[i - 1] + ' ' + b_toc[i]
                b_toc[i] = ''
        d_toc = []
        for i in b_toc:
            if i != '':
                j = i.rstrip()
                d_toc.append(j)
        toc5 = d_toc

        sum5 = 0
        for i in range(len(toc5)):
            sum5 += int(len(toc5[i]))

        b_toc = []
        toc_xml = xml.split('\n</p>\n<p>')

        toc_new = []
        dxlist = []
        dxlist2 = []
        for i in toc_xml:
            dx = toc_xml.index(i)
            if bool(re.match('[T][A][B][L][E]\s[O][F]', i)):
                dxlist.append(dx)
                print(dx)
            if bool(re.match('[L][I][S][T]\s[O][F]', i)) or bool(re.match('[A][N][N][E][X]\s[7][:]', i)):
                dxlist2.append(dx)

        if dxlist2:
            if not dxlist2:
                toc_new = toc_xml[dxlist[0]:dxlist2[0] + 1]
            else:
                toc_new = toc_xml[0:dxlist2[0] + 1]

        else:
            toc = []


        toc_new = [re.sub('\n[0-9][.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?\s[A-Z]', '#\g<0>', item) for item
                   in toc_new]
        toc_new = [re.sub('[A][N][N][E][X]+', '#\g<0>', item) for item in toc_new]

        toc_new2 = []
        for item in toc_new:
            item = item.replace('\n', '')
            tmp = item.split("#")
            toc_new2.extend(tmp)
        toc_new = toc_new2
        toc_new = [item.strip() for item in toc_new]
        toc_new = [item for item in toc_new if item != '']

        toc_d = []
        for i in toc_new:
            if '....' in i:
                j = i.split('....')
                toc_d.append(j[0])
            else:
                toc_d.append(i)

        for i in toc_d:
            if '</p>' not in i:
                if 'iii' != i and 'iv' != i and 'v' != i and 'vi' != i and 'viii' != i and '' != i and 'ITT2' not in i:
                    b_toc.append(i)

        toc6 = []
        for i in range(len(b_toc)):
            if not bool(
                    re.match('[0-9][.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?\s[A-Z]', b_toc[i])) and not bool(
                re.match('[A][N][N][E][X]+', b_toc[i])):
                b_toc[i - 1] = b_toc[i - 1] + ' ' + b_toc[i]
                b_toc[i] = ''
        d_toc = []
        for i in b_toc:
            if i != '':
                j = i.rstrip()
                d_toc.append(j)
                d_toc[0] = d_toc[0].replace(" 5", '')

        for i in d_toc:
            if bool(re.match('[0-9][.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?\s[A-Z]', i)) or bool(
                    re.match('[A][N][N][E][X]+', i)):
                toc6.append(i)

        sum6 = 0
        for i in range(len(toc6)):
            sum6 += int(len(toc6[i]))

        sum_list = [sum1, sum2, sum3, sum4, sum5, sum6]
        toc_list = [toc1, toc2, toc3, toc4, toc5, toc6]
        sum0 = 0
        for i in range(6):

            if sum0 > sum_list[i]:
                sum0 = sum0
            elif sum0 < sum_list[i] and '<p>' not in toc_list[i][-1]:
                sum0 = sum_list[i]
        toc_index = sum_list.index(sum0)
        toc = toc_list[toc_index]

        for i in toc:
            if len(i) < 6 and not bool(re.search('[0-9]', i)) or bool(re.search('\n<p />',i)):
                toc=[]
        return toc

    def sentence_tokenize(self, xml, tokenizer):
        page_splited = xml.split('<div class="page">')

        non_split = []
        for page in page_splited:
            page = re.sub('</p><p>[A-Z]', '###\g<0>', page)
            non_split.append(page)


        #aply0 = []
        #for i in non_split:
           # i = re.sub('\n</p>\n<p>\d\d?[.]\s', '###\g<0>', i)
            #aply0.append(i)

        aply_1 = []
        for i in non_split:
            i = re.sub('\n</p>\n<p>[1-9][0-9]?[.][0-9][0-9]?[.]?[0-9]?[.]?[0-9]?[.]?[0-9]?\s[A-Z]', '###\g<0>', i)
            aply_1.append(i)




        aply_2 = []
        for i in aply_1:
            i = re.sub('\n</p>\n<p>[a-z|A-Z][a-z|A-Z]?[V|I|v|i]?[i|I]?[.|)]\s', '###\g<0>', i)
            aply_2.append(i)

        aply_3 = []
        for i in aply_2:
            i = re.sub('\n</p>\n<p>?\s[A-Z]', '###\g<0>', i)
            aply_3.append(i)


        page_splited = non_split
        semi_split = []
        for page in aply_3:
            clean = re.compile('[ㄱ-ㅣ가-힣]')
            xml_cleaned = re.sub(clean, '', page)
            xml_cleaned = xml_cleaned.replace('\n</p>\n<p>', ' ')
            xml_cleaned = xml_cleaned.replace('  ', ' ')
            clean2 = re.compile('<.*?>')
            xml_cleaned = re.sub(clean2, '', xml_cleaned)

            xml_cleaned = xml_cleaned.split('\uf06f')
            no_toc_tok_sen1 = [res for res in xml_cleaned if '.....' not in res]
            semi_split.append(no_toc_tok_sen1)

        no_toc_tok_sen = []
        for i in semi_split:
            b = []
            for j in i:
                # if len(tokenizer.tokenize(j))>1:

                token_sent = tokenizer.tokenize(j)
                b.extend(token_sent)
            no_toc_tok_sen.append(b)
            for i in no_toc_tok_sen:
                if '........' in i:
                    no_toc_tok_sen.remove(i)
        tok_sentance = no_toc_tok_sen
        return tok_sentance

    def get_sen_page(self, tok_sentance, toc, spentSplitList):

        aply = []
        list1 = []
        list2 = []
        # 정규표현식으로, 목차 가지고 와서 치환
        # print(re.sub('https?://\S+',
        #             '[링크](\g<0>)',
        #             'http://www.google.com and https://greeksharifa.github.io'))
        page = -1
        for l in tok_sentance:
            page = int(page)
            page = page + 1
            for r in l:
                page = str(page)
                result_sent = r
                for t in toc:
                    if t in result_sent:
                        dx = result_sent.index(t)

                        if result_sent[dx - 1] != '.' and result_sent[dx - 2] != '.':
                            result_sent = result_sent.replace(t, '###' + t + '###')
                        elif dx == 0:
                            result_sent = result_sent.replace(t, '###' + t + '###')

                aply.append([result_sent, page])

        aply3 = []
        for i in aply:
            i[0] = re.sub('\s[o]\s\D', '###\g<0>', i[0])
            aply3.append([i[0], i[1]])

        aply4 = []
        for i in aply3:
            # if bool(re.search('\d[.]\d[.]\d\s\D{3,}',i[0])):
            i[0] = re.sub('\\uf0a7', '###\g<0>', i[0])
            i[0] = re.sub('\\uf0b7', '###\g<0>', i[0])
            aply4.append([i[0], i[1]])

        aply5 = []
        for i in aply4:
            i[0] = re.sub('?\s', '###\g<0>', i[0])

            aply5.append([i[0], i[1]])


        # 문장분리
        aply6 = []
        for i in aply5:
            for j in range(len(spentSplitList)):
                i[0] = re.sub(spentSplitList[j], '\g<0>###', i[0])
                aply6.append([i[0], i[1]])

        aply7 = []
        for i in aply6:
            # if bool(re.search('\d[.]\d[.]\d\s\D{3,}',i[0])):
            i[0] = i[0].replace('\n', '')
            i[0] = i[0].replace('\n\n', '')

            aply7.append([i[0], i[1]])

        list1 = []
        list2 = []

        for i in aply7:
            tlist = i[0].split('###')

            # print(len(tlist))
            for t in tlist:
                if len(t.strip()) > 0:
                    list1.append([t.strip(), i[1]])
                    # if len(t) >= 1:

        sent_page_splited = list1

        for i in sent_page_splited:
            i[0] = i[0].replace('=', '')

        sentence = []
        page_number = []

        for i in sent_page_splited:
            sentence.append(i[0])
            page_number.append(i[1])
        page = page_number
        sent_page = sent_page_splited

        return sent_page, sentence, page

    def frame(self, sent_page, toc, sentence, page, file_name):
        df_sen_pg = pd.DataFrame({'sentence': sentence, 'page_number': page})  ## letssee == spacy version
        # df_sen_pg = df_sen_pg[['sentence', 'page_number']]

        text_df = pd.DataFrame(sentence, columns=['sentence'])

        for i in range(5):
            cate = 'category_' + str(i + 1)
            text_df[cate] = ""

        text_length = []
        for i in df_sen_pg['sentence']:
            length = len(i)
            text_length.append(length)

        text_df["number"] = 1
        text_df["shipowner"] = ''
        text_df["file_name"] = file_name
        text_df["page_number"] = page
        text_df["text_length"] = text_length
        text_df["classification"] = 'sentence'
        text_df = text_df[
            ['number', 'shipowner', 'file_name', 'category_1', 'category_2', 'category_3', 'category_4', 'category_5',
             'sentence', 'classification', 'page_number', 'text_length']]
        sen_list = df_sen_pg['sentence'].tolist()
        cate_list = [cate for cate in toc if cate != 'q']
        toc_list = cate_list
        return text_df, sen_list, cate_list, df_sen_pg

    def mapping(self, text_df, df_sen_pg, xml, sen_list, cate_list):
        toc_list = cate_list
        for i_text_list in sen_list:
            for i_cate_list in toc_list:
                # for i_cate_list in cate_list:
                #    for i_text_list in sen_list:

                if i_cate_list in i_text_list:
                    i_text_list_splited = i_text_list.split(" ")
                    num_1 = i_text_list_splited[0]
                    num_1_splited = str(num_1).split(".")
                    i_cate_list_splited = i_cate_list.split(" ")
                    num = i_cate_list_splited[0]
                    num_splited = str(num).split(".")
                    if num_splited == num_1_splited:
                        index_number = sen_list.index(i_text_list)

                        if len(num_splited) == 1:
                            text_df['category_1'][index_number::] = i_cate_list
                            text_df['category_2'][index_number::] = "-"
                            text_df['category_3'][index_number::] = "-"
                            text_df['category_4'][index_number::] = "-"
                            text_df['category_5'][index_number::] = "-"
                        elif len(num_splited) == 2:
                            text_df['category_2'][index_number::] = i_cate_list
                            text_df['category_3'][index_number::] = "-"
                            text_df['category_4'][index_number::] = "-"
                            text_df['category_5'][index_number::] = "-"

                        elif len(num_splited) == 3:
                            text_df['category_3'][index_number::] = i_cate_list
                            text_df['category_4'][index_number::] = "-"
                            text_df['category_5'][index_number::] = "-"

                        elif len(num_splited) == 4:
                            text_df['category_4'][index_number::] = i_cate_list
                            text_df['category_5'][index_number::] = "-"

                        elif len(num_splited) == 5:
                            text_df['category_5'][index_number::] = i_cate_list

        for i_text_list in sen_list:
            for i_cate_list in toc_list:

                if i_cate_list in i_text_list:
                    i_text_list_splited = i_text_list.split(" ")
                    num_1 = i_text_list_splited[0]
                    num_1_splited = str(num_1).split(".")
                    i_cate_list_splited = i_cate_list.split(" ")
                    num = i_cate_list_splited[0]
                    num_splited = str(num).split(".")
                    if num_splited == num_1_splited:
                        index_number = sen_list.index(i_text_list)

                        if len(num_splited) == 1:
                            text_df['classification'][index_number] = 'TOC'
                        elif len(num_splited) == 2:
                            text_df['classification'][index_number] = 'TOC'

                        elif len(num_splited) == 3:
                            text_df['classification'][index_number] = 'TOC'

                        elif len(num_splited) == 4:
                            text_df['classification'][index_number] = 'TOC'

                        elif len(num_splited) == 5:
                            text_df['classification'][index_number] = 'TOC'
        # return text_df

        # def refine_sentence(self, text_df, df_sen_pg, xml, sen_list, toc_list):

        pglist = text_df["page_number"].tolist()
        for i in pglist:
            dx = pglist.index(i)
            if pglist[dx] != pglist[dx - 1]:
                index_number = dx
                text_df['classification'][index_number] = 'Header'
        sen_class_list = []
        sen_class = []
        sen_list = df_sen_pg['sentence'].tolist()
        class_list = text_df['classification'].tolist()
        for i in range(len(sen_list)):
            sen_class = {"sentence": sen_list[i], "type": class_list[i], "page": int(pglist[i])}

            sen_class_list.append(sen_class)

        for i_text_list in sen_list:
            for i_cate_list in cate_list:
                # for i_cate_list in cate_list:
                #    for i_text_list in sen_list:

                if i_cate_list in i_text_list:
                    i_text_list_splited = i_text_list.split(" ")
                    num_1 = i_text_list_splited[0]
                    num_1_splited = str(num_1).split(".")
                    i_cate_list_splited = i_cate_list.split(" ")
                    num = i_cate_list_splited[0]
                    num_splited = str(num).split(".")
                    if num_splited == num_1_splited:
                        index_number = sen_list.index(i_text_list)
                        text_df["sentence"] = text_df["sentence"].drop(index_number)
        text_df = text_df.dropna()

        return text_df, sen_class_list

    def naming(self, fullname):
        name1 = fullname.split('/')
        name2 = name1[-1].replace('.pdf', '')
        excelname = name1[-2] + '/' + name2 + ".xlsx"
        dirname = name1[-2]
        return excelname, dirname
