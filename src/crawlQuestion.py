# -*- coding: utf-8 -*-

import util
import sys, time, re
from pymongo import MongoClient

def crawlQuestion(qid):
    """ Crawl the topics of the question, and store the result in the database. """
    print '[{0}] starts.'.format(qid)
    apiurl = 'http://www.zhihu.com/question/{0}'.format(qid)
    client = MongoClient()
    content = util.getZhihu(apiurl.format(qid))

    # process the question itself
    topicids = [int(x) for x in re.findall(r'"/topic/(\d+)"', content)]
    timestamp = int(time.time())
    title = re.search('<h2 class="zm-item-title [^"]*">([^<]*)', content).group(1).strip()
    topAnswerIds = re.findall(r'<a class="answer-date-link[^"]*" .*? href="/question/{0}/answer/(\d+)"'.format(qid), content)
    visitsCount = int(re.search('"visitsCount" content="(\d+)"', content).group(1))
    # special handling of follower
    followerNumber = int(re.search(
        '<a href="/question/{0}/followers"><strong>(\d+)</strong></a>'.format(qid), 
        util.getZhihu('http://www.zhihu.com/question/{0}/followers'.format(qid))
    ).group(1))
    toInsert = {
        'id': int(qid),
        'title': title,
        'topicIds': topicids,
        'lastCrawlTimestamp': timestamp,
        'topAnswerIds': topAnswerIds,
        'followerNumber': followerNumber,
        'visitsCount': visitsCount 
    }
    client['zhihu']['questions'].update({ 'id': int(qid) }, toInsert, upsert=True)

    # process the answers
    upvotes = [int(x) for x in re.findall(r'data-votecount="(\d+)"', content)]
    dateCreateds = [int(x) for x in re.findall(r'data-created="(\d+)"', content)]
    scores = [float(x) for x in re.findall(r'data-score="([0-9+-.]*)"', content)]
    # special processing for the authors
    authorStarts = [x.start() for x in re.finditer(r'<h3 class="zm-item-answer-author-wrap">', content)]
    authorEnds = [x + re.search(r'</h3>', content[x:-1]).start() for x in authorStarts]
    authorTexts = [content[s:e] for s, e in zip(authorStarts, authorEnds)]
    def parseAuthor(text):
        match = re.search('/people/([^"]*)', text)
        if match: # visible users
            return match.group(1)
        match = re.search('<h3 [^>]*>([^<]*)</h3>', text)
        if match: # anonymous
            return match.group(1)
        return 'UNKNOWN' # invisible
    authors = [parseAuthor(str(x)) for x in authorTexts]
    assert len(upvotes) == len(topAnswerIds)
    assert len(upvotes) == len(authors)
    assert len(upvotes) == len(dateCreateds)
    assert len(upvotes) == len(scores) 
    #print len(topAnswerIds), topAnswerIds
    #print len(upvotes), upvotes
    #print len(dateCreateds), dateCreateds
    #print len(scores), scores
    #print len(authors), authors
    toInsert = []
    for i in range(len(upvotes)):
        toInsert.append({
            'id': topAnswerIds[i],
            'qid': int(qid),
            'lastQuestionCrawlTimestamp': timestamp,
            'upvote': upvotes[i],
            'dateCreated': dateCreateds[i],
            'score': scores[i],
            'author': authors[i]
        })
    bulk = client['zhihu']['answers'].initialize_ordered_bulk_op()
    for r in toInsert:
        bulk.find({'id': r['id']}).remove()
        bulk.insert(r)
    bulk.execute()
    print '[{0}] complete, {1} answers updated.'.format(qid, len(upvotes))

if __name__ == '__main__':
    if len(sys.argv) != 2:
        sys.stderr.write("""
Usage: {0} <qid>
Crawl zhihu to get the basic information of the question. The output will be written to mongodb.

Example usage: {0} 28339620
""".format(sys.argv[0]))
        sys.exit(-1)

    crawlQuestion(sys.argv[1])
