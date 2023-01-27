# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface


from itemadapter import ItemAdapter
from datetime import date, datetime
import pymysql
import pandas as pd
import time
import os
from ncpPro.items import NcpproItem, NcpproItemOfProvince


class NcpproPipeline:  # 将数据写入csv中
    def __init__(self):
        self.total_data = None
        self.province_data = None

    def open_spider(self, spider):
        if not os.path.exists(r'./csv/' + str(date.today())):
            os.mkdir('./csv/' + str(date.today()))
        else:
            pass  # 目录存在时执行
        with open(r'./csv/' + str(date.today()) + '/total.csv', 'w+', encoding='utf-8') as total_file:
            total_file.write(
                '新增确诊病例,新增本土病例,新增境外病例,新增无症状病例,现有确诊病例,现有本土病例,现有境外病例,现有无症状病例,累计确诊病例,累计境外病例,累计治愈,累计死亡,数据来源日期\n'
            )
        with open(r'./csv/' + str(date.today()) + '/province.csv', 'w+', encoding='utf-8') as province_file:
            province_file.write(
                '地区,新增确诊,现有确诊,累计确诊,累计死亡,数据来源日期\n'
            )

    def process_item(self, item, spider):
        if isinstance(item, NcpproItem):  # 有多个Item类时配置，可以防止多个Item之间会相互影响
            with open('./csv/' + str(date.today()) + '/total.csv', 'a+', encoding='utf-8') as total_file:
                total_file.write(
                    str(self.write_total(item)) + '\n'
                )
            with open('./csv/totalDiagnosisForAll.csv', 'a+', encoding='utf-8') as total_all_data:
                total_all_data.write(
                    str(self.write_total(item)) + '\n'
                )
        if isinstance(item, NcpproItemOfProvince):
            with open('./csv/' + str(date.today()) + '/province.csv', 'a+', encoding='utf-8') as province_file:
                try:
                    for city_data in item['province_data']:
                        province_file.write(
                            str(self.write_province(city_data)) + '\n'
                        )
                except KeyError:
                    pass
        return item

    def close_spider(self, spider):
        pass

    def write_total(self, item) -> str:
        try:
            self.total_data = '{},{},{},{},{},{},{},{},{},{},{},{},{}'.format(
                item['new_diagnosis'],
                item['new_local'],
                item['new_overseas'],
                item['new_asymptomatic'],
                item['current_diagnosis'],
                item['current_local'],
                item['current_overseas'],
                item['current_asymptomatic'],
                item['total_diagnosis'],
                item['total_overseas'],
                item['total_cured'],
                item['total_dead'],
                str(date.today()).replace('-', '/')
            )
        except KeyError:  # 有些key可能会因为数据为0不存在
            pass
        finally:
            return self.total_data

    def write_province(self, city_data) -> str:
        try:
            self.province_data = '{},{},{},{},{},{}'.format(
                city_data['name'],  # 地区
                city_data['today']['local_confirm_add'],  # 新增确诊
                city_data['total']['nowConfirm'],  # 现有确诊
                city_data['total']['confirm'],  # 累计确诊
                city_data['total']['dead'],  # 累计死亡
                city_data['date'],  # 数据来源日期
            )
        except KeyError:  # 有些key可能会因为数据为0不存在
            pass
        finally:
            return self.province_data


class NcpproPipelineToMySQL:
    def __init__(self):
        self.cursor = None
        self.conn = None

    def open_spider(self, spider):
        self.conn = pymysql.connect(
            host='127.0.0.1',
            user='root',
            password='Lyl1030',
            db='ncp_data'
        )
        self.cursor = self.conn.cursor()

    def close_spider(self, spider):
        pass

    def process_item(self, item, spider):
        self.create_table()  # 创建总表、省表
        self.write_data()  # 写入数据
        self.conn.commit()

    def create_table(self) -> None:
        sql_province = '''(
                    area varchar(50) not null unique comment '地区',
                    new_diagnosis int comment '新增确诊',
                    current_diagnosis int comment '现有确诊',
                    total_diagnosis int comment '累计确诊',
                    total_dead int comment '累计死亡',
                    from_date date comment '数据来源日期'
                ) comment '各个省份的疫情数据';
                '''
        self.cursor.execute(  # 创建省表的sql语句提交
            'create table if not exists {} {}'.format(
                'province_' + str(date.today()).replace('-', ''),
                sql_province
            )
        )

    def write_data(self) -> None:
        total_data = pd.read_csv(r'./csv/' + str(date.today()) + '/total.csv')
        province_data = pd.read_csv('./csv/' + str(date.today()) + '/province.csv')
        if total_data.新增确诊病例.values:  # 随便取一个columns的value，保证列表不为空列表
            sql_total = "{} into total_diagnosis values ({},{},{},{},{},{},{},{},{},{},{},{},'{}');".format(
                'insert',  # 写在str里会被pycharm报黄高亮，看着难受
                total_data.新增确诊病例.values[0],
                total_data.新增本土病例.values[0],
                total_data.新增境外病例.values[0],
                total_data.新增无症状病例.values[0],
                total_data.现有确诊病例.values[0],
                total_data.现有本土病例.values[0],
                total_data.现有境外病例.values[0],
                total_data.现有无症状病例.values[0],
                total_data.累计确诊病例.values[0],
                total_data.累计境外病例.values[0],
                total_data.累计治愈.values[0],
                total_data.累计死亡.values[0],
                str(total_data.数据来源日期.values[0]).replace('/', '-')
            )
            self.cursor.execute(sql_total)
        if province_data.地区.values.any():  # 同上，随便取一个columns的value，保证列表不为空列表，any表示任一取，all()取所有
            for row in list(range(len(province_data.地区))):
                sql_province_f = "{} * from province_{} where area='{}';".format(  # 查看数据库是否有相同数据
                    'select',
                    str(date.today()).replace('-', ''),
                    province_data.地区[row],
                )
                self.cursor.execute(sql_province_f)
                # print(self.cursor.fetchall())
                # 防止scrapy的异步协程机制引起的并发修改
                if self.cursor.fetchall():  # 如果数据已存在则执行数据更新
                    sql_province_u = """
                    {} province_{}
                    set 
                        new_diagnosis={},
                        current_diagnosis={},
                        total_diagnosis={},
                        total_dead={},
                        from_date='{}' 
                    where area='{}'
                    """.format(
                        'update',
                        str(date.today()).replace('-', ''),
                        province_data.新增确诊[row],
                        province_data.现有确诊[row],
                        province_data.累计确诊[row],
                        province_data.累计死亡[row],
                        str(province_data.数据来源日期[row]).replace('/', '-'),
                        province_data.地区[row]
                    )
                    # print('更新：', sql_province_u)
                    self.cursor.execute(sql_province_u)
                else:  # 如果数据不存在则写入
                    sql_province_i = "{} into province_{} values ('{}',{},{},{},{},'{}');".format(
                        'insert',
                        str(date.today()).replace('-', ''),
                        province_data.地区[row],
                        province_data.新增确诊[row],
                        province_data.现有确诊[row],
                        province_data.累计确诊[row],
                        province_data.累计死亡[row],
                        str(province_data.数据来源日期[row]).replace('/', '-')
                    )
                    # print('写入：', sql_province_i)
                    self.cursor.execute(sql_province_i)
