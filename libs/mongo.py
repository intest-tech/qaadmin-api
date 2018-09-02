import os
from pymongo import MongoClient
from libs.myconfigparser import config
from bson import ObjectId


def conn_mongo():
    DOCKER_FLAG = os.environ.get('DOCKER', False)
    if DOCKER_FLAG:
        conn = MongoClient('mongo', 27017)
    else:
        conn = MongoClient(config['mongo']['host'], int(config['mongo']['port']))
        # conn = MongoClient('localhost', 27017)
    db = conn.qaadmin
    return db


def singleton(cls, *args, **kwargs):
    instances = {}

    def _singleton():
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]

    return _singleton


qa_db = conn_mongo()


@singleton
class Project(object):
    db = qa_db

    def get(self, name: str) -> dict:
        """
        获取某个 project 信息.
        :param name: project name
        :return: 
        """
        result = self.db['Project'].find_one({'_id': name})
        return result

    def get_tags(self, name: str) -> list:
        """
        获取某个 project 信息.
        :param name: project name
        :return: 
        """
        result = self.db['Project'].find_one({'_id': name}, {'tags': 1})
        return result.get('tags', [])

    def list(self) -> list:
        """
        获取 project 列表.
        :return: 
        """
        cur = self.db['Project'].find({'is_del': False}, {'_id': 1})
        return list(cur)

    def exist(self, name: str) -> bool:
        """
        Check project existence
        :param name:
        :return: True: pass; False: error
        """
        return bool(self.get(name))


@singleton
class Result(object):
    db = qa_db

    def get(self, id):
        """
        获取 test result 详细数据
        :param id: _id of test result
        :return: 
        """
        find_condition = {'_id': ObjectId(id), 'is_del': False}
        filter_condition = {'is_del': 0, '_id': 0}
        result = self.db['TestResult'].find_one(find_condition, filter_condition)
        return result

    def get_page(self, pro_id, tag, page_index: int, page_size: int) -> dict:
        find_condition = {'is_del': False, 'project': pro_id}
        if tag:
            find_condition['tag'] = tag
        filter_condition = {
            '_id': 1,
            'was_successful': 1,
            'version': 1,
            'create_time': 1,
            'failures': 1,
            'errors': 1,
            'success': 1,
            'run_time': 1,
            'details': 1,
            'tag': 1
        }
        count = self.db['TestResult'].count_documents(find_condition)
        result = self.db['TestResult'].find(find_condition, filter_condition) \
            .sort('_id', -1) \
            .skip((page_index - 1) * page_size) \
            .limit(page_size)
        page = dict(
            results=list(result),
            p=page_index,
            ps=page_size,
            total=count
        )
        return page

    def list_detail(self) -> list:
        """
        获取project中最新的测试记录, 用于展示project列表
        :return: 
        """
        filter_condition = {'is_del': 0, '_id': 0, 'details': 0, 'run_time': 0}
        latest_result_list = []
        cur = self.db['Project'].find({'is_del': False}, {'_id': 1, 'latest_test': 1})
        result = list(cur)
        for item in result:
            latest_test = item.get('latest_test')
            if latest_test:
                find_condition = {'_id': latest_test}
                result = self.db['TestResult'].find_one(find_condition, filter_condition)
                latest_result_list.append(result)
            else:
                latest_result_list.append({'project': item['_id']})
        return latest_result_list


if __name__ == '__main__':
    b = Result()
    print(b.get_page('gt-api-test', None, 1, 20))
