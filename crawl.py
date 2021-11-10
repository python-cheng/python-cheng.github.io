# -*- coding: utf-8 -*-
import json
import requests
import random
from time import sleep
from lxml import etree
from selenium import webdriver
from collections import defaultdict
from selenium.webdriver import ChromeOptions
from selenium.webdriver.chrome.options import Options
from selenium.webdriver import ActionChains
from selenium.common.exceptions import UnexpectedAlertPresentException

# 绕过服务器端的反爬检测
option = ChromeOptions()
option.add_argument('disable-infobars')
option.add_experimental_option('excludeSwitches', ['enable-automation'])
option.add_experimental_option('useAutomationExtension', False)
option.add_argument("--disable-blink-features=AutomationControlled")

# 实现浏览器的无头显示（设置好后，爬取数据失败，目前没有解决）
chrome_options = Options()
chrome_options.add_argument('--headless')
chrome_options.add_argument('--disable-gpu')

# 该代码主要实现代理ip(如果ip被封，可以使用)
# options = webdriver.ChromeOptions()
# options.add_argument('--proxy-server=http://117.69.186.245')

# UA伪装，反爬策略的一种
# headers = {
#     'User-Agent':'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/93.0.4577.82 Safari/537.36'
# }

# 爬取所需内容的主要程序
def crawl_step_1(bro1,file,current_url):
    page_text = bro1.page_source
    tree1 = etree.HTML(page_text)
    # 获取所需内容对应的标签
    div_list1 = tree1.xpath('//div[@class="company-original-offer-list"]/div')
    # 内容存在多个标签中，因此要循环遍历
    for div in div_list1:
        # 过滤掉异常，以防程序终止（主要为过滤掉店铺只保留工厂）
        try:
            flag = div.xpath('.//span[@class="factory-tag"]/text()')[0]
        except Exception:
            continue
        # 过滤掉非石家庄地区的工厂
        location = div.xpath('.//span[@class="position-text"]//text()')[0]
        if location != '河北石家庄':
            continue
        # 获取工厂名称
        company_name = div.xpath('.//div[@class="title-container"]/a/text()')[0]
        # 获取工厂经营时间
        time = div.xpath('.//span[@class="integrity-year"]/text()')[0]
        # 获取产品类型（其返回值为列表，需将其转换为字符串）
        production_type = div.xpath('.//span[@class="service-info"]/span//text()')
        production_type = '|'.join(production_type)
        # 获取交易笔数、回头率等
        trading = div.xpath('.//div[@class="company-info"]//text()')
        trading_dic = defaultdict(str)
        name_list = []
        res_list = []
        for n1 in range(0,len(trading),2):
            name_list.append(trading[n1])
        for n2 in range(1,len(trading)+1,2):
            res_list.append(trading[n2])
        for key,value in zip(name_list,res_list):
            trading_dic[key] = value
        # 获取主营产品
        main_production = div.xpath('.//span[@class="main-craft-content"]//text()')[0]
        # 获取公司详细信息如员工总数、公司面积等信息，需要点击详细信息的url
        company_info_url = div.xpath('.//span[@class="company-breadcrumb"]/a[2]/@href')[0]

        bro2 = webdriver.Chrome(executable_path='./chromedriver',options=option)
        sleep(5)
        bro2.get(url=current_url)
        # 取得上一次信息登录时的cookies,主要目的是绕过淘宝的反爬检测
        with open('C:/Users/G.C.adjacent/Desktop/cookies.txt', 'r') as fp:
            cookies = json.load(fp)
            for cookie in cookies:
                cookie.pop('domain')
                bro2.add_cookie(cookie)
        sleep(5)
        bro2.get(url=company_info_url)
        sleep(5)
        page_text = bro2.page_source
        tree2 = etree.HTML(page_text)
        # 获取工厂的地址
        try:
            address = tree2.xpath('//div[@class="location"]//text()')[0]
        except Exception:
            address = ''
        # 获取年交易额(因为格式的原因，需要采用一些方法，来实现)
        total_volume = tree2.xpath('//div[@style="margin: 16px; display: flex; flex-flow: row wrap; border-width: 1px 1px 1px 0px; border-left-style: initial; border-left-color: initial; border-bottom-style: solid; border-bottom-color: rgb(241, 245, 255); border-top-style: solid; border-top-color: rgb(241, 245, 255); border-right-style: solid; border-right-color: rgb(241, 245, 255);"]//text()')
        total_volume_dic = defaultdict(str)
        key_list = []
        value_list = []
        for n3 in range(0,len(total_volume),2):
            key_list.append(total_volume[n3])
        for n4 in range(1,len(total_volume)+1,2):
            value_list.append(total_volume[n4])
        for key,value in zip(key_list,value_list):
            total_volume_dic[key] = value
        sleep(8)
        # 将数据读入到csv文件中
        vector = str(company_name)+','+str(time)+','+str(production_type)+','+str(trading_dic['近90天成交笔数'])+','+str(trading_dic['回头率'])+','+str(total_volume_dic['员工总数'])+','+str(total_volume_dic['公司面积'])+','+str(main_production)+','+str(address)+','+str(total_volume_dic['年交易额'])+'\n'
        file.write(vector)
        print('数据爬取完毕!!!')
        bro2.quit()

def crawl_step_2(bro1,current_url):
    file = open('C:/Users/G.C.adjacent/Desktop/crawl.csv', 'w', encoding='utf-8-sig')
    title = '公司名称' + ',' + '时间' + ',' + '生产类型' + ',' + '近90天成交笔数' + ',' + '回头率' + ',' + '员工总数' + ',' + '公司面积' + ',' + '主营产品' + ',' + '公司地址' + ',' + '年交易额' + '\n'
    file.write(title)
    # 获取某一区域搜索出来的信息的全部页数
    total_page = bro1.find_element_by_xpath('//*[@id="app"]/div/div[9]/div/div/div/span[1]/em').text
    sleep(3)
    # 循环遍历，实现全部页数的爬取
    for page in range(int(total_page)+1):
        crawl_step_1(bro1, file,current_url)
        print('当前页爬取完毕！！！')
        # 当前页爬取完毕后，就进行下一页点击
        sleep(15)
        next_page = bro1.find_element_by_xpath('//*[@id="app"]/div/div[9]/div/div/span/a[8]')
        sleep(3)
        next_page.click()
        sleep(3)
        bro1.execute_script('window.scrollTo(0,document.body.scrollHeight)')
        sleep(8)
    file.close()
    bro1.quit()

def crawl_step_3(region):
    # 需要进行登录
    url = 'https://s.1688.com/company/company_search.htm'
    bro1 = webdriver.Chrome(executable_path='./chromedriver',options=option)

    bro1.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
    })

    bro1.get(url=url)
    sleep(8)
    bro1.find_element_by_id('alisearch-input').send_keys(region)
    sleep(3)
    bro1.find_element_by_xpath('//*[@id="app"]/div/div[2]/div[1]/div/div[2]/div/div/div[1]/form/fieldset/div/div[2]/button').click()
    sleep(3)
    a_tag = bro1.find_element_by_xpath('//*[@id="alibar"]/div[1]/div[2]/ul/li[3]/a')
    a_tag.click()
    sleep(3)
    user_name = bro1.find_element_by_xpath('//*[@id="fm-login-id"]')
    password = bro1.find_element_by_xpath('//*[@id="fm-login-password"]')
    # 输入账号
    sleep(3)
    user_name.send_keys('***')
    # 输入密码
    sleep(3)
    password.send_keys('***')
    sleep(3)
    btn = bro1.find_element_by_xpath('//*[@id="login-form"]/div[4]/button')
    btn.click()
    sleep(8)
    current_url = bro1.current_url
    cookies = bro1.get_cookies()
    with open('C:/Users/G.C.adjacent/Desktop/cookies.txt','w') as fp:
        json.dump(cookies,fp)
    crawl_step_2(bro1,current_url)


if __name__ == '__main__':
    # 注意事项：一次只能爬取一个区域的数据，如果要爬取多个区域，需要手动更改区域即修修改region的值
    # 为了躲避淘宝网站的反爬检测，需要修改浏览器驱动中的$cdc对应的内容
    # 请求过快会使得服务端进行限速，最后导致网络通信故障，从而使得爬取数据失败,因此，有时需要修改休眠时间
    # 如果运行出错，请重新尝试再运行一次
    # 如果上述操作都尝试了，爬虫爬到一定时间还是出错，那就需要考虑将页数缩减，隔一段时间再爬，即一次爬取少量的数据
    # url = 'https://s.1688.com/company/company_search.htm?keywords=%DE%BB%B3%C7&spm=a26352.13672862.searchbox.input'
    region = '藁城'
    crawl_step_3(region)
