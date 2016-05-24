from django.shortcuts import render, render_to_response
from django.template import RequestContext
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt  
from .liveqa import main
from lxml import etree
from xml.sax.saxutils import escape
import logging
import json
# Create your views here.
logger = logging.getLogger(__name__)
xml_esc = {"'": "&apos;", '"': '&quot;'}
def index(request):
    return render_to_response('index.html', {}, RequestContext(request))

@csrf_exempt   
def run(request):
    q_id = request.POST['qid']
    q_id = q_id.replace('YA:', '')
    q_category = request.POST['category']
    q_title = request.POST['title']
    q_body = request.POST['body']
    answered = 'yes'
    logger.debug('*********** INCOMING QUESTION ***********')
    logger.debug('id: {}'.format(q_id))
    logger.debug('title: {}'.format(q_title))
    logger.debug('body: {}'.format(q_body))
    try:
        resp = main.run(q_id, q_category, q_title, q_body)
    except:
        logger.error('LIVEQA Error {}'.format(request.POST), exc_info=True)
        answered = 'no'
        resp = {
            'answer': {
                'q':{
                    'best_answer': '',
                    'url': '',
                    'title': '',
                }
            },
            'time': 0
        }
    ctxt = {
        'q_title': q_title,
        'q_body': q_body,
        'response': resp['answer']['q']['best_answer'],
        'time': resp['time']
    }


    try:
        xml = etree.XML("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <xml>
              <answer answered="{answered}" pid="{pid}" qid="{qid}" time="{time}">
                <content>{answer}</content>
                <resources>{resources}</resources>
                <title-foci>0-5</title-foci>
                <body-foci>0-4</body-foci>
                <summary>{summary}</summary>
              </answer>
            </xml>""".format(
                **{'answered':answered, 
                 'qid': q_id,
                 'pid': 'JBC-TREC2016', 
                 'time': resp['time'], 
                 'answer': escape(resp['answer']['q']['best_answer'], xml_esc), 
                 'resources': escape(resp['answer']['q']['url'], xml_esc), 
                 'summary': escape(resp['answer']['q']['title'], xml_esc)}))
    except:
        xml = etree.XML("""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
            <xml>
              <answer answered="{answered}" pid="{pid}" qid="{qid}" time="{time}">
                <content>{answer}</content>
                <resources>{resources}</resources>
                <title-foci>0-5</title-foci>
                <body-foci>0-4</body-foci>
                <summary>{summary}</summary>
              </answer>
            </xml>""".format(
                **{'answered':answered, 
                 'qid': q_id,
                 'pid': 'JBC-TREC2016', 
                 'time': resp['time'], 
                 'answer': escape(resp['answer']['q']['best_answer'].encode('utf-8'), xml_esc), 
                 'resources': escape(resp['answer']['q']['url'], xml_esc), 
                 'summary': escape(resp['answer']['q']['title'].encode('utf-8'), xml_esc)}))
    try:
        logger.debug(
            json.dumps(
                etree.tostring(xml, xml_declaration=True, encoding="utf-8")
                )
            )
        xml_resp = etree.tostring(xml, xml_declaration=True, encoding="utf-8")
    except:
        logger.debug(
            json.dumps(
                etree.tostring(xml, xml_declaration=True)
                )
            )
        xml_resp = etree.tostring(xml, xml_declaration=True)
    #return render_to_response('index.html', ctxt, RequestContext(request))
    return HttpResponse(xml_resp)
