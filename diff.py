import difflib
from operator import itemgetter


def GetSimpleList(orginList):
    simpleList = list()
    for element in orginList:
        # print(element['sentence'])
        simpleList.append(element['sentence'])
    return  simpleList


def GetPageCount(dic):
    # print(dic)
    lastest_page = max(dic, key=itemgetter('page'))
    # print(lastest_page)
    return  lastest_page['page']


def GetSplitSentence(inputList):
    # print(inputList)
    maxPage = GetPageCount(inputList)
    pageList = []

    for i in range(maxPage):
        page = i + 1
        outputList = [x for x in inputList if x['page'] == page]
        sentences = ""
        for j in range(len(outputList)):
            sentences = sentences + outputList[j]['sentence']

        pageList.insert(page, sentences)

    return pageList


def GetDiff(seqm):
    output = []
    insert = ""
    delete = ""
    replace = ""
    for opcode, a0, a1, b0, b1 in seqm.get_opcodes():
        if opcode == 'equal':
            output.append(seqm.a[a0:a1 + 5])
        elif opcode == 'insert':
            output.append("<ins>" + seqm.b[b0:b1] + "</ins>")
            insert = insert + '|' + seqm.b[b0:b1] if len(insert) > 0 else seqm.b[b0:b1]
        elif opcode == 'delete':
            output.append("<del>" + seqm.a[a0:a1] + "</del>")
            delete = delete + '|' + seqm.a[a0:a1] if len(delete) > 0 else seqm.a[a0:a1]
        elif opcode == 'replace':
            output.append("<replace>" + seqm.a[a0:a1] + "</replace>")
            replace = replace + '|' + seqm.a[a0:a1] if len(replace) > 0 else seqm.a[a0:a1]
        else:
            raise RuntimeError
    return output, insert, delete, replace


def GetDiffText(t1, t2):
    sm = difflib.SequenceMatcher(None, t1, t2)
    res, insert, delete, replace = GetDiff(sm)
    return res, insert, delete, replace


def GetDiffByKind(orgDic, compareDic, splitOrginSentList, splitCompareSentList):
    insertByPage = ""
    deleteByPage = ""
    replaceByPage = ""

    orginPageNum = GetPageCount(orgDic)
    comparePageNum = GetPageCount(compareDic)

    maxPageNum = comparePageNum if orginPageNum >= comparePageNum else orginPageNum

    for iPage in range(maxPageNum):
        res, insert, delete, replace = GetDiffText(splitOrginSentList[iPage], splitCompareSentList[ipage])
        insertByPage = insertByPage + '@@' + insert if len(insertByPage) > 0 else insert
        deleteByPage = deleteByPage + '@@' + delete if len(deleteByPage) > 0 else delete
        replaceBypage = replaceByPage + '@@' + replace if len(replaceBypage) > 0 else replace

    return insertBypage, deleteByPage, replaceByPage
