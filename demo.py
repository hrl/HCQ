import urllib.request
import urllib.parse
import datetime
import re
from pprint import pprint

from pyquery import PyQuery
from lunardate import LunarDate

from dateutil.tz import (
    tzlocal,
    gettz,
)


BuildDict = {
    'w12': '13',
    'e5': '11',
    'e9': '7',
    'w5': '5',
    'e12': '1',
}


def getDateCN():
    tzCN = gettz('Asia/Shanghai')
    timeLocal = datetime.datetime.now(tzlocal())
    timeCN = timeLocal.astimezone(tzCN)
    return timeCN.strftime('%Y-%m-%d')


def getTerm(date=getDateCN(), seazon=None):
    # getTerm(year, seazon):
    #   getTerm(2014, 0): 2014 Spring
    #   getTerm(2014, 1): 2014 Autumn
    # getTerm(date):
    #   getTerm('2014-09-01')
    if seazon is not None:
        year = date
    else:
        year, month, day = date.split('-')
        year = int(year)
        month = int(month)
        day = int(day)

        yearLunar = LunarDate.fromSolarDate(year, month, day).year
        if month < 8:
            if yearLunar == year:
                seazon = 0
            else:
                seazon = 1
        else:
            seazon = 1

        year = yearLunar

    return str((year - 2009) * 2 + seazon)


def reloadValidationCode(postDict, pqPage):
    baseCode = pqPage('input')\
        .filter(lambda: PyQuery(this).attr('id').startswith('_'))
    for i in range(len(baseCode)):
        code = baseCode.eq(i)
        postDict[code.attr('id')] = code.attr('value')


def loadPagePQ(opener, queryUrl, postDict=None):
    if postDict is None:
        page = opener.open(queryUrl).read().decode('utf8', 'ignore')
    else:
        postData = urllib.parse.urlencode(postDict).encode('utf8')
        page = opener.open(queryUrl, postData).read().decode('utf8', 'ignore')
    pq = PyQuery(page)
    return pq


def loadClassroomDetail(roomList, pqClassroomList):
    for i in range(1, len(pqClassroomList)):
        pqClassroom = pqClassroomList.eq(i).children()
        classrommName = pqClassroom.eq(0).text()

        classroomDetailList = []
        for n in range(1, 6):
            pqClassDetail = pqClassroom.eq(n).text()
            if not pqClassDetail:
                classroomDetailList.append(2*n - 1)
                classroomDetailList.append(2*n)

        for n in range(1, len(classroomDetailList), 2):
            try:
                if classroomDetailList[n] + 1 == classroomDetailList[n+1]:
                    classroomDetailList[n] = -1
                    classroomDetailList[n+1] = -1
            except IndexError:
                pass
        classroomDetailList = list(
            filter(lambda x: x != -1, classroomDetailList))

        classroomDetail = ''
        for n in range(0, len(classroomDetailList), 2):
            classroomDetail += "%d-%d, " % (classroomDetailList[n],
                                            classroomDetailList[n+1])
        classroomDetail = classroomDetail.strip(', ')

        if classroomDetail:
            roomList.append((classrommName, classroomDetail))


def queryClass(Build=BuildDict['w12'], QueryDate=getDateCN(), Term=getTerm()):
    # Init
    roomList = []
    queryUrl = "http://202.114.5.131/index.aspx"
    postDict = {
        'Term': Term,
        'Build': Build,
        'QueryDate': QueryDate,
        'Filter': '',
    }
    opener = urllib.request.build_opener()
    opener.addheaders = [
        ("User-Agent", ("Mozilla/5.0 (X11; Linux x86_64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/37.0.2062.120 Safari/537.36")),
        ('Origin', 'http://202.114.5.131'),
        ('Referer', 'http://202.114.5.131/index.aspx'),
    ]

    # Prepare
    pqMain = loadPagePQ(opener, queryUrl)
    reloadValidationCode(postDict, pqMain)
    opener.addheaders = [
        ('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8'),
    ]

    # Load ClassroomList
    postDict['ScriptManager1'] = 'UpdatePanel1|btnRightall'
    postDict['btnRightall'] = '>>'
    pqClass = loadPagePQ(opener, queryUrl, postDict)

    # Clean Dict
    del postDict['ScriptManager1']
    del postDict['btnRightall']

    # Prepare Classroom Detail
    reloadValidationCode(postDict, pqClass)
    postDict['Button1'] = '查询'
    pqDetail = loadPagePQ(opener, queryUrl, postDict)

    # Clean Dict
    del postDict['Button1']

    # Check Page
    pageList = pqDetail('#Pager')
    if pageList:
        pageMaxA = pageList('a').filter(lambda: PyQuery(this).text() == '尾页')
        if pageMaxA:
            pageMaxHref = pageMaxA.attr('href')
            pageMaxRe = re.compile(r'''\d+''')
            pageMax = int(pageMaxRe.findall(pageMaxHref)[0])
        else:
            pageMax = 1
    else:
        pageMax = 1

    # Load Classroom Detail
    pageCurrent = 1
    while pageCurrent <= pageMax:
        pqClassroomList = pqDetail('#gvItem').children()
        loadClassroomDetail(roomList, pqClassroomList)

        if pageCurrent != pageMax:
            # Load Next Page
            reloadValidationCode(postDict, pqDetail)
            postDict['__EVENTTARGET'] = 'Pager'
            postDict['__EVENTARGUMENT'] = str(pageCurrent + 1)
            pqDetail = loadPagePQ(opener, queryUrl, postDict)

            # Clean Dict
            del postDict['__EVENTTARGET']
            del postDict['__EVENTARGUMENT']

        pageCurrent += 1

    return roomList


if __name__ == '__main__':
    queryDate = getDateCN()
    print('可用的自习室:')
    print(queryDate)
    print('--------------------')
    print('西十二:')
    pprint(queryClass(BuildDict['w12'], queryDate))
    print('--------------------')
    print('东九:')
    pprint(queryClass(BuildDict['e9'], queryDate))
    print('--------------------')
    print('西五:')
    pprint(queryClass(BuildDict['w5'], queryDate))
    print('--------------------')
    print('东十二:')
    pprint(queryClass(BuildDict['e12'], queryDate))
    print('--------------------')
    print('东五:')
    pprint(queryClass(BuildDict['w5'], queryDate))
