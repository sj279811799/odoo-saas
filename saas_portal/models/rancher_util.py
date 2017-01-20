#!/usr/bin/python
# -*- coding: UTF-8 -*-
""" Rancher Api for Odoo By Song """
import gdapi


class Rancher:
    def __init__(self, rancher):
        self.url = 'http://%s/v1/' % rancher.url
        self.env_name = rancher.env_name
        self.access_key = rancher.access_key
        self.secret_key = rancher.secret_key

    # 获取env_id
    def get_env_id(self):
        client = gdapi.Client(url=self.url, access_key=self.access_key, secret_key=self.secret_key)
        envs = client.list_project()
        for env in envs:
            if env.name == self.env_name:
                return env.id
        return False

    # 获取所有主机
    def get_host(self):
        host_lists = []
        env_id = self.get_env_id()
        url = '%sprojects/%s' % (self.url, env_id)
        client = gdapi.Client(url=url, access_key=self.access_key, secret_key=self.secret_key)
        for host in client.list_host().data:
            host_type = False
            if 'label' in host.labels:
                host_type = host.labels['label']
            host_lists.append({
                'host_id': host.id,
                'name': host.name,
                'host_name': host.hostname,
                'host_ip': host.publicEndpoints[0].ipAddress,
                'memory_total': host.info.memoryInfo.memTotal,
                'memory_available': host.info.memoryInfo.memAvailable,
                'cpu': host.info.cpuInfo.modelName,
                'cpu_count': host.info.cpuInfo.count,
                'state': host.state,
                'host_type': host_type,
            })
        return host_lists

    # 根据主机ID设置主机标签
    def update_host_label(self, host_id, host_type):
        env_id = self.get_env_id()
        url = '%sprojects/%s/hosts' % (self.url, env_id)
        client = gdapi.Client(url=url, access_key=self.access_key, secret_key=self.secret_key)
        host = client.by_id_host(host_id)
        labels = host.labels
        labels.update({
            'label': host_type,
        })
        client.update(host, labels=labels)
        return True

    # 创建Stacks
    def create_partition(self, partition):
        env_id = self.get_env_id()
        url = '%sprojects/%s/environments' % (self.url, env_id)
        client = gdapi.Client(url=url, access_key=self.access_key, secret_key=self.secret_key)
        partition = client.create_environment(partition)
        return partition.id

    # 根据stacks_id获取所有的Server
    def get_service(self, partition_id):
        service_lists = []
        env_id = self.get_env_id()
        url = '%sprojects/%s/services' % (self.url, env_id)
        client = gdapi.Client(url=url, access_key=self.access_key, secret_key=self.secret_key)
        for service in client.list_service().data:
            if 'environmentId' in service and service.environmentId == partition_id:
                service_lists.append({
                    'service_id': service.id,
                    'name': service.name,
                    'state': service.state,
                    'kind': service.kind,
                    'image': service.launchConfig.imageUuid,
                    'scale': service.scale,
                })
        return service_lists

    # 根据id删除Stacks
    # def unlink_partition(self, partition_id):

    # 根据stack_id获取LB的容器id
    def get_container_id(self, partition_id):
        env_id = self.get_env_id()
        url = '%sprojects/%s/services' % (self.url, env_id)
        client = gdapi.Client(url=url, access_key=self.access_key, secret_key=self.secret_key)
        for service in client.list_service().data:
            if 'environmentId' in service and service.environmentId == partition_id and service.name == 'lb':
                return service.instanceIds and service.instanceIds[0] or False

    # 根据container_id获取LB的容器ip
    def get_lb_ip(self, container_id):
        env_id = self.get_env_id()
        url = '%sprojects/%s/containers' % (self.url, env_id)
        client = gdapi.Client(url=url, access_key=self.access_key, secret_key=self.secret_key)
        for container in client.list_container().data:
            if container.id == container_id:
                return container.primaryIpAddress