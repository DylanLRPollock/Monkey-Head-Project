#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ================================================== #
# This file is a part of PYGPT package               #
# Website: https://pygpt.net                         #
# GitHub:  https://github.com/szczyglis-dev/py-gpt   #
# MIT License                                        #
# Created By  : Marcin Szczygliński                  #
# Updated Date: 2025.01.16 01:00:00                  #
# ================================================== #

import datetime
import os.path
from typing import Optional

from llama_index.core.indices.base import BaseIndex
from llama_index.core import StorageContext
from llama_index.vector_stores.elasticsearch import ElasticsearchStore

from pygpt_net.utils import parse_args
from .base import BaseStore


class ElasticsearchProvider(BaseStore):
    def __init__(self, *args, **kwargs):
        super(ElasticsearchProvider, self).__init__(*args, **kwargs)
        """
        Elasticsearch vector store provider

        :param args: args
        :param kwargs: kwargs
        """
        self.window = kwargs.get('window', None)
        self.id = "ElasticsearchStore"
        self.prefix = "elastic_"  # prefix for index directory
        self.indexes = {}

    def create(self, id: str):
        """
        Create empty index

        :param id: index name
        """
        path = self.get_path(id)
        if not os.path.exists(path):
            os.makedirs(path)
            self.store(id)

    def get_es_client(self, id: str) -> ElasticsearchStore:
        """
        Get Elasticsearch client

        :param id: index name
        :return: Elasticsearch client
        """
        defaults = {
            "index_name": id,
        }
        additional_args = parse_args(
            self.window.core.config.get('llama.idx.storage.args', []),
        )
        if "index_name" in additional_args:
            del defaults["index_name"]

        return ElasticsearchStore(
            **defaults,
            **additional_args
        )

    def get(
            self,
            id: str,
            llm: Optional = None,
            embed_model: Optional = None,
    ) -> BaseIndex:
        """
        Get index

        :param id: index name
        :param llm: LLM instance
        :param embed_model: Embedding model instance
        :return: index instance
        """
        if not self.exists(id):
            self.create(id)
        vector_store = self.get_es_client(id)
        storage_context = StorageContext.from_defaults(
            vector_store=vector_store,
        )
        self.indexes[id] = self.index_from_store(
            vector_store=vector_store,
            storage_context=storage_context,
            llm=llm,
            embed_model=embed_model,
        )
        return self.indexes[id]

    def store(
            self,
            id: str,
            index: Optional[BaseIndex] = None
    ):
        """
        Store index

        :param id: index name
        :param index: index instance
        """
        path = self.get_path(id)
        lock_file = os.path.join(path, 'store.lock')
        with open(lock_file, 'w') as f:
            f.write(id + ': ' + str(datetime.datetime.now()))
        self.indexes[id] = index
