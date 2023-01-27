# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class NcpproItem(scrapy.Item):
    new_diagnosis = scrapy.Field()  # 新增确诊病例
    new_local = scrapy.Field()  # 新增本土病例
    new_overseas = scrapy.Field()  # 新增境外病例
    new_asymptomatic = scrapy.Field()  # 新增无症状病例
    current_diagnosis = scrapy.Field()  # 现有确诊的病例
    current_local = scrapy.Field()  # 现有本土病例
    current_overseas = scrapy.Field()  # 现有境外病例
    current_asymptomatic = scrapy.Field()  # 现有无症状
    total_diagnosis = scrapy.Field()  # 累计确诊病例
    total_overseas = scrapy.Field()  # 累计境外病例
    total_cured = scrapy.Field()  # 累计治愈
    total_dead = scrapy.Field()  # 累计死亡


class NcpproItemOfProvince(scrapy.Item):
    province_data = scrapy.Field()  # 各个省份的数据，是一个list()，元素为dict
