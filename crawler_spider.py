import re
import pandas as pd
import requests
from lxml import html
from urllib.parse import urlparse,urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
from retrying import retry
import time
import logging

class MySpider(object):
    def __init__(self,url_seed,path_read,path_save):
        '''
        初始化
        :param url_seed:
        :param path_read:
        :param path_save:
        '''
        self.url_seed = url_seed#数据源
        self.company = None#公司名
        self.path_read = path_read#公司名excel路径
        self.path_save = path_save#保存的excel路径
        options = Options()
        options.add_argument('--headless')
        self.driver = webdriver.Firefox(executable_path='D:\\geckodriver-v0.23.0-win64\\geckodriver.exe', options=options)
        self.log = logging.Logger('')#简单的日志输出
        self.log.addHandler(logging.StreamHandler())

    def load_excel(self):
        '''
        加载excel中公司名称
        :return:
        '''
        companys = pd.read_excel(self.path_read, names=['company'])  # 获取公司名
        row_num = companys.shape[0]  # 数据行数
        return companys, row_num

    def url_perfect(self, url_seed, url_perfected):
        '''
        完善数据源url
        :param url_seed:
        :param url_perfected:
        :return:
        '''
        parse_result = urlparse(url_seed)
        scheme = parse_result.scheme
        netloc = parse_result.netloc
        return urljoin(scheme+'://'+netloc, url_perfected)

    def content_parse(self, url):
        '''
        解析页面元素获取相应字段的数据
        :param url:
        :return:
        '''
        self.driver.get(url)
        time.sleep(3)
        contents = [element.text for element in self.driver.find_elements(by=By.XPATH,value='//p[contains(@class,"basic-item")]/em | //p[contains(@class,"basic-item")]/span')]
        columns = ['公司']#字段
        data = [self.company]#数据
        for i in range(0,len(contents),2):
            column, value = contents[i:i+2]
            columns.append(column)
            data.append(value)
        return pd.DataFrame(data=[data],columns=columns)

    @retry(stop_max_attempt_number=0)#尝试
    def main(self, company):
        company = re.sub('\（','(',re.sub('\）',')',company))
        self.company = company#公司
        response = requests.get(self.url_seed + company)
        tree = html.fromstring(response.text)
        try:
            url, title = tree.xpath('//div[contains(@class,"-items")]//a[@title="{name}"]/@href | //div[contains(@class,"-items")]//a[@title="{name}"]/@title'.format(name=company))
        except ValueError as e:
            self.log.warning(e)
            url, title = tree.xpath('//div[contains(@class,"-items")]//a[contains(@title,"{name}")]/@href | //div[contains(@class,"-items")]//a[contains(@title,"{name}")]/@title'.format(name=company))
        url_parse = self.url_perfect(self.url_seed, url)
        return self.content_parse(url_parse)

    def start(self):
        '''
        启动
        :return:
        '''
        companys, rows = self.load_excel()
        dataframes = []
        for row in range(rows):
            dataframes.append(self.main(companys.iloc[row, 0]))
            time.sleep(2)
        companys_info = pd.concat(dataframes)
        companys_info.to_excel(self.path_save, sheet_name='公司信息', index=False)


if __name__ == '__main__':
    MySpider('https://xin.baidu.com/s?q=','companyname.xlsx','companys_info.xlsx').start()