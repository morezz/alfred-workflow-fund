#!/usr/bin/python
# -*- coding: utf-8 -*-
import sys
import requests
import json
import re
import argparse
from workflow import Workflow, ICON_INFO, ICON_WARNING, web


def check(code):
    url = "http://fundgz.1234567.com.cn/js/%s.js" % code

    headers = {'content-type': 'application/json',
               'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:22.0) Gecko/20100101 Firefox/22.0'}

    # r = web.get(url, params=None, headers=headers)

    r = requests.get(url, headers=headers)

    # fundcode      - 基金代码
    # name          - 基金名称
    # jzrq          - 净值日期
    # dwjz          - 当日净值
    # gsz           - 估算净值
    # gszzl         - 估算涨跌百分比 即-0.42%
    # gztime        - 估值时间

    # jsonpgz({"fundcode":"320007","name":"xxxx","jzrq":"2021-02-18","dwjz":"1.8190","gsz":"1.8143","gszzl":"-0.26",
    # "gztime":"2021-02-19 15:00"});%
    content = r.text

    pattern = r'^jsonpgz\((.*)\)'

    search = re.findall(pattern, content)
    result = None
    try:
        for i in search:
            data = json.loads(i)
            result = data
    except Exception as e:
        print(e)

    return result


def search_key_for_fund(data):
    return json.dumps(data)


def main(wf):
    reload(sys)  # reload 才能调用 setdefaultencoding 方法
    sys.setdefaultencoding('utf-8')  # 设置 'utf-8'

    # build argument parser to parse script args and collect their
    # values
    parser = argparse.ArgumentParser()
    # add an optional (nargs='?') --setfundcode argument and save its
    # value to 'fundcode' (dest). This will be called from a separate "Run Script"
    parser.add_argument('--setfundcode', dest='fundcode', nargs='?', default=None)
    # add an optional query and save it to 'query'
    parser.add_argument('query', nargs='?', default=None)
    # parse the script's arguments
    args = parser.parse_args(wf.args)

    ####################################################################
    # Save the fund code
    ####################################################################

    # decide what to do based on arguments
    if args.fundcode:  # Script was passed fund code
        # save the key
        fund_code_list = wf.settings.get('fund_code_key', [])
        fund_code_list.append(args.fundcode)
        wf.settings['fund_code_key'] = list(set(fund_code_list))
        return 0  # 0 means script exited cleanly

    ####################################################################
    # Check that we have fund code
    ####################################################################

    fund_code_list = wf.settings.get('fund_code_key', None)
    if not fund_code_list:  # Fund code has not yet been set
        wf.add_item('No fund code key set.', 'Please use fundsave to set your fund code.', valid=False,
                    icon=ICON_WARNING)
        wf.send_feedback()
        return 0

    ####################################################################
    # View/filter fund result
    ####################################################################
    query = args.query
    # Retrieve fund from cache if available and no more than 60
    # seconds old
    fund_result = []

    def wrapper():
        """`cached_data` can only take a bare callable (no args),
        so we need to wrap callables needing arguments in a function
        that needs none.
        """
        for code in fund_code_list:
            fund_result.append(check(code))
        return fund_result

    fund_result = wf.cached_data('funds', wrapper, max_age=10)

    # If script was passed a query, use it to filter funds
    if query:
        fund_result = wf.filter(query, fund_result, key=search_key_for_fund, min_score=20)

    # Loop through the returned funds and add a item for each to
    # the list of results for Alfred
    for data in fund_result:
        # result = "Name: {}, Fund Unit net worth: {}, Or fall: {}".format(data["name"], data["dwjz"], data["gszzl"])
        main_title = "{}, {}".format(data["name"], data["fundcode"])
        sub_title = "{}, {}%, {}, {}".format(data["gsz"], data["gszzl"], data["dwjz"], data["gztime"])
        wf.add_item(title=main_title, subtitle=sub_title, valid=True, icon=ICON_INFO)

    wf.send_feedback()
    return 0


if __name__ == u"__main__":
    wf = Workflow()
    sys.exit(wf.run(main))
