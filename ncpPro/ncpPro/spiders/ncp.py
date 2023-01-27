import json
import re
import scrapy
from scrapy import Request
from ncpPro.items import NcpproItem, NcpproItemOfProvince


class NcpSpider(scrapy.Spider):
    name = 'ncp'
    # allowed_domains = ['www.xxx.com']
    # start_urls = ['www.baidu.com']
    total_url = r'https://voice.baidu.com/act/newpneumonia/newpneumonia/?from=osari_aladin_banner'
    province_url = r'https://api.inews.qq.com/newsqa/v1/query/inner/publish/modules/list?modules=localCityNCOVDataList,diseaseh5Shelf'

    # 设置多个Item类，防止在存储不同数据时导致一个管道出现多次调用
    item_total = NcpproItem()
    item_province = NcpproItemOfProvince()

    def start_requests(self):
        yield Request(
            url=self.total_url,
            callback=self.get_total_data
        )
        yield Request(
            url=self.province_url,
            callback=self.get_all_province_data
        )

    def close(spider, reason):
        print('爬取完成')

    def get_total_data(self, response):  # 获取总的数据
        ex = r'"summaryDataIn":{(.*)},"summaryDataOut"'
        data = re.findall(ex, response.text, re.S)[0]  # 解析得到关键Json，但返回的数据类型为str
        dic = dict()
        for item in data.split(','):
            item = item.replace('"', '')
            key = item.split(':')[0]
            value = item.split(':')[1]
            dic[key] = int(value)
        self.call_total_item(dic)  # 将数据存入Item类中
        yield self.item_total

    def get_all_province_data(self, response):  # 获取各个省份的数据
        province_json = json.loads(response.text)['data']['diseaseh5Shelf']['areaTree'][0]['children']  # 获取Json下需要的数据
        lis = list()  # 设置一个容器，防止管道多次触发，导致总数居被多次存储
        for city_dic in list(range(len(province_json))):  # 23(省)+5(自治区)+4(直辖市)+2(特别行政区)=[0, 34)
            lis.append(province_json[city_dic])
        self.call_province_item(lis)
        yield self.item_province

    def call_total_item(self, dic) -> None:
        self.item_total['new_diagnosis'] = dic['confirmedRelative']
        self.item_total['new_local'] = dic['unOverseasInputNewAdd']
        self.item_total['new_overseas'] = dic['overseasInputRelative']
        self.item_total['new_asymptomatic'] = dic['asymptomaticRelative']
        self.item_total['current_diagnosis'] = dic['curConfirm']
        self.item_total['current_local'] = dic['curLocalConfirm']
        self.item_total['current_overseas'] = dic['curOverseasInput']
        self.item_total['current_asymptomatic'] = dic['asymptomatic']
        self.item_total['total_diagnosis'] = dic['confirmed']
        self.item_total['total_overseas'] = dic['overseasInput']
        self.item_total['total_cured'] = dic['cured']
        self.item_total['total_dead'] = dic['died']

    def call_province_item(self, lis) -> None:
        self.item_province['province_data'] = lis
