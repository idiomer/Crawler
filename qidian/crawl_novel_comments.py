#coding:utf-8
import requests
import bs4
from bs4 import BeautifulSoup
import os
import json
import re
import time


headers = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"}


def makedirs(thepath):
    if not os.path.exists(thepath):
        os.makedirs(thepath)

def get_book_tags(html):
    tags_node = html.findAll('p', attrs={'class': 'tag'})[0]
    tag_color_list = [{'tagName': tag.get_text().strip(), 'tagColor': '&'.join(tag.get('class', ''))} 
        for tag in tags_node if isinstance(tag, bs4.element.Tag)]
    return tag_color_list

def crawl(bookId, _csrfToken=None, output_path='data/novel_chapter_comments'):
    exception_count = 0
    if _csrfToken is None:
        raise Exception("_csrfToken must be not None")
    makedirs(output_path)

    bookId = int(bookId)
    chapter_text_title_href, html = get_chapters(bookId)
    if chapter_text_title_href:
        book_path = os.path.join(output_path, 'bookId=%s' % bookId)
        makedirs(book_path)

        with open(os.path.join(book_path, '_meta.json'), 'w', encoding='utf-8') as fw:
            tags = get_book_tags(html)
            json.dump(dict(bookId=bookId, tags=tags), fw, ensure_ascii=False)

    for text, title, href in chapter_text_title_href:
        # 获取章节id
        chapter_url = 'http:' + href
        chapter_html = get_chapter_html(chapter_url)
        chapterId = int(get_chapter_id(chapter_html.text))
        if chapterId < 0:
            exception_count += 1
            print("warning: %s can't get chapterId" % chapter_url)
            continue
        
        chapter_path = os.path.join(book_path, 'chapterId=%s' % chapterId)
        if os.path.exists(chapter_path):
            print("skip %s" % chapter_path)
            continue

        # 获取有评论的segments
        segments = get_segments_having_comment(bookId, chapterId, _csrfToken=_csrfToken)
        if segments is None:
            exception_count += 1
            print("warning: get_segments_having_comment(%d, %d) failed" % (bookId, chapterId))
            continue
        if len(segments) == 0:
            print('skip %s/%s for len(segments) == 0' % (bookId, chapterId))

        # 获取segment的所有评论
        if len(segments) == 0:
            continue
        segments_with_comments = []
        for d in segments:
            segmentId = d['segmentId']
            reviewNum = d['reviewNum']
            if reviewNum == 0:
                continue
            # other_keys: containSelf, isHotSegment

            comments = get_segment_comments(bookId, chapterId, segmentId, pageSize=reviewNum+1, _csrfToken=_csrfToken)
            if comments is None or len(comments) == 0:
                exception_count += 1
                print("warning: get_segment_comments(%s, %s, %s, _csrfToken=%s) failed" % (
                    bookId, chapterId, segmentId, _csrfToken))
                continue

            d['bookId'] = bookId
            d['chapterId'] = chapterId
            d['quoteContent'] = get_quoteContent(comments)
            d['comments'] = comments
            segments_with_comments.append(d)

        # 保存章节信息
        makedirs(chapter_path)
        with open(os.path.join(chapter_path, '_meta.json'), 'w', encoding='utf-8') as fw:
            json.dump(dict(chapterId=chapterId, 
                           chapterTitle=text.strip(), 
                           chapterUrl=href.strip(),
                           chapterOtherInfo=title.strip(),
                           ), 
                    fw, ensure_ascii=False, indent=2)
        # 保存章节内的所有segments的评论
        with open(os.path.join(chapter_path, 'segments_comments.json'), 'w', encoding='utf-8') as fw:
            json.dump(segments_with_comments, fw, ensure_ascii=False)
        print('finish %s' % chapter_path)
    if exception_count > 10:
        raise Exception('exception_count > 10')

def get_quoteContent(comments):
    for comment in comments:
        if 'quoteContent' in comment:
            return comment['quoteContent']
    raise Exception('')

def get_chapters(bookId, url='https://book.qidian.com/info/', whole_url=None):
    if whole_url is not None:
        resp = requests.get(url, headers=headers)
    else:
        resp = requests.get(url + str(bookId), headers=headers)
    html = BeautifulSoup(resp.text)
    links = html.findAll('a')
    result = [[node.get_text(), node.get('title', ''), node.get('href')] for node in links 
        if 'read.qidian.com/chapter/' in node.get('href', '') 
            and node.get_text() not in ("", "免费试读")
    ]

    mid = len(result) // 2
    seen = dict()
    unique_results = []
    for i, item in enumerate(result):
        text, title, href  = item
        if href not in seen:
            unique_results.append(item)
            seen[href] = len(unique_results) - 1
        else:
            # 重复的href，尽可能取靠近中间的那个；跨中点的取前面的那个
            if i <= mid:
                seen.pop(seen[href])
                unique_results.append(item)
                seen[href] = len(unique_results) - 1
            else:
                continue
    return unique_results, html

def get_chapter_html(chapter_url):
    return requests.get(chapter_url, headers=headers)

def get_chapter_id(html_text):
    import re
    m = re.search(r'id="chapter-(\d+)"', html_text)
    if m:
        chapter_id = m.group(1)
    else:
        m2 = re.search(r'data-cid="(\d+)"', html_text)
        if m2:
            chapter_id = m2.group(1)
        else:
            chapter_id = "-1"
    return chapter_id

def get_segments_having_comment(bookId, chapterId, _csrfToken=None, 
        url='https://read.qidian.com/ajax/chapterReview/reviewSummary', whole_url=None):
    '''
    '''

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,en-US;q=0.6",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
    }
    if whole_url is not None:
        resp = requests.get(whole_url, headers=headers)
    else:
        if _csrfToken is None:
            raise Exception("_csrfToken must be not None")
        params = dict(_csrfToken=_csrfToken, bookId=bookId, chapterId=chapterId)
        resp = requests.get(url, params=params, headers=headers)

    result = resp.json()
    if str(result['code']) == "0":
        return result['data']['list']
    else:
        print(result)
        return None

def get_segment_comments(bookId, chapterId, segmentId, type_=2, page=1, pageSize=20, 
        _csrfToken=None, url='https://read.qidian.com/ajax/chapterReview/reviewList', whole_url=None):
    ''' segmentId: 段落
    whole_url = "https://read.qidian.com/ajax/chapterReview/reviewList
                ?_csrfToken=eiCZbuIwSi15D93NRb3jCMZbj7aIBNm881c257rr&bookId=1023698028
                &chapterId=571666566&segmentId=-1&type=2&page=1&pageSize=20"
    '''

    headers = {
        "accept": "application/json, text/javascript, */*; q=0.01",
        "accept-encoding": "gzip, deflate, br",
        "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,zh-TW;q=0.7,en-US;q=0.6",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
    }
    if whole_url is not None:
        resp = requests.get(whole_url, headers=headers)
    else:
        if _csrfToken is None:
            raise Exception("_csrfToken must be not None")
        params = dict(_csrfToken=_csrfToken, bookId=bookId, chapterId=chapterId, segmentId=segmentId, 
                        type=type_, page=page, pageSize=pageSize)
        resp = requests.get(url, params=params, headers=headers)
    result = resp.json()
    if str(result['code']) == "0":
        return result['data']['list']
    else:
        print(result)
        return None

def get_bookId_list(url='https://www.qidian.com/'):
    re_bookId = re.compile(r'//book\.qidian\.com/info/(\d+)')
    resp = requests.get(url, headers=headers)
    html = BeautifulSoup(resp.text)
    bookId_list = [int(re_bookId.search(node.get('href', '')).group(1)) for node in html.findAll('a') 
        if re_bookId.search(node.get('href', ''))]
    return bookId_list

def get_token():
    resp = requests.get('https://www.qidian.com/ajax/Help/getCode?_csrfToken=')
    if resp.json()['code'] == 0:
        return [item.split('=', 1)[1] for item in resp.headers['Set-Cookie'].split('; ') if '_csrfToken=' in item][0]
    else:
        return None


if __name__ == '__main__':
    _csrfToken = get_token()
    print('_csrfToken = %s' % _csrfToken)
    bookId_list = get_bookId_list('https://www.qidian.com/lishi')
    print('#books = %d' % len(bookId_list))
    for bookId in bookId_list:
        print("now book is %s" % bookId)
        crawl(bookId, _csrfToken)





'''
{'code': 0,
 'msg': 'success',
 'data': {'list': [{'segmentId': -1,
    'reviewNum': 4,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 64,
    'reviewNum': 2,
    'containSelf': False,
    'isHotSegment': True},
   {'segmentId': 1,
    'reviewNum': 2,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 4,
    'reviewNum': 1,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 69,
    'reviewNum': 5,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 6,
    'reviewNum': 3,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 7,
    'reviewNum': 1,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 8,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 74,
    'reviewNum': 2,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 13,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 14,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 15,
    'reviewNum': 1,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 16,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 19,
    'reviewNum': 1,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 23,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 26,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 27,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 28,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 29,
    'reviewNum': 3,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 33,
    'reviewNum': 0,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 48,
    'reviewNum': 4,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 49,
    'reviewNum': 2,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 50,
    'reviewNum': 2,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 55,
    'reviewNum': 4,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 56,
    'reviewNum': 3,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 57,
    'reviewNum': 1,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 60,
    'reviewNum': 2,
    'containSelf': False,
    'isHotSegment': False},
   {'segmentId': 63,
    'reviewNum': 1,
    'containSelf': False,
    'isHotSegment': False}],
  'total': 28}}


{'code': 0,
 'msg': 'success',
 'data': {'list': [{'reviewId': '523423540414906368',
    'cbid': '18005249408491104',
    'ccid': '48354474586519009',
    'guid': '850000586674',
    'userId': '221637815',
    'nickName': '游鱗',
    'avatar': 'https://qidian.qpic.cn/qd_face/349573/3250245/100',
    'segmentId': 50,
    'content': '杀鱼角，如果你教我发财，我就请你吃炒粉！',
    'status': 1,
    'createTime': '09-16 09:34:33',
    'updateTime': '2020-12-07 09:36:22',
    'quoteReviewId': '0',
    'quoteContent': '嘴上骂着，但扑街少年眼珠子一转，还是小跑追了上去，嘴上说道：“呐，杀鱼角，我也不是不信你，就是想开开眼界，你怎么三个月让黑窝仔自己出来开档口。”',
    'quoteGuid': '0',
    'quoteUserId': '0',
    'quoteNickName': '',
    'type': 2,
    'likeCount': 16,
    'dislikeCount': 0,
    'userLike': False,
    'userDislike': False,
    'isSelf': False,
    'essenceStatus': False,
    'riseStatus': False,
    'level': 2,
    'imagePre': '',
    'imageDetail': '',
    'rootReviewId': '523423540414906368',
    'rootReviewReplyCount': 0},
   {'reviewId': '523243839591415808',
    'cbid': '18005249408491104',
    'ccid': '48354474586519009',
    'guid': '120007816793',
    'userId': '319516296',
    'nickName': '道正贤',
    'avatar': 'https://qidian.qpic.cn/qd_face/349573/6159580/100',
    'segmentId': 50,
    'content': '草，有画面了',
    'status': 1,
    'createTime': '09-15 21:40:29',
    'updateTime': '2020-12-07 09:36:24',
    'quoteReviewId': '0',
    'quoteContent': '嘴上骂着，但扑街少年眼珠子一转，还是小跑追了上去，嘴上说道：“呐，杀鱼角，我也不是不信你，就是想开开眼界，你怎么三个月让黑窝仔自己出来开档口。”',
    'quoteGuid': '0',
    'quoteUserId': '0',
    'quoteNickName': '',
    'type': 2,
    'likeCount': 17,
    'dislikeCount': 0,
    'userLike': False,
    'userDislike': False,
    'isSelf': False,
    'essenceStatus': False,
    'riseStatus': False,
    'level': 1,
    'imagePre': '',
    'imageDetail': '',
    'rootReviewId': '523243839591415808',
    'rootReviewReplyCount': 0}],
  'total': 2,
  'isEnd': 1}}
'''
